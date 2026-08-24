#!/usr/bin/bash
# debug_payload.sh — genera el payload de simulate y lo valida SIN llamar a Vault.
# Corre esto desde la raíz del repo:
#   bash debug_payload.sh contracts/savings_product.py

set -euo pipefail

CONTRACT_FILE="${1:-contracts/savings_product.py}"
OUT="/tmp/debug_simulate_payload.json"

# Usa el MISMO script que usa os-vault-simulate
py .openspec-cli/lib/vault_simulate_payload.py "${CONTRACT_FILE}" > "${OUT}"

echo "── Payload guardado en: ${OUT}"
echo "── Tamaño: $(wc -c < "${OUT}") bytes"
echo ""
echo "── Validando JSON con python -m json.tool ..."
if py -m json.tool "${OUT}" > /dev/null 2>&1; then
    echo "✅ JSON VÁLIDO — el generador está bien. El problema está en cómo os-vault-simulate lo envía a curl."
else
    echo "❌ JSON INVÁLIDO — aquí está el detalle:"
    py -m json.tool "${OUT}"
fi

echo ""
echo "── Contexto alrededor del carácter 8939 (donde Vault reportó el error):"
py -c "
with open('${OUT}', 'rb') as f:
    data = f.read()
pos = 8939
start = max(0, pos - 60)
end = min(len(data), pos + 60)
print(repr(data[start:end]))
print(' ' * (min(60, pos-start)) + '^-- posición 8939 aprox aquí')
"
