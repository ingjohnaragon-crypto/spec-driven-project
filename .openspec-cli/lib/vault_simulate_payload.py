#!/usr/bin/env python3
"""
vault_simulate_payload.py — FIXED v5
Builds the JSON payload for POST /v1/contracts:simulate
Usage: python3 vault_simulate_payload.py <contract_file> [start_ts] [end_ts] [param_vals_json]

Historial de fixes:
1. Timestamps vacíos -> se resuelven con datetime.
2. smart_contract_param_vals -> es un MAPA {nombre: valor}, no una lista.
3. "outputs" (top-level) -> removido. No es lista de strings; en el schema de
   Core_Api.json es una lista de objetos {"timestamp","derived_params"} para
   snapshots puntuales. No hace falta para una simulación básica.
4. "instructions[].transaction" -> NO EXISTE en el schema. Se deja
   "instructions" vacío por ahora (posting_instruction_batch real pendiente).
5. smart_contracts[].id -> el Core_Api.json (colección Postman) NO lista este
   campo, pero probado empíricamente contra el sandbox real: sin "id" -> error
   "smart contract version \"\" is invalid, ID must be a string containing a
   64 bit integer". Con "id":"1" -> el error desaparece. Se prioriza lo que
   Vault acepta de verdad sobre el documento (puede estar desactualizado).
"""
import sys
import json
from datetime import datetime, timedelta, timezone

contract_file = sys.argv[1]
start_ts_arg = sys.argv[2] if len(sys.argv) > 2 else ""
end_ts_arg = sys.argv[3] if len(sys.argv) > 3 else ""
param_vals_arg = sys.argv[4] if len(sys.argv) > 4 else "{}"

param_vals = json.loads(param_vals_arg) if param_vals_arg else {}

def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

if start_ts_arg:
    start_ts = start_ts_arg
    start_dt = datetime.strptime(start_ts_arg, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
else:
    start_dt = datetime.now(timezone.utc)
    start_ts = iso(start_dt)

if end_ts_arg:
    end_ts = end_ts_arg
else:
    end_dt = start_dt + timedelta(days=30)
    end_ts = iso(end_dt)

with open(contract_file, encoding="utf-8") as f:
    code = f.read()

smart_contract_param_vals = {
    k: str(v)
    for k, v in param_vals.items()
}

payload = {
    "start_timestamp": start_ts,
    "end_timestamp": end_ts,
    "smart_contracts": [
        {
            "id": "1",
            "code": code,
            "smart_contract_param_vals": smart_contract_param_vals,
        }
    ],
    "instructions": [],
}

print(json.dumps(payload, indent=2))