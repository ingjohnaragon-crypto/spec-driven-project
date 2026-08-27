#!/usr/bin/env python3
"""vault_products_fetch_and_print.py — lists Vault products (product versions).

Per the Vault Core API docs:
  - GET /v1/products already returns id, display_name, current_version_id and
    is_internal for every product -- no need to fetch product-versions just to
    show the current one.
  - GET /v1/product-versions:batchGet?ids=... fetches full version details
    (version number, tags, ...) for a specific set of version ids in one call,
    which is what we use to enrich the "current only" view.
  - GET /v1/product-versions?product_id=... (there is no "list versions across
    all products" call) is only used for --all, to also list superseded
    versions of each product.

Vault has no "created by" concept, so "only what I deployed" (--mine) is
tracked locally: os-vault-deploy appends a JSON line per successful deploy to
a log file, and this script filters the live product list against it.

Optionally, one or more product ids can be requested directly via
GET /v1/products:batchGet instead of listing every product.

Usage:
  py vault_products_fetch_and_print.py <base_url> <token> <only_current:true|false> \
      <mine_only:true|false> [log_file] [product_id ...]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"

PAGE_SIZE = 30
BATCH_SIZE = 30


def err(msg: str) -> None:
    print(f"{RED}✖  {msg}{RESET}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"{YELLOW}⚠  {msg}{RESET}", file=sys.stderr)


def vault_get(base_url: str, token: str, path: str) -> dict:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"X-Auth-Token": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def paginated_get(base_url: str, token: str, path: str, list_key: str, params: dict | None = None) -> list:
    items: list = []
    page_token = ""
    base_params = dict(params or {})
    while True:
        query = dict(base_params)
        query["page_size"] = PAGE_SIZE
        if page_token:
            query["page_token"] = page_token
        url = f"{path}?{urllib.parse.urlencode(query)}"
        data = vault_get(base_url, token, url)
        items.extend(data.get(list_key, []))
        page_token = data.get("next_page_token", "")
        if not page_token:
            break
    return items


def batch_get(base_url: str, token: str, path: str, ids: list, map_key: str) -> dict:
    """Fetch resources by id via a :batchGet endpoint, chunked (no page_size on this endpoint)."""
    result: dict = {}
    for i in range(0, len(ids), BATCH_SIZE):
        chunk = ids[i:i + BATCH_SIZE]
        query = urllib.parse.urlencode([("ids", cid) for cid in chunk])
        data = vault_get(base_url, token, f"{path}?{query}")
        result.update(data.get(map_key, {}))
    return result


def version_str(pv: dict) -> str:
    ver = pv.get("display_version_number") or pv.get("contracts_language_api_version")
    if isinstance(ver, dict):
        return f"{ver.get('major', '?')}.{ver.get('minor', '?')}.{ver.get('patch', '?')}"
    return str(ver) if ver else "?"


def load_mine_ids(log_file: str) -> set | None:
    """Product ids this machine has deployed via os-vault-deploy, or None if there's no log yet."""
    if not log_file or not os.path.isfile(log_file):
        return None
    ids: set = set()
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            product_id = entry.get("product_id")
            if product_id:
                ids.add(product_id)
    return ids


def print_row(i: int, product_id: str, display_name: str, product_version_id: str,
              version: str, is_current: str, is_internal: bool) -> None:
    suffix = " (internal)" if is_internal else ""
    print(f"  {i}. {display_name}{suffix}")
    print(f"     product_id         : {product_id}")
    print(f"     product_version_id : {product_version_id}")
    print(f"     version            : {version}")
    print(f"     is_current         : {is_current}")
    print()


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "Usage: py vault_products_fetch_and_print.py <base_url> <token> <only_current> "
            "<mine_only> [log_file] [product_id ...]",
            file=sys.stderr,
        )
        return 1

    base_url, token, only_current_arg, mine_only_arg = sys.argv[1:5]
    log_file = sys.argv[5] if len(sys.argv) > 5 else ""
    requested_ids = sys.argv[6:]
    only_current = only_current_arg.lower() == "true"
    mine_only = mine_only_arg.lower() == "true"

    try:
        if requested_ids:
            found = batch_get(base_url, token, "/v1/products:batchGet", requested_ids, "products")
            products = list(found.values())
            for pid in requested_ids:
                if pid not in found:
                    warn(f"Product '{pid}' not found")
        else:
            products = paginated_get(base_url, token, "/v1/products", "products", {})
    except urllib.error.HTTPError as e:
        err(f"Fetching products failed (HTTP {e.code}):")
        print(e.read().decode(errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        err(f"Could not reach Vault: {e.reason}")
        return 1

    if mine_only:
        mine_ids = load_mine_ids(log_file)
        if mine_ids is None:
            print(f"\n  (no local deploy history found -- {log_file or 'the log file'} doesn't exist yet)")
            print("  Deploy something with os-vault-deploy first, or drop --mine to see every product in this Vault instance.")
            return 0
        products = [p for p in products if p.get("id") in mine_ids]

    if not products:
        print("\n  (no products found -- deploy one with os-vault-deploy)")
        return 0

    rows: list[tuple[str, str, str, str, str, bool]] = []

    if only_current:
        version_ids = [p["current_version_id"] for p in products if p.get("current_version_id")]
        version_details: dict = {}
        if version_ids:
            try:
                version_details = batch_get(
                    base_url, token, "/v1/product-versions:batchGet", version_ids, "product_versions"
                )
            except urllib.error.HTTPError as e:
                warn(f"Could not fetch version details (HTTP {e.code}) -- showing products without version numbers")
            except urllib.error.URLError as e:
                warn(f"Could not fetch version details: {e.reason} -- showing products without version numbers")

        for p in products:
            cur_id = p.get("current_version_id") or ""
            pv = version_details.get(cur_id, {})
            rows.append((
                p.get("id", "?"),
                p.get("display_name") or p.get("id", "?"),
                cur_id or "(no version deployed yet)",
                version_str(pv) if cur_id else "-",
                "yes" if cur_id else "n/a",
                bool(p.get("is_internal", False)),
            ))
    else:
        for p in products:
            product_id = p.get("id", "?")
            is_internal = bool(p.get("is_internal", False))
            try:
                versions = paginated_get(
                    base_url, token, "/v1/product-versions", "product_versions", {"product_id": product_id}
                )
            except urllib.error.HTTPError as e:
                warn(f"Could not fetch versions for product '{product_id}' (HTTP {e.code})")
                continue
            except urllib.error.URLError as e:
                warn(f"Could not fetch versions for product '{product_id}': {e.reason}")
                continue

            if not versions:
                rows.append((
                    product_id, p.get("display_name") or product_id,
                    "(no version deployed yet)", "-", "n/a", is_internal,
                ))
                continue

            for pv in versions:
                rows.append((
                    pv.get("product_id", product_id),
                    pv.get("display_name") or product_id,
                    pv.get("id", "?"),
                    version_str(pv),
                    "yes" if str(pv.get("is_current", "")).lower() == "true" else "no",
                    is_internal,
                ))

    print(f"\n  {len(rows)} product version(s) found:\n")
    for i, row in enumerate(rows, start=1):
        print_row(i, *row)

    print("  Tip: os-vault-account <product_version_id> <customer_id>  -- open a test account")
    return 0


sys.exit(main())
