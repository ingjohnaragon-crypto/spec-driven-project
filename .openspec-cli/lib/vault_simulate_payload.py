#!/usr/bin/env python3
"""
vault_simulate_payload.py
Builds the JSON payload for POST /v1/contracts:simulate
Usage: python3 vault_simulate_payload.py <contract_file> <start_ts> <end_ts> <param_vals_json>
"""
import sys, json, os

contract_file = sys.argv[1]
start_ts      = sys.argv[2]
end_ts        = sys.argv[3]
param_vals    = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}

with open(contract_file, encoding="utf-8") as f:
    code = f.read()

# Build param vals array from dict
smart_contract_param_vals = [
    {"name": k, "value": str(v)}
    for k, v in param_vals.items()
]

payload = {
    "start_timestamp": start_ts,
    "end_timestamp":   end_ts,
    "smart_contracts": [
        {
            "code": code,
            "smart_contract_param_vals": smart_contract_param_vals
        }
    ],
    "instructions": [
        {
            # Default: one deposit at start to trigger pre_posting_hook
            "timestamp": start_ts,
            "transaction": {
                "amount": "100",
                "denomination": "GBP",
                "instruction_details": {
                    "description": "OpenSpec simulation test deposit"
                }
            }
        }
    ],
    "outputs": [
        "BALANCES",
        "POSTING_INSTRUCTION_BATCHES",
        "LOGS"
    ]
}

print(json.dumps(payload, indent=2))
