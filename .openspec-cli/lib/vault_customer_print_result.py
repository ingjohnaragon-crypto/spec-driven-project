#!/usr/bin/env python3
"""vault_customer_print_result.py — imprime el resultado de crear un customer."""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_customer_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)

cust = result.get("customer", result)
print(f"\n✅ Customer created successfully!")
print(f"   customer_id : {cust.get('id','?')}")
print(f"   status      : {cust.get('status','?')}")
details = cust.get('customer_details', {})
print(f"   name        : {details.get('first_name','?')} {details.get('last_name','?')}")
print(f"\n   Next step:")
print(f"   os-vault-account 9652 {cust.get('id','?')}")
