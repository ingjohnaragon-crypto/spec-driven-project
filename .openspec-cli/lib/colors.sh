#!/bin/sh
# .openspec-cli/lib/colors.sh
# Terminal color helpers — sourced by all commands

# Reset
RESET='\033[0m'

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
BOLD='\033[1m'

# Semantic aliases
COLOR_SUCCESS=$GREEN
COLOR_ERROR=$RED
COLOR_WARN=$YELLOW
COLOR_INFO=$CYAN
COLOR_STEP=$BLUE
COLOR_LABEL=$BOLD

# ── Printers ────────────────────────────────────────────────
os_info()    { printf "${COLOR_INFO}ℹ  %s${RESET}\n" "$*"; }
os_success() { printf "${COLOR_SUCCESS}✔  %s${RESET}\n" "$*"; }
os_warn()    { printf "${COLOR_WARN}⚠  %s${RESET}\n" "$*"; }
os_error()   { printf "${COLOR_ERROR}✖  %s${RESET}\n" "$*" >&2; }
os_step()    { printf "${COLOR_STEP}▶  %s${RESET}\n" "$*"; }
os_label()   { printf "${COLOR_LABEL}%s${RESET}\n" "$*"; }
os_divider() { printf "${COLOR_INFO}%s${RESET}\n" "────────────────────────────────────────────"; }
