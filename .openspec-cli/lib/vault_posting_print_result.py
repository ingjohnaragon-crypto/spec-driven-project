#!/usr/bin/env python3
"""vault_posting_print_result.py — imprime resultado de crear un posting."""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_posting_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)

pib = result.get("posting_instruction_batch", result)
print(f"\n✅ Posting created successfully!")
print(f"   batch_id : {pib.get('id','?')}")
print(f"   status   : {pib.get('status','?')}")
for pi in pib.get("posting_instructions", []):
    print(f"   instruction_id : {pi.get('id','?')}")
print(f"\n   Check balances: os-vault-balances <account_id>")
