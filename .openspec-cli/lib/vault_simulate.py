#!/usr/bin/env python3
"""vault_simulate.py — POST /v1/contracts:simulate (streaming NDJSON).

Builds the simulation payload from a contract file, opens the account inside
the simulation, streams the response line by line (per the Thought Machine
Contract Simulation docs: requests(stream=True) + iter_lines), and prints a
readable log: every scheduled event, every posting it generates and the
running account balances after it.

Usage:
    vault_simulate.py <contract_file> [start_ts] [end_ts] [param_overrides_json]
                      [--deposit N] [--payroll] [--deposit-on YYYY-MM-DD]
                      [--all-accounts] [--raw]

    param_overrides_json merges over the values auto-extracted from the
    contract's Parameter(...) declarations. Each key is routed to the
    TEMPLATE/GLOBAL bucket (smart_contract_param_vals) or the INSTANCE bucket
    (create_account.instance_param_vals) by the parameter's declared level.

    --deposit N     Seed the account with an inbound settlement of N before the
                    schedules run, so fees / interest actually move money. A
                    throw-away contra account is opened inside the simulation to
                    fund it (the sandbox has no addressable internal accounts).
    --payroll       Mark that seed deposit as a payroll credit
                    (instruction_details.tipo_transaccion = "NOMINA").
    --deposit-on    Date of the seed deposit (default: simulation start).
    --all-accounts  Also render the contra account's logs / balances.
    --verbose       Do not fold runs of no-op scheduled events into one line.
    --raw           Dump the NDJSON stream verbatim, no formatting.

Env: VAULT_BASE_URL, VAULT_TOKEN
"""
from __future__ import annotations

import ast
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

try:
    import requests
except ImportError:
    sys.stderr.write(
        "ERROR: the 'requests' package is required. "
        "Install it: pip install -r requirements.txt\n"
    )
    sys.exit(1)

SIM_ACCOUNT_ID = "openspec-sim-account"
SIM_CONTRA_ID = "openspec-sim-contra"
SIM_VERSION_ID = "1"
COMMITTED = "POSTING_PHASE_COMMITTED"

_GREEN, _RED, _CYAN, _YELLOW, _DIM, _BOLD, _RESET = (
    "\033[0;32m", "\033[0;31m", "\033[0;36m", "\033[0;33m",
    "\033[0;90m", "\033[1m", "\033[0m",
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


def _money(raw) -> str:
    try:
        return f"{Decimal(str(raw)):,.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return str(raw)


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


def _pick_denomination(instance_vals: dict[str, str]) -> str:
    for val in instance_vals.values():
        if isinstance(val, str) and len(val) == 3 and val.isalpha() and val.isupper():
            return val
    return os.environ.get("VAULT_DEFAULT_DENOMINATION", "GBP")


def build_payload(contract_file: str, start_ts: str, end_ts: str, overrides: dict,
                  deposit: str | None, payroll: bool,
                  deposit_on: str | None) -> tuple[dict, list[str], str]:
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

    denomination = _pick_denomination(instance_vals)

    instructions: list[dict] = [
        {
            "timestamp": start_ts,
            "create_account": {
                "id": SIM_ACCOUNT_ID,
                "product_version_id": SIM_VERSION_ID,
                "instance_param_vals": instance_vals,
            },
        }
    ]

    if deposit is not None:
        dep_ts = deposit_on or start_ts
        if len(dep_ts) == 10:  # bare YYYY-MM-DD
            dep_ts += "T00:01:00Z"
        details = {"description": "OpenSpec sim seed deposit"}
        if payroll:
            details["tipo_transaccion"] = "NOMINA"
        # The sandbox exposes no addressable internal account inside a
        # simulation, so fund the deposit from a throw-away account on the same
        # contract. Its own hooks/schedules run too — they are filtered from the
        # output unless --all-accounts.
        instructions.append(
            {
                "timestamp": start_ts,
                "create_account": {
                    "id": SIM_CONTRA_ID,
                    "product_version_id": SIM_VERSION_ID,
                    "instance_param_vals": instance_vals,
                },
            }
        )
        instructions.append(
            {
                "timestamp": dep_ts,
                "create_posting_instruction_batch": {
                    "client_id": "OpenSpecSimSeed",
                    "client_batch_id": "openspec-sim-seed",
                    "posting_instructions": [
                        {
                            "client_transaction_id": "openspec-sim-seed-ct",
                            "instruction_details": details,
                            "inbound_hard_settlement": {
                                "amount": str(deposit),
                                "denomination": denomination,
                                "target_account": {"account_id": SIM_ACCOUNT_ID},
                                "internal_account_id": SIM_CONTRA_ID,
                            },
                        }
                    ],
                },
            }
        )

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
        "instructions": instructions,
    }
    return payload, warnings, denomination


# ── Response rendering ───────────────────────────────────────────────────────

_INSTRUCTION_KEYS = (
    "custom_instruction", "inbound_hard_settlement", "outbound_hard_settlement",
    "inbound_authorisation", "outbound_authorisation", "authorisation_adjustment",
    "settlement", "release", "transfer",
)


def _event_name(log: str) -> str:
    """'processed scheduled event "X" for account "Y"' -> '"X"'."""
    parts = log.split('"')
    return f'"{parts[1]}"' if len(parts) >= 2 else log


def _instruction_kind(pi: dict) -> str:
    for key in _INSTRUCTION_KEYS:
        if pi.get(key):
            return key
    return "instruction"


def _render_error(obj: dict) -> None:
    err = obj.get("error", obj)
    print(_c(_RED, f"  ✖ {err.get('message', obj.get('message', 'error'))}"))
    violations = []
    for d in err.get("details", []) or obj.get("details", []):
        violations += d.get("violations", [])
        for inner in d.get("details", []) or []:
            violations += inner.get("violations", [])
    for v in violations:
        meta = v.get("metadata", {})
        etype = meta.get("exception_type", v.get("violation_type", ""))
        args = meta.get("exception_args", "")
        trace = meta.get("stack_trace", "")
        print(_c(_RED, f"      {etype}: {args}"))
        for frame in str(trace).splitlines():
            print(_c(_RED, f"        {frame.strip()}"))


class Renderer:
    """Streams a readable log: events, the postings they generate and the
    running balances after each. Consecutive scheduled events that move no
    money (e.g. a daily counter reset) are folded into one line unless
    --verbose."""

    def __init__(self, primary: str, show_all: bool, verbose: bool) -> None:
        self.primary = primary
        self.show_all = show_all
        self.verbose = verbose
        self.running: dict[str, dict] = {}
        self._quiet: list[tuple[str, str]] = []  # (timestamp, event name)

    def _flush_quiet(self) -> None:
        if not self._quiet:
            return
        if len(self._quiet) == 1:
            ts, event = self._quiet[0]
            print(f"  {_c(_CYAN, ts)}  processed scheduled event {event}", flush=True)
        else:
            names = sorted({e for _, e in self._quiet})
            what = ", ".join(names)
            span = f"{self._quiet[0][0]} … {self._quiet[-1][0]}"
            print(
                f"  {_c(_DIM, span)}  "
                f"{_c(_DIM, f'{len(self._quiet)} scheduled events, no movement ({what})')}",
                flush=True,
            )
        self._quiet = []

    def _postings(self, res: dict) -> list[tuple[str, list[str]]]:
        out: list[tuple[str, list[str]]] = []
        for batch in res.get("posting_instruction_batches") or []:
            for pi in batch.get("posting_instructions") or []:
                postings = pi.get("committed_postings") or []
                mine = [p for p in postings if p.get("account_id") == self.primary]
                if not self.show_all and postings and not mine:
                    continue
                rows = []
                for p in (postings if self.show_all else (mine or postings)):
                    side = "Cr" if p.get("credit") else "Dr"
                    where = p.get("account_address", "?")
                    if p.get("account_id") != self.primary:
                        where += f" @{p.get('account_id')}"
                    rows.append(
                        f"{side} {_money(p.get('amount')):>14} "
                        f"{p.get('denomination', '')}  {where}"
                    )
                details = pi.get("instruction_details") or {}
                out.append((details.get("description") or _instruction_kind(pi), rows))
        return out

    def _balances(self, res: dict) -> list[tuple[str, list[str]]]:
        out: list[tuple[str, list[str]]] = []
        for acc_id, block in (res.get("balances") or {}).items():
            if acc_id != self.primary and not self.show_all:
                continue
            cells = []
            for b in block.get("balances") or []:
                if b.get("phase") != COMMITTED:
                    continue
                addr = b.get("account_address", "?")
                den = b.get("denomination", "")
                self.running.setdefault(acc_id, {})[(addr, den)] = b.get("amount")
                cells.append(f"{addr} {_money(b.get('amount'))} {den}")
            if cells:
                out.append((acc_id, cells))
        return out

    def result(self, res: dict) -> None:
        ts = res.get("timestamp", "?")
        logs = [
            log for log in (res.get("logs") or [])
            if self.show_all or not (SIM_CONTRA_ID in log and self.primary not in log)
        ]
        postings = self._postings(res)
        balances = self._balances(res)

        if not logs and not postings and not balances:
            return  # nothing to show (e.g. a filtered contra-account line)

        if (
            not self.verbose and not postings and not balances
            and all(log.startswith("processed scheduled event") for log in logs)
        ):
            self._quiet.append((ts, _event_name(logs[0])))
            return

        self._flush_quiet()
        tag = _c(_CYAN, ts)
        for log in logs:
            print(f"  {tag}  {log}", flush=True)
        for label, rows in postings:
            print(f"  {tag}  {_c(_YELLOW, '⇄')} {label}", flush=True)
            for row in rows:
                print(f"        {row}", flush=True)
        for acc_id, cells in balances:
            prefix = "balances" if acc_id == self.primary else f"balances @{acc_id}"
            print(f"        {_c(_CYAN, prefix + ':')} " + "  ·  ".join(cells), flush=True)

    def error(self, obj: dict) -> None:
        self._flush_quiet()
        _render_error(obj)

    def finish(self) -> None:
        self._flush_quiet()
        balances = self.running.get(self.primary)
        if not balances:
            return
        print()
        print(_c(_BOLD, f"Saldos finales ({self.primary})"))
        for (addr, den), amount in sorted(balances.items()):
            print(f"  {addr:<24} {_money(amount):>16} {den}")


def _parse_flags(argv: list[str]) -> tuple[list[str], dict]:
    flags = {
        "deposit": None, "payroll": False, "deposit_on": None,
        "all_accounts": False, "raw": False, "verbose": False,
    }
    positional: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--deposit", "-d") and i + 1 < len(argv):
            flags["deposit"] = argv[i + 1]
            i += 2
        elif arg in ("--payroll", "--nomina"):
            flags["payroll"] = True
            i += 1
        elif arg == "--deposit-on" and i + 1 < len(argv):
            flags["deposit_on"] = argv[i + 1]
            i += 2
        elif arg == "--all-accounts":
            flags["all_accounts"] = True
            i += 1
        elif arg == "--raw":
            flags["raw"] = True
            i += 1
        elif arg in ("--verbose", "-v"):
            flags["verbose"] = True
            i += 1
        else:
            positional.append(arg)
            i += 1
    return positional, flags


def main(argv: list[str]) -> int:
    _configure_stdout()
    argv, flags = _parse_flags(argv)
    if not argv:
        sys.stderr.write(
            "Usage: vault_simulate.py <contract_file> [start_ts] [end_ts] "
            "[param_overrides_json] [--deposit N] [--payroll] "
            "[--deposit-on YYYY-MM-DD] [--all-accounts] [--verbose] [--raw]\n"
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

    if flags["deposit"] is not None:
        try:
            Decimal(flags["deposit"])
        except InvalidOperation:
            sys.stderr.write(f"ERROR: --deposit expects a number, got {flags['deposit']!r}\n")
            return 1

    payload, warnings, denomination = build_payload(
        contract_file, start_ts, end_ts, overrides,
        flags["deposit"], flags["payroll"], flags["deposit_on"],
    )

    print(_c(_CYAN, "────────────────────────────────────────────"))
    print(_c(_BOLD, "OpenSpec — Vault Contract Simulation"))
    print(_c(_CYAN, "────────────────────────────────────────────"))
    print(f"Contract : {contract_file}")
    print(f"Window   : {start_ts} → {end_ts}")
    print(f"Template : {json.dumps(payload['smart_contracts'][0]['smart_contract_param_vals'])}")
    print(f"Instance : {json.dumps(payload['instructions'][0]['create_account']['instance_param_vals'])}")
    if flags["deposit"] is not None:
        kind = "payroll credit" if flags["payroll"] else "deposit"
        when = flags["deposit_on"] or start_ts
        print(f"Seed     : +{_money(flags['deposit'])} {denomination} {kind} @ {when}")
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
    renderer = Renderer(SIM_ACCOUNT_ID, flags["all_accounts"], flags["verbose"])
    for raw in resp.iter_lines():
        if not raw:
            continue
        n_lines += 1
        if flags["raw"]:
            print(raw.decode("utf-8", "replace"), flush=True)
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  (unparsed) {raw[:300]!r}", flush=True)
            continue
        if isinstance(obj, list):  # bare log array
            for log in obj:
                print(f"  {log}", flush=True)
        elif "result" in obj:
            renderer.result(obj["result"])
        elif obj.get("error") or obj.get("code") or obj.get("http_code"):
            failed = True
            renderer.error(obj)
        else:
            print(f"  {json.dumps(obj)[:400]}", flush=True)
        sys.stdout.flush()

    elapsed = time.time() - t0
    if not flags["raw"]:
        renderer.finish()
    print(_c(_CYAN, "────────────────────────────────────────────"))
    if failed or resp.status_code != 200:
        print(_c(_RED + _BOLD, f"✖ Simulation FAILED   {n_lines} lines   ⏱ {elapsed:.1f}s"))
        return 1
    print(_c(_GREEN + _BOLD, f"✔ Simulation OK   {n_lines} lines   ⏱ {elapsed:.1f}s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
