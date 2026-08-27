#!/usr/bin/env python3
"""vault_products_fetch_and_print.py — lists all Vault products (product versions).

Vault's GET /v1/product-versions requires a product_id -- there is no "list
versions across all products" call. So this lists all Products via
GET /v1/products first, then fetches the version(s) for each one, and
prints a single human-readable list (no raw JSON).

Usage:
  py vault_products_fetch_and_print.py <base_url> <token> <only_current:true|false>
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"

PAGE_SIZE = 30


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


def paginated_get(base_url: str, token: str, path: str, list_key: str) -> list:
    items: list = []
    page_token = ""
    while True:
        sep = "&" if "?" in path else "?"
        url = f"{path}{sep}page_size={PAGE_SIZE}"
        if page_token:
            url += f"&page_token={page_token}"
        data = vault_get(base_url, token, url)
        items.extend(data.get(list_key, []))
        page_token = data.get("next_page_token", "")
        if not page_token:
            break
    return items


def version_str(pv: dict) -> str:
    ver = pv.get("display_version_number") or pv.get("contracts_language_api_version")
    if isinstance(ver, dict):
        return f"{ver.get('major', '?')}.{ver.get('minor', '?')}.{ver.get('patch', '?')}"
    return str(ver) if ver else "?"


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: py vault_products_fetch_and_print.py <base_url> <token> <only_current>", file=sys.stderr)
        return 1

    base_url, token, only_current_arg = sys.argv[1], sys.argv[2], sys.argv[3]
    only_current = only_current_arg.lower() == "true"

    try:
        products = paginated_get(base_url, token, "/v1/products", "products")
    except urllib.error.HTTPError as e:
        err(f"Fetching products failed (HTTP {e.code}):")
        print(e.read().decode(errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        err(f"Could not reach Vault: {e.reason}")
        return 1

    if not products:
        print("\n  (no products found -- deploy one with os-vault-deploy)")
        return 0

    rows = []
    for product in products:
        product_id = product.get("id", "?")
        path = f"/v1/product-versions?product_id={product_id}"
        if only_current:
            path += "&is_current=true"
        try:
            rows.extend(paginated_get(base_url, token, path, "product_versions"))
        except urllib.error.HTTPError as e:
            warn(f"Could not fetch versions for product '{product_id}' (HTTP {e.code})")
        except urllib.error.URLError as e:
            warn(f"Could not fetch versions for product '{product_id}': {e.reason}")

    if not rows:
        print("\n  (no product versions found -- deploy one with os-vault-deploy)")
        return 0

    print(f"\n  {len(rows)} product version(s) found:\n")
    for i, pv in enumerate(rows, start=1):
        is_current = "yes" if str(pv.get("is_current", "")).lower() == "true" else "no"
        print(f"  {i}. {pv.get('display_name', '(no name)')}")
        print(f"     product_id         : {pv.get('product_id', '?')}")
        print(f"     product_version_id : {pv.get('id', '?')}")
        print(f"     version            : {version_str(pv)}")
        print(f"     is_current         : {is_current}")
        print()

    print("  Tip: os-vault-account <product_version_id> <customer_id>  -- open a test account")
    return 0


sys.exit(main())
