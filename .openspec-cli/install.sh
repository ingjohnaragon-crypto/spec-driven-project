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
if ! _os_has_python > /dev/null; then
  error "Missing required dependency: Python 3 (tried: py, python3, python)"
  MISSING=1
else
  success "Python   : $(_os_has_python)"
fi

for dep in curl git; do
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
info "Reload your shell or run:  source ~/.bashrc"
divider

_has_cmd() {
  printf '%s' "$INSTALLED_CMDS" | grep -qx "$1"
}

_print_cmd() {
  # usage: _print_cmd <name> <usage> <description>
  _has_cmd "$1" || return 0
  info "  $1"
  info "      $2"
  info "      → $3"
}

label "  ── Setup / configuración ──"
_print_cmd "os-stack" \
  "os-stack [--list | <stack-name>]" \
  "Activa o lista el stack (vault-smart-contracts, python-fastapi, …)"
_print_cmd "os-agent" \
  "os-agent [--list | <agent-name>]" \
  "Activa o lista el agente (copilot, cursor, claude-code, …)"
_print_cmd "os-language" \
  "os-language [--list | <lang>]" \
  "Cambia el idioma de salida (es / en)"

divider
label "  ── Jira ──"
_print_cmd "os-tickets" \
  "os-tickets [status] [--project KEY]" \
  "Lista tickets del proyecto Jira"
_print_cmd "os-create-ticket" \
  "os-create-ticket [--hu] [--project KEY] [summary] [type]" \
  "Crea un ticket (opción --hu genera HU con IA)"
_print_cmd "os-enrich" \
  "os-enrich <TICKET-ID>" \
  "Enriquece el ticket con detalle técnico (prompt → archivo)"
_print_cmd "os-enrich-apply" \
  "os-enrich-apply <TICKET-ID> [file]" \
  "Sube el enriquecimiento a Jira (+ story points si aplica)"
_print_cmd "os-transition" \
  "os-transition <TICKET-ID> [--list | <estado>]" \
  "Mueve el ticket de estado en Jira"

divider
label "  ── Desarrollo (workflow) ──"
_print_cmd "os-plan" \
  "os-plan <TICKET-ID>" \
  "Genera el plan de implementación (ai-specs/changes/planes/…)"
_print_cmd "os-develop" \
  "os-develop <TICKET-ID>" \
  "Crea rama feature/… y entrega el prompt de implementación"
_print_cmd "os-commit" \
  "os-commit [TICKET-ID]" \
  "Commit + push + PR → develop (incluye plan/enriquecimiento)"

divider
label "  ── Code review (GitHub) ──"
_print_cmd "os-review" \
  "os-review <PR-NUMBER>" \
  "Genera code review AI → .openspec-cli/.review-output.md"
_print_cmd "os-review-apply" \
  "os-review-apply <PR-NUMBER> [file]" \
  "Publica el review en el PR (APPROVE / REQUEST CHANGES)"
_print_cmd "os-review-fix" \
  "os-review-fix <PR-NUMBER>" \
  "Aplica fixes del review y re-genera re-review"

divider
label "  ── Vault Smart Contracts ──"
_print_cmd "os-vault-lint" \
  "os-vault-lint [contracts/ | file.py]" \
  "Lint sandbox Vault (7 reglas: imports, float, ZoneInfo, …)"
_print_cmd "os-vault-test" \
  "os-vault-test [contracts/foo.py | tests/…] [--coverage]" \
  "Lint + pytest; --coverage mide el contrato (>= 90%)"
_print_cmd "os-vault-simulate" \
  "os-vault-simulate <contract.py> [start] [end] [params_json]" \
  "Simula el contrato contra Vault Core API"
_print_cmd "os-vault-deploy" \
  "os-vault-deploy <contract.py> <product_id> <name> [api]" \
  "Despliega ProductVersion en Vault Core"
_print_cmd "os-vault-account" \
  "os-vault-account <product_version_id> <customer_id> [ccy]" \
  "Crea cuenta de prueba ligada a un product version"
_print_cmd "os-vault-balances" \
  "os-vault-balances <account_id>" \
  "Consulta balances en vivo de una cuenta Vault"

divider
label "  Flujo típico Vault"
info "  1. os-enrich KAN-XX && os-enrich-apply KAN-XX"
info "  2. os-plan KAN-XX"
info "  3. os-develop KAN-XX"
info "  4. os-vault-lint contracts/<product>.py"
info "  5. os-vault-test contracts/<product>.py --coverage"
info "  6. os-commit KAN-XX"
info "  7. os-review <PR> && os-review-apply <PR>"
divider
info "Re-run after every git pull on main:"
info "  sh .openspec-cli/install.sh && source ~/.bashrc"
divider
