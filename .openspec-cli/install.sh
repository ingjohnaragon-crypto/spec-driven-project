#!/bin/sh
# .openspec-cli/install.sh
# ─────────────────────────────────────────────────────────────
# Installs the OpenSpec CLI globally by symlinking commands
# into ~/.openspec/bin and adding it to PATH.
#
# Usage (from repo root):
#   chmod +x .openspec-cli/install.sh
#   ./.openspec-cli/install.sh
# ─────────────────────────────────────────────────────────────
set -e

REPO_CLI_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.openspec"
BIN_DIR="$INSTALL_DIR/bin"

# ── Colors (inline — no sourcing needed at install time) ──────
GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'; BOLD='\033[1m'
info()    { printf "${CYAN}ℹ  %s${RESET}\n" "$*"; }
success() { printf "${GREEN}✔  %s${RESET}\n" "$*"; }
warn()    { printf "${YELLOW}⚠  %s${RESET}\n" "$*"; }
error()   { printf "${RED}✖  %s${RESET}\n" "$*" >&2; }
label()   { printf "${BOLD}%s${RESET}\n" "$*"; }
divider() { printf "${CYAN}%s${RESET}\n" "────────────────────────────────────────────"; }

divider
label "  OpenSpec CLI — Installer"
divider

# ── Check dependencies ────────────────────────────────────────
MISSING=0
for dep in python3 curl git; do
  if ! command -v "$dep" > /dev/null 2>&1; then
    error "Missing required dependency: $dep"
    MISSING=1
  fi
done

if ! command -v gh > /dev/null 2>&1; then
  warn "GitHub CLI (gh) not found — os-commit PR creation will be skipped."
  warn "Install from: https://cli.github.com"
fi

if [ "$MISSING" = "1" ]; then
  error "Install missing dependencies and re-run."
  exit 1
fi

# ── Create install directory ──────────────────────────────────
mkdir -p "$BIN_DIR"

# ── Symlink commands ──────────────────────────────────────────
for cmd_file in "$REPO_CLI_DIR/commands"/os-*; do
  cmd_name=$(basename "$cmd_file")
  target="$BIN_DIR/$cmd_name"

  if [ -L "$target" ]; then
    rm "$target"
  fi

  ln -sf "$cmd_file" "$target"
  chmod +x "$cmd_file"
  success "Linked: $cmd_name -> $target"
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

# ── Create .env.example if not present ───────────────────────
ENV_EXAMPLE="$REPO_CLI_DIR/../.env.example"
if [ ! -f "$ENV_EXAMPLE" ]; then
  cat > "$ENV_EXAMPLE" << 'ENV_EOF'
# OpenSpec CLI — environment variables
# Copy this file to .env (in your project root) and fill in the values.
# NEVER commit .env to version control.

# Jira Cloud
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_TOKEN=your_jira_api_token

# GitHub (optional — gh CLI handles auth separately via: gh auth login)
# GITHUB_TOKEN=your_github_personal_access_token
ENV_EOF
  success "Created .env.example"
fi

# ── Done ──────────────────────────────────────────────────────
divider
success "OpenSpec CLI installed successfully!"
divider
info "Reload your shell or run:"
info "  source ~/.zshrc   (zsh)"
info "  source ~/.bashrc  (bash)"
divider
label "  Available commands:"
info "  os-plan    <TICKET-ID>   Generate implementation plan"
info "  os-develop <TICKET-ID>   Prepare implementation prompt + create branch"
info "  os-commit  [TICKET-ID]   Commit, push and open PR"
info "  os-enrich  <TICKET-ID>   Enrich Jira ticket with technical detail"
divider
label "  Setup:"
info "  1. Copy .env.example to .env"
info "  2. Fill in JIRA_BASE_URL, JIRA_EMAIL, JIRA_TOKEN"
info "  3. Run: gh auth login  (for PR creation)"
info "  4. Test: os-plan KAN-1"
divider
