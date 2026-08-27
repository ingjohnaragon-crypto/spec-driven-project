#!/usr/bin/env python3
"""vault_products_print_result.py — prints a human-readable list of Vault products (product versions)."""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_products_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

versions = data.get("product_versions", [])
if not versions:
    print("\n  (no products found -- deploy one with os-vault-deploy)")
    sys.exit(0)


def version_str(pv):
    ver = pv.get("display_version_number") or pv.get("contracts_language_api_version")
    if isinstance(ver, dict):
        return f"{ver.get('major', '?')}.{ver.get('minor', '?')}.{ver.get('patch', '?')}"
    return str(ver) if ver else "?"


print(f"\n  {len(versions)} product(s) found:\n")
for i, pv in enumerate(versions, start=1):
    is_current = "yes" if str(pv.get("is_current", "")).lower() == "true" else "no"
    print(f"  {i}. {pv.get('display_name', '(no name)')}")
    print(f"     product_id         : {pv.get('product_id', '?')}")
    print(f"     product_version_id : {pv.get('id', '?')}")
    print(f"     version            : {version_str(pv)}")
    print(f"     is_current         : {is_current}")
    print()

print("  Tip: os-vault-account <product_version_id> <customer_id>  -- open a test account")

if data.get("next_page_token"):
    print("\n  Note: more products exist beyond this page (pagination not yet supported by this command).")
