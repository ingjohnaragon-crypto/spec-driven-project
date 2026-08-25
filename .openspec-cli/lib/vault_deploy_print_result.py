#!/usr/bin/env python3
"""vault_deploy_print_result.py — v2, no muestra api_version si Vault no lo devuelve."""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_deploy_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)

pv = result.get("product_version", result)
print(f"\n✅ Product version deployed successfully!")
print(f"   product_version_id : {pv.get('id','?')}")
print(f"   product_id         : {pv.get('product_id','?')}")
print(f"   display_name       : {pv.get('display_name','?')}")
print(f"   is_current         : {pv.get('is_current','?')}")

ver = pv.get('display_version_number') or pv.get('contracts_language_api_version')
if ver:
    if isinstance(ver, dict):
        ver_str = f"{ver.get('major','?')}.{ver.get('minor','?')}.{ver.get('patch','?')}"
    else:
        ver_str = str(ver)
    print(f"   version            : {ver_str}")

print(f"\n   Next steps:")
print(f"   1. Create an account: os-vault-account {pv.get('id','?')} <customer_id>")
print(f"   2. Test with postings via Vault dashboard or API")
