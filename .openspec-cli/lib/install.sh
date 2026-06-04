#!/bin/sh
# .openspec-cli/install.sh
# Installs the OpenSpec CLI into ~/.openspec
# Usage: sh .openspec-cli/install.sh
set -e

REPO_CLI_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.openspec"
BIN_DIR="$INSTALL_DIR/bin"
LIB_DIR="$INSTALL_DIR/lib"

GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'; BOLD='\033[1m'
info()    { printf "${CYAN}i  %s${RESET}\n" "$*"; }
success() { printf "${GREEN}ok %s${RESET}\n" "$*"; }
warn()    { printf "${YELLOW}!  %s${RESET}\n" "$*"; }
error()   { printf "${RED}x  %s${RESET}\n" "$*" >&2; }
label()   { printf "${BOLD}%s${RESET}\n" "$*"; }
divider() { printf "${CYAN}%s${RESET}\n" "────────────────────────────────────────────"; }

divider
label "  OpenSpec CLI — Installer"
divider

# ── Check dependencies ────────────────────────────────────────
for dep in curl git; do
  if ! command -v "$dep" > /dev/null 2>&1; then
    error "Missing: $dep"; exit 1
  else
    success "Found: $dep"
  fi
done

# Check Python (py, python3 or python)
PYTHON_CMD=""
for cmd in py python3 python; do
  if command -v "$cmd" > /dev/null 2>&1; then
    ver=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "")
    if [ "$ver" = "3" ]; then PYTHON_CMD="$cmd"; break; fi
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  error "Python 3 not found (tried: py, python3, python)"
  error "Install from: https://www.python.org/downloads/"
  exit 1
else
  success "Found Python 3: $PYTHON_CMD"
fi

if ! command -v gh > /dev/null 2>&1; then
  warn "GitHub CLI (gh) not found — os-commit PR creation will be skipped"
  warn "Install from: https://cli.github.com"
fi

# Check contracts_api (optional — needed for os-vault-test)
if "$PYTHON_CMD" -c "from contracts_api import SmartContractDescriptor" > /dev/null 2>&1; then
  success "Found: contracts_api SDK (Vault testing enabled)"
else
  warn "contracts_api not installed — os-vault-test will not work"
  warn "To install: cd contracts_sdk/contracts_sdk && $PYTHON_CMD -m pip install ."
fi

# ── Create directories ────────────────────────────────────────
mkdir -p "$BIN_DIR" "$LIB_DIR"
success "Install dir: $INSTALL_DIR"

# ── Copy lib files ────────────────────────────────────────────
for lib_file in "$REPO_CLI_DIR/lib/"*.sh "$REPO_CLI_DIR/lib/"*.py; do
  [ -f "$lib_file" ] || continue
  lib_name=$(basename "$lib_file")
  sed 's/\r//' "$lib_file" > "$LIB_DIR/$lib_name"
  chmod +x "$LIB_DIR/$lib_name" 2>/dev/null || true
  success "Installed lib: $lib_name"
done

# ── Copy commands ─────────────────────────────────────────────
for cmd_file in "$REPO_CLI_DIR/commands/"os-*; do
  [ -f "$cmd_file" ] || continue
  cmd_name=$(basename "$cmd_file")
  target="$BIN_DIR/$cmd_name"
  sed 's/\r//' "$cmd_file" > "$target"
  chmod +x "$target"
  success "Installed command: $cmd_name"
done

# ── Placeholders ──────────────────────────────────────────────
touch "$REPO_CLI_DIR/.last-prompt.md"
touch "$REPO_CLI_DIR/.enriched-content.md"
touch "$REPO_CLI_DIR/.review-output.md"
touch "$REPO_CLI_DIR/.last-simulation.json"

# ── Add to PATH ───────────────────────────────────────────────
PATH_LINE="export PATH=\"\$HOME/.openspec/bin:\$PATH\""
for shell_rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
  if [ -f "$shell_rc" ]; then
    if ! grep -q ".openspec/bin" "$shell_rc" 2>/dev/null; then
      printf "\n# OpenSpec CLI\n%s\n" "$PATH_LINE" >> "$shell_rc"
      success "Added to PATH in $shell_rc"
    else
      info "PATH already in $shell_rc"
    fi
  fi
done

# ── Create .env.example ───────────────────────────────────────
ENV_EXAMPLE="$(dirname "$REPO_CLI_DIR")/.env.example"
cat > "$ENV_EXAMPLE" << 'ENV_EOF'
# OpenSpec CLI — environment variables
# Copy to .env and fill in values. NEVER commit .env to git.

# ── Jira Cloud ────────────────────────────────────────────────
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=KAN

# ── Vault Core API (optional — needed for os-vault-* commands) ─
VAULT_BASE_URL=https://your-vault-instance.thought-machine.net
VAULT_TOKEN=your_vault_api_token
VAULT_DEFAULT_DENOMINATION=GBP
ENV_EOF
success "Updated .env.example"

divider
success "OpenSpec CLI installed successfully!"
divider

# ── Print installed commands ──────────────────────────────────
label "  Core workflow:"
info "  os-stack          [--list | <stack>]     Switch or list stacks"
info "  os-agent          [--list | <agent>]     Switch or list AI agents"
info "  os-enrich         <TICKET>               Enrich Jira ticket technically"
info "  os-enrich-apply   <TICKET>               Upload enrichment to Jira"
info "  os-plan           <TICKET>               Generate implementation plan"
info "  os-develop        <TICKET>               Create branch + implementation"
info "  os-commit         [TICKET]               Commit + push + open PR"
info "  os-review         <PR>                   Generate AI code review"
info "  os-review-apply   <PR>                   Publish review to GitHub"
divider
label "  Jira management:"
info "  os-tickets        [status]               List project tickets"
info "  os-create-ticket  [--hu] [summary] [type] Create ticket (--hu = AI user story)"
info "  os-transition     <TICKET> [status]      Move ticket to new status"
divider
label "  Vault Smart Contracts:"
info "  os-vault-test     [file] [--coverage]    Run tests with contracts_api SDK"
info "  os-vault-simulate <contract.py> ...      Simulate against Vault sandbox"
info "  os-vault-deploy   <contract.py> ...      Deploy to Vault as ProductVersion"
info "  os-vault-account  <product_ver> <cust>   Create test account"
info "  os-vault-balances <account_id>           Check live balances"
divider
label "  Setup:"
info "  1. cp .env.example .env && edit .env"
info "  2. gh auth login"
info "  3. os-stack --list && os-stack vault-smart-contracts"
info "  4. os-agent --list && os-agent claude-code"
info "  5. os-tickets"
divider
label "  Reload shell:"
info "  source ~/.bashrc   (bash / Git Bash)"
info "  source ~/.zshrc    (zsh)"
divider