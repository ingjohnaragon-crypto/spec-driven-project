#!/usr/bin/env bash
# install-vault-patch.sh
# Adds Vault commands to existing OpenSpec installation
# Run from repo root: sh .openspec-cli/install-vault-patch.sh

set -euo pipefail

BIN_DIR="${HOME}/.openspec/bin"
LIB_DIR="${HOME}/.openspec/lib"
CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Vault commands..."

# Copy vault library files
cp "${CLI_DIR}/lib/vault.sh"                   "${LIB_DIR}/vault.sh"
cp "${CLI_DIR}/lib/vault_simulate_payload.py"  "${LIB_DIR}/vault_simulate_payload.py"
cp "${CLI_DIR}/lib/vault_deploy_payload.py"    "${LIB_DIR}/vault_deploy_payload.py"

# Copy vault commands
for cmd in os-vault-simulate os-vault-deploy os-vault-account os-vault-balances; do
    cp "${CLI_DIR}/commands/${cmd}" "${BIN_DIR}/${cmd}"
    chmod +x "${BIN_DIR}/${cmd}"
    echo "  ✔ ${cmd}"
done

echo ""
echo "Add to your .env:"
echo "  VAULT_BASE_URL=https://your-vault-instance.com"
echo "  VAULT_TOKEN=your_vault_api_token"
echo ""
echo "Done. Try: os-vault-simulate contracts/my_product.py"
