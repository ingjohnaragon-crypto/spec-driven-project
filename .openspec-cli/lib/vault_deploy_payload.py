#!/usr/bin/env python3
"""
vault_deploy_payload.py
Builds the JSON payload for POST /v1/product-versions
Usage: python3 vault_deploy_payload.py <contract_file> <product_id> <display_name> <api_version>
"""
import ast
import json
import re
import sys

contract_file = sys.argv[1]
product_id    = sys.argv[2]
display_name  = sys.argv[3]
api_version   = sys.argv[4] if len(sys.argv) > 4 else "3.11.0"

with open(contract_file, encoding="utf-8") as f:
    code = f.read()


def extract_supported_denominations(source: str) -> list:
    patterns = (
        r"SUPPORTED_DENOMINATIONS\s*=\s*(\[[^\]]+\])",
        r"supported_denominations\s*=\s*(\[[^\]]+\])",
    )
    for pattern in patterns:
        match = re.search(pattern, source)
        if not match:
            continue
        try:
            value = ast.literal_eval(match.group(1))
        except (SyntaxError, ValueError):
            continue
        if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
            return value
    return ["GBP"]


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
        "supported_denominations": extract_supported_denominations(code),
        "is_current":      True
    }
}

print(json.dumps(payload, indent=2))
