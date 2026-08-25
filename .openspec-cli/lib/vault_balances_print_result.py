#!/usr/bin/env python3
"""
vault_balances_print_result.py — v2
Imprime balances vivos de una cuenta. Ajustado a la forma real de
/v1/balances/live: "balances" es una LISTA PLANA de objetos (no un
diccionario por cuenta como se asumia originalmente para /v2/).
"""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_balances_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

balances = data.get("balances", [])
if not balances:
    print("  (sin balances -- cuenta recien creada sin movimientos)")
    sys.exit(0)

print(f"  {'Address':20s} {'Denom':6s} {'Amount':12s} {'Phase':30s}")
print(f"  {'-'*20} {'-'*6} {'-'*12} {'-'*30}")
for b in balances:
    addr = b.get("account_address", "DEFAULT")
    denom = b.get("denomination", "")
    amount = b.get("amount", b.get("net", "?"))
    phase = b.get("phase", "").replace("POSTING_PHASE_", "")
    print(f"  {addr:20s} {denom:6s} {amount:>12s} {phase:30s}")
