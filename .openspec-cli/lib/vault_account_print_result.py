#!/usr/bin/env python3
"""vault_account_print_result.py — imprime el resultado de crear una cuenta."""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_account_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)

acct = result.get("account", result)
print(f"\n✅ Account created successfully!")
print(f"   account_id : {acct.get('id','?')}")
print(f"   status     : {acct.get('status','?')}")
print(f"   product_version_id : {acct.get('product_version_id','?')}")
print(f"\n   Check balances: os-vault-balances {acct.get('id','?')}")
