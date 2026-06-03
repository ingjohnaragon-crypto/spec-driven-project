#!/usr/bin/env bash
# vault.sh — Vault Core API v1 helpers for OpenSpec
# Requires: VAULT_BASE_URL, VAULT_TOKEN in .env

# ── Auth header ───────────────────────────────────────────────
vault_auth_header() {
    echo "Authorization: Bearer ${VAULT_TOKEN}"
}

# ── GET helper ────────────────────────────────────────────────
vault_get() {
    local path="$1"
    curl -sf \
        -H "$(vault_auth_header)" \
        -H "Content-Type: application/json" \
        "${VAULT_BASE_URL}${path}"
}

# ── POST helper ───────────────────────────────────────────────
vault_post() {
    local path="$1"
    local body="$2"
    curl -sf \
        -X POST \
        -H "$(vault_auth_header)" \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "${VAULT_BASE_URL}${path}"
}

# ── Simulate a Smart Contract ─────────────────────────────────
# Usage: vault_simulate <contract_file> <start_ts> <end_ts> [param_vals_json]
vault_simulate() {
    local contract_file="$1"
    local start_ts="${2:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
    local end_ts="${3:-$(date -u -d '+30 days' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+30d +%Y-%m-%dT%H:%M:%SZ)}"
    local param_vals="${4:-{}}"

    if [ ! -f "${contract_file}" ]; then
        echo "ERROR: Contract file not found: ${contract_file}" >&2
        return 1
    fi

    local code
    code=$(cat "${contract_file}")

    # Build payload using Python to handle escaping safely
    py "${OS_CLI_LIB}/vault_simulate_payload.py" \
        "${contract_file}" \
        "${start_ts}" \
        "${end_ts}" \
        "${param_vals}"
}

# ── Deploy product version ────────────────────────────────────
# Usage: vault_deploy <contract_file> <product_id> <display_name> [api_version]
vault_deploy() {
    local contract_file="$1"
    local product_id="$2"
    local display_name="$3"
    local api_version="${4:-3.11.0}"

    if [ ! -f "${contract_file}" ]; then
        echo "ERROR: Contract file not found: ${contract_file}" >&2
        return 1
    fi

    py "${OS_CLI_LIB}/vault_deploy_payload.py" \
        "${contract_file}" \
        "${product_id}" \
        "${display_name}" \
        "${api_version}" | \
    vault_post "/v1/product-versions" "$(cat /dev/stdin)"
}

# ── Get account balances ──────────────────────────────────────
vault_balances() {
    local account_id="$1"
    vault_get "/v2/balances/live?account_ids=${account_id}"
}

# ── Get product versions ──────────────────────────────────────
vault_product_versions() {
    local product_id="$1"
    vault_get "/v1/product-versions?product_id=${product_id}&is_current=true"
}