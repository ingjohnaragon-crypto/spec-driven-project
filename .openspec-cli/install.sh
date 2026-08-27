#!/bin/sh
# .openspec-cli/install.sh
# ─────────────────────────────────────────────────────────────
# Installs / refreshes the OpenSpec CLI into ~/.openspec
#
# Usage (from repo root):
#   sh .openspec-cli/install.sh
#
# On Windows (Git Bash), commands are copied (symlinks are unreliable).
# Re-run this script after pulling main to refresh all os-* commands + libs.
# ─────────────────────────────────────────────────────────────
set -e

REPO_CLI_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.openspec"
BIN_DIR="$INSTALL_DIR/bin"
LIB_DIR="$INSTALL_DIR/lib"

# ── Colors (inline — no sourcing needed at install time) ──────
GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'; BOLD='\033[1m'
info()    { printf "${CYAN}ℹ  %s${RESET}\n" "$*"; }
success() { printf "${GREEN}✔  %s${RESET}\n" "$*"; }
warn()    { printf "${YELLOW}⚠  %s${RESET}\n" "$*"; }
error()   { printf "${RED}✖  %s${RESET}\n" "$*" >&2; }
label()   { printf "${BOLD}%s${RESET}\n" "$*"; }
divider() { printf "${CYAN}%s${RESET}\n" "────────────────────────────────────────────"; }

_os_has_python() {
  for cmd in py python3 python; do
    if command -v "$cmd" > /dev/null 2>&1; then
      ver=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "")
      if [ "$ver" = "3" ]; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

divider
label "  OpenSpec CLI — Installer"
divider
info "Source : $REPO_CLI_DIR"
info "Target : $INSTALL_DIR"

# ── Check dependencies ────────────────────────────────────────
MISSING=0
for dep in curl git; do
  if ! command -v "$dep" > /dev/null 2>&1; then
    error "Missing required dependency: $dep"
    MISSING=1
  fi
done

PYTHON_CMD=""
for cmd in python py python3; do
  if command -v "$cmd" > /dev/null 2>&1; then
    ver=$("$cmd" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "")
    if [ "$ver" = "3" ]; then
      PYTHON_CMD="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  error "Python 3 not found (tried: py, python3, python)"
  MISSING=1
else
  success "Found Python 3: $PYTHON_CMD"
fi

if ! command -v gh > /dev/null 2>&1; then
  warn "GitHub CLI (gh) not found — os-commit PR creation will be skipped."
  warn "Install from: https://cli.github.com"
fi

if [ "$MISSING" = "1" ]; then
  error "Install missing dependencies and re-run."
  exit 1
fi

if "$PYTHON_CMD" -c 'from contracts_api import SmartContractDescriptor' > /dev/null 2>&1; then
  success "Found: contracts_api SDK (Vault testing enabled)"
else
  warn "contracts_api not installed -- os-vault-test will not work"
  warn "To install: cd contracts_sdk/contracts_sdk && $PYTHON_CMD -m pip install ."
fi

# ── Create install directory ──────────────────────────────────
mkdir -p "$BIN_DIR" "$LIB_DIR"

# ── Install lib files (always copy — commands resolve ~/.openspec/lib) ──
info "Refreshing libraries..."
for lib_file in "$REPO_CLI_DIR/lib/"*.sh "$REPO_CLI_DIR/lib/"*.py "$REPO_CLI_DIR/lib/"*.md; do
  [ -f "$lib_file" ] || continue
  case "$(basename "$lib_file")" in
    _*) continue ;;  # skip private helpers like _patch_*.py
  esac
  lib_name=$(basename "$lib_file")
  sed 's/\r//' "$lib_file" > "$LIB_DIR/$lib_name"
  chmod +x "$LIB_DIR/$lib_name" 2>/dev/null || true
  success "Installed lib: $lib_name"
done

# ── Install commands ──────────────────────────────────────────
# Prefer symlink to the repo so edits are live; on Windows fall back to copy.
info "Refreshing commands..."
INSTALLED_CMDS=""
for cmd_file in "$REPO_CLI_DIR/commands"/os-*; do
  [ -f "$cmd_file" ] || continue
  cmd_name=$(basename "$cmd_file")
  target="$BIN_DIR/$cmd_name"

  # Remove previous link or stale copy
  rm -f "$target"

  linked=0
  if ln -sf "$cmd_file" "$target" 2>/dev/null; then
    # Git Bash on Windows may create a normal file instead of a symlink
    if [ -L "$target" ]; then
      linked=1
      success "Linked : $cmd_name"
    fi
  fi

  if [ "$linked" = "0" ]; then
    sed 's/\r//' "$cmd_file" > "$target"
    chmod +x "$target"
    success "Copied : $cmd_name"
  fi

  INSTALLED_CMDS="${INSTALLED_CMDS}${cmd_name}
"
done

# Remove bin entries that no longer exist in the repo
for installed in "$BIN_DIR"/os-*; do
  [ -e "$installed" ] || continue
  name=$(basename "$installed")
  if [ ! -f "$REPO_CLI_DIR/commands/$name" ]; then
    rm -f "$installed"
    warn "Removed stale command: $name"
  fi
done

# ── Add to PATH ───────────────────────────────────────────────
PATH_LINE="export PATH=\"\$HOME/.openspec/bin:\$PATH\""
PATH_ADDED=0

for shell_rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
  if [ -f "$shell_rc" ]; then
    if ! grep -q ".openspec/bin" "$shell_rc" 2>/dev/null; then
      echo "" >> "$shell_rc"
      echo "# OpenSpec CLI" >> "$shell_rc"
      echo "$PATH_LINE" >> "$shell_rc"
      success "Added to PATH in $shell_rc"
      PATH_ADDED=1
    else
      info "PATH already configured in $shell_rc"
      PATH_ADDED=1
    fi
  fi
done

if [ "$PATH_ADDED" = "0" ]; then
  warn "Could not find .zshrc or .bashrc — add this line manually:"
  warn "  $PATH_LINE"
fi

# ── Done ──────────────────────────────────────────────────────
divider
success "OpenSpec CLI installed / refreshed successfully!"
divider
info "Reload your shell or run:"
info "  source ~/.zshrc   (zsh)"
info "  source ~/.bashrc  (bash / Git Bash on Windows)"
divider
label "  Multi-agent configuration (set once per project):"
info "  os-stack          [--list | <stack>]       Tech stack → agent file + standards + tooling"
info "  os-agent          [--list | <agent>]       AI agent → clipboard or CLI delivery"
info "  os-language       [--list | <lang>]        Output language (en / es)"
divider
label "  Core workflow (Jira ticket → PR):"
info "  os-enrich         <TICKET>                 Build enrichment prompt (+ deliver to agent)"
info "  os-enrich-apply   <TICKET> [file]          Upload enrichment to Jira"
info "  os-plan           <TICKET>                 Plan prompt → planes/<TICKET>/<TICKET>_backend.md"
info "  os-develop        <TICKET>                 Branch + implement (autonomous on CLI agents)"
info "  os-commit         [TICKET]                 Commit, push, open PR → develop"
info "  os-review         <PR>                     Review prompt → .review-output.md"
info "  os-review-apply   <PR> [file]              Publish review on GitHub"
info "  os-review-fix     <PR> [--no-commit]       Fix loop: apply review + re-review"
divider
label "  Jira management:"
info "  os-tickets        [status] [--project KEY]  List tickets"
info "  os-create-ticket  [--hu] [--project KEY] [summary] [type]"
info "  os-transition     <TICKET> [--list | <state>]"
divider
label "  Vault Smart Contracts (when stack = vault-smart-contracts):"
info "  os-vault-lint     [file|dir]               Sandbox restriction check"
info "  os-vault-test     [file] [--coverage]      Lint + pytest (contracts_api SDK)"
info "  os-vault-simulate <contract.py> [start] [end] [params_json]"
info "  os-vault-deploy   <contract.py> <product_id> \"<display name>\""
info "  os-vault-products [--all]                  List deployed products"
info "  os-vault-account  <product_version_id> <customer_id> [denomination]"
info "  os-vault-balances <account_id>"
divider
label "  AI agents (openspec/config.yaml → agents:):"
info "  copilot, cursor, windsurf  → clipboard (paste .openspec-cli/.last-prompt.md)"
info "  claude-code, aider         → CLI (prompt sent automatically)"
divider
label "  Quick start — clipboard agent (Cursor / Copilot):"
info "  1. cp .env.example .env && gh auth login"
info "  2. os-stack vault-smart-contracts && os-agent cursor && os-language es"
info "  3. os-enrich KAN-XX  → paste output → os-enrich-apply KAN-XX"
info "  4. os-plan KAN-XX    → review ai-specs/changes/planes/KAN-XX/"
info "  5. os-develop KAN-XX → os-vault-test --coverage && os-commit KAN-XX"
divider
label "  Quick start — CLI agent (Claude Code / Aider):"
info "  1. os-agent claude-code && os-stack vault-smart-contracts"
info "  2. os-plan KAN-XX && os-develop KAN-XX   (implementation runs in terminal)"
info "  3. os-vault-test --coverage && os-commit KAN-XX"
info "  4. os-review <PR> && os-review-apply <PR>"
divider
label "  Working files (per agent session):"
info "  .openspec-cli/.last-prompt.md       Last prompt built by any os-* command"
info "  .openspec-cli/.enriched-content.md  Paste enrichment before os-enrich-apply"
info "  .openspec-cli/.review-output.md     Review output (os-review / os-review-apply)"
divider
