#!/usr/bin/env python3
"""vault_log_deploy.py — records a successful os-vault-deploy locally.

Vault's API has no "created by" field, so os-vault-products --mine has no
server-side way to tell "products I deployed" apart from everything else in
a shared Vault instance. This appends one JSON line per successful deploy to
a local log file that --mine filters against.

Usage:
  py vault_log_deploy.py <deploy_result_file> <log_file> <contract_file>
"""
import datetime
import json
import sys

if len(sys.argv) < 4:
    print("Usage: py vault_log_deploy.py <deploy_result_file> <log_file> <contract_file>", file=sys.stderr)
    sys.exit(1)

result_file, log_file, contract_file = sys.argv[1:4]

with open(result_file, encoding="utf-8") as f:
    result = json.load(f)

pv = result.get("product_version", result)
product_id = pv.get("product_id", "")

if not product_id:
    # Nothing usable to log -- don't fail the deploy over this.
    sys.exit(0)

entry = {
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "product_id": product_id,
    "display_name": pv.get("display_name", ""),
    "product_version_id": pv.get("id", ""),
    "contract_file": contract_file,
}

with open(log_file, "a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
