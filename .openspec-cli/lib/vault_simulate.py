#!/usr/bin/env python3
"""vault_simulate.py — POST /v1/contracts:simulate (streaming NDJSON).

Builds the simulation payload from a contract file, opens the account inside
the simulation, streams the response line by line (per the Thought Machine
Contract Simulation docs: requests(stream=True) + iter_lines), and prints a
readable summary.

Usage:
    vault_simulate.py <contract_file> [start_ts] [end_ts] [param_overrides_json]

    param_overrides_json merges over the values auto-extracted from the
    contract's Parameter(...) declarations. Each key is routed to the
    TEMPLATE/GLOBAL bucket (smart_contract_param_vals) or the INSTANCE bucket
    (create_account.instance_param_vals) by the parameter's declared level.

Env: VAULT_BASE_URL, VAULT_TOKEN
"""
from __future__ import annotations

import ast
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    sys.stderr.write(
        "ERROR: the 'requests' package is required. "
        "Install it: pip install -r requirements.txt\n"
    )
    sys.exit(1)

SIM_ACCOUNT_ID = "openspec-sim-account"
SIM_VERSION_ID = "1"

_GREEN, _RED, _CYAN, _YELLOW, _BOLD, _RESET = (
    "\033[0;32m", "\033[0;31m", "\033[0;36m", "\033[0;33m", "\033[1m", "\033[0m"
)


def _configure_stdout() -> None:
    """UTF-8 for ✔/✖/⏱, and line buffering so the NDJSON stream prints as it
    arrives (not in one block) even when stdout is piped."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore[union-attr]
        except (AttributeError, OSError, ValueError):
            pass


def _c(code: str, text: str) -> str:
    return text if os.environ.get("NO_COLOR") else f"{code}{text}{_RESET}"


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Parameter extraction ──────────────────────────────────────────────────────

def _literal(node: ast.AST):
    """Best-effort extraction of a Parameter default_value node to a string."""
    if isinstance(node, ast.Constant):
        return None if node.value is None else str(node.value)
    if isinstance(node, ast.Call):
        fn = getattr(node.func, "id", "")
        if fn == "Decimal" and node.args and isinstance(node.args[0], ast.Constant):
            return str(node.args[0].value)
        if fn in ("OptionalValue", "UnionItemValue") and node.args:
            return _literal(node.args[0])
    return None


def _shape_names(node: ast.AST) -> set[str]:
    """All Shape constructor names in a shape= expression (handles OptionalShape(shape=...))."""
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            fn = getattr(sub.func, "id", "")
            if fn.endswith("Shape"):
                names.add(fn)
    return names


def extract_params(tree: ast.AST) -> dict[str, dict]:
    """{name: {level, value, optional, is_date}} for non-derived params."""
    params: dict[str, dict] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Parameter"):
            continue
        name = level = value = None
        derived = optional = is_date = False
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                name = kw.value.value
            elif kw.arg == "level" and isinstance(kw.value, ast.Attribute):
                level = kw.value.attr
            elif kw.arg == "derived":
                derived = getattr(kw.value, "value", False) is True
            elif kw.arg == "default_value":
                value = _literal(kw.value)
            elif kw.arg == "shape":
                shapes = _shape_names(kw.value)
                optional = "OptionalShape" in shapes
                is_date = "DateShape" in shapes
        if name and not derived:
            params[name] = {
                "level": level, "value": value, "optional": optional, "is_date": is_date,
            }
    return params


def build_payload(contract_file: str, start_ts: str, end_ts: str,
                  overrides: dict) -> tuple[dict, list[str]]:
    code = open(contract_file, encoding="utf-8").read()
    params = extract_params(ast.parse(code))

    template_vals: dict[str, str] = {}
    instance_vals: dict[str, str] = {}
    warnings: list[str] = []

    for name, meta in params.items():
        overridden = name in overrides
        # Optional params: rely on the contract's own default unless overridden —
        # avoids re-encoding OptionalValue/UnionItemValue wrappers.
        if meta["optional"] and not overridden:
            if meta["value"] is None:
                warnings.append(
                    f"parameter {name!r} is optional with no default; the contract "
                    f"may still require it — pass it in the overrides JSON if so"
                )
            continue
        val = overrides.get(name, meta["value"])
        bucket = template_vals if meta["level"] in ("TEMPLATE", "GLOBAL") else instance_vals
        if val is None:
            warnings.append(
                f"parameter {name!r} ({meta['level']}) has no default and no override "
                f"— pass it in the overrides JSON"
            )
            continue
        val = str(val)
        if meta["is_date"] and "T" in val:  # Vault DateShape wants YYYY-MM-DD
            val = val.split("T", 1)[0]
        bucket[name] = val

    # overrides for names not declared as Parameter (e.g. typo) — surface it
    for name in overrides:
        if name not in params:
            warnings.append(f"override {name!r} does not match any contract parameter")

    payload = {
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "smart_contracts": [
            {
                "code": code,
                "smart_contract_version_id": SIM_VERSION_ID,
                "smart_contract_param_vals": template_vals,
            }
        ],
        "instructions": [
            {
                "timestamp": start_ts,
                "create_account": {
                    "id": SIM_ACCOUNT_ID,
                    "product_version_id": SIM_VERSION_ID,
                    "instance_param_vals": instance_vals,
                },
            }
        ],
    }
    return payload, warnings


# ── Response rendering ───────────────────────────────────────────────────────

def _render_error(obj: dict) -> None:
    print(_c(_RED, f"  ✖ {obj.get('message', 'error')}"))
    violations = []
    for d in obj.get("details", []):
        violations += d.get("violations", [])
    for v in violations:
        meta = v.get("metadata", {})
        etype = meta.get("exception_type", v.get("violation_type", ""))
        args = meta.get("exception_args", "")
        trace = meta.get("stack_trace", "")
        print(_c(_RED, f"      {etype}: {args}"))
        for frame in str(trace).splitlines():
            print(_c(_RED, f"        {frame.strip()}"))


def _render_result(r: dict) -> None:
    ts = r.get("timestamp", "?")
    for log in r.get("logs", []) or []:
        print(f"  {_c(_CYAN, ts)}  {log}")
    for acc, note in (r.get("account_notification_directives") or {}).items():
        print(f"  {_c(_CYAN, ts)}  notification → {acc}: {note}")
    balances = r.get("balances")
    if balances:
        print(f"  {_c(_CYAN, ts)}  balances: {json.dumps(balances)[:400]}")


def main(argv: list[str]) -> int:
    _configure_stdout()
    if not argv:
        sys.stderr.write(
            "Usage: vault_simulate.py <contract_file> [start_ts] [end_ts] "
            "[param_overrides_json]\n"
        )
        return 1

    contract_file = argv[0]
    if not os.path.isfile(contract_file):
        sys.stderr.write(f"ERROR: contract file not found: {contract_file}\n")
        return 1

    base = os.environ.get("VAULT_BASE_URL", "").rstrip("/")
    token = os.environ.get("VAULT_TOKEN", "")
    if not base or not token:
        sys.stderr.write("ERROR: VAULT_BASE_URL and VAULT_TOKEN must be set in .env\n")
        return 1

    now = datetime.now(timezone.utc)
    start_ts = argv[1] if len(argv) > 1 and argv[1] else _iso(now)
    if len(argv) > 2 and argv[2]:
        end_ts = argv[2]
    else:
        base_dt = datetime.strptime(start_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        end_ts = _iso(base_dt + timedelta(days=90))
    overrides = json.loads(argv[3]) if len(argv) > 3 and argv[3] else {}

    payload, warnings = build_payload(contract_file, start_ts, end_ts, overrides)

    print(_c(_CYAN, "────────────────────────────────────────────"))
    print(_c(_BOLD, "OpenSpec — Vault Contract Simulation"))
    print(_c(_CYAN, "────────────────────────────────────────────"))
    print(f"Contract : {contract_file}")
    print(f"Window   : {start_ts} → {end_ts}")
    print(f"Template : {json.dumps(payload['smart_contracts'][0]['smart_contract_param_vals'])}")
    print(f"Instance : {json.dumps(payload['instructions'][0]['create_account']['instance_param_vals'])}")
    for w in warnings:
        print(_c(_YELLOW, f"  ⚠ {w}"))
    print(_c(_CYAN, "────────────────────────────────────────────"))

    repo_root = os.environ.get("OS_REPO_ROOT") or "."
    debug_path = os.path.join(repo_root, ".openspec-cli", ".last-simulation.json")
    try:
        with open(debug_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except OSError:
        pass

    t0 = time.time()
    try:
        resp = requests.post(
            f"{base}/v1/contracts:simulate",
            stream=True,
            headers={"X-Auth-Token": token, "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
    except requests.RequestException as exc:
        print(_c(_RED, f"✖ request failed: {exc}"))
        return 1

    hdr_ct = resp.headers.get("content-type", "")
    print(f"HTTP {resp.status_code}  {hdr_ct}  ({time.time() - t0:.1f}s)")
    if "ndjson" in hdr_ct:
        print(_c(_CYAN, "──── streaming (line by line, as Vault replays) ────"))
    else:
        print(_c(_CYAN, "────────────────────────────────────────────"))

    n_lines = 0
    failed = False
    for raw in resp.iter_lines():
        if not raw:
            continue
        n_lines += 1
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  (unparsed) {raw[:300]!r}", flush=True)
            continue
        if isinstance(obj, list):  # bare log array
            for log in obj:
                print(f"  {log}", flush=True)
        elif "result" in obj:
            _render_result(obj["result"])
        elif obj.get("error") or obj.get("code") or obj.get("http_code"):
            failed = True
            _render_error(obj)
        else:
            print(f"  {json.dumps(obj)[:400]}", flush=True)
        sys.stdout.flush()

    elapsed = time.time() - t0
    print(_c(_CYAN, "────────────────────────────────────────────"))
    if failed or resp.status_code != 200:
        print(_c(_RED + _BOLD, f"✖ Simulation FAILED   {n_lines} lines   ⏱ {elapsed:.1f}s"))
        return 1
    print(_c(_GREEN + _BOLD, f"✔ Simulation OK   {n_lines} lines   ⏱ {elapsed:.1f}s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
