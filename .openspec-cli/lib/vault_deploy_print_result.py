#!/usr/bin/env python3
"""
vault_deploy_print_result.py — imprime el resultado del deploy de un
Smart Contract. Reemplaza el heredoc "${OS_PYTHON}" << PYEOF ... PYEOF que
tenia os-vault-deploy embebido inline, el cual fallaba con FileNotFoundError
porque incrustaba la ruta /tmp/... como texto DENTRO del script Python en
vez de pasarla como argumento -- MSYS/Git Bash solo traduce rutas
POSIX->Windows cuando van como argumento directo a un ejecutable nativo.

Usage: py vault_deploy_print_result.py <RESULT_FILE>
"""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: py vault_deploy_print_result.py <RESULT_FILE>", file=sys.stderr)
    sys.exit(1)

result_file = sys.argv[1]

with open(result_file, encoding="utf-8") as f:
    result = json.load(f)

pv = result.get("product_version", result)
print(f"\n✅ Product version deployed successfully!")
print(f"   product_version_id : {pv.get('id','?')}")
print(f"   product_id         : {pv.get('product_id','?')}")
print(f"   display_name       : {pv.get('display_name','?')}")
print(f"   is_current         : {pv.get('is_current','?')}")
print(f"   api_version        : {pv.get('contracts_language_api_version','?')}")
print(f"\n   Next steps:")
print(f"   1. Create an account: os-vault-account <product_version_id>")
print(f"   2. Test with postings via Vault dashboard or API")
