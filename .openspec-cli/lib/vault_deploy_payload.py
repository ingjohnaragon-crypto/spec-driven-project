#!/usr/bin/env python3
"""
vault_deploy_payload.py
Builds the JSON payload for POST /v1/product-versions
Usage: python3 vault_deploy_payload.py <contract_file> <product_id> <display_name> <api_version>
"""
import sys, json

contract_file = sys.argv[1]
product_id    = sys.argv[2]
display_name  = sys.argv[3]
api_version   = sys.argv[4] if len(sys.argv) > 4 else "3.11.0"

with open(contract_file, encoding="utf-8") as f:
    code = f.read()

payload = {
    "product_version": {
        "product_id":      product_id,
        "display_name":    display_name,
        "code":            code,
        "contracts_language_api_version": {
            "major": int(api_version.split(".")[0]),
            "minor": int(api_version.split(".")[1]),
            "patch": int(api_version.split(".")[2])
        },
        "params":          [],
        "supported_denominations": ["GBP"],
        "is_current":      True
    }
}

print(json.dumps(payload, indent=2))
