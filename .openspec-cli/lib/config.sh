#!/bin/sh

_os_find_python() {
  for cmd in py python3 python; do
    if command -v "$cmd" > /dev/null 2>&1; then
      result=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "")
      if [ "$result" = "3" ]; then echo "$cmd"; return 0; fi
    fi
  done
  return 1
}

_os_find_root() {
  dir="$(pwd)"
  while [ "$dir" != "/" ]; do
    [ -f "$dir/openspec/config.yaml" ] && echo "$dir" && return 0
    dir="$(dirname "$dir")"
  done
  return 1
}

os_load_config() {
  OS_REPO_ROOT="$(_os_find_root)"
  if [ -z "$OS_REPO_ROOT" ]; then os_error "openspec/config.yaml not found."; exit 1; fi
  OS_CONFIG="$OS_REPO_ROOT/openspec/config.yaml"
  OS_PYTHON="$(_os_find_python 2>/dev/null || true)"
  PARSER="$HOME/.openspec/lib/parse_config.py"
  result=$($OS_PYTHON "$PARSER" "$OS_CONFIG" 2>/dev/null)
  OS_ACTIVE_STACK=$(grep "^stack:" "$OS_CONFIG" | head -1 | sed "s/^stack:[[:space:]]*//" | tr -d "")
  OS_STACK_LABEL=$(echo "$result"   | grep "^label="            | cut -d= -f2-)
  OS_BUILD_CMD=$(echo "$result"     | grep "^build_command="    | cut -d= -f2-)
  OS_TEST_CMD=$(echo "$result"      | grep "^test_command="     | cut -d= -f2-)
  OS_RUN_CMD=$(echo "$result"       | grep "^run_command="      | cut -d= -f2-)
  OS_LINT_CMD=$(echo "$result"      | grep "^lint_command="     | cut -d= -f2-)
  OS_COVERAGE_CMD=$(echo "$result"  | grep "^coverage_command=" | cut -d= -f2-)
  OS_AGENT_REL=$(echo "$result"     | grep "^agent="            | cut -d= -f2-)
  OS_STANDARDS_REL=$(echo "$result" | grep "^standards="        | cut -d= -f2-)
  OS_AGENT_PATH="$OS_REPO_ROOT/$OS_AGENT_REL"
  OS_STANDARDS_PATH="$OS_REPO_ROOT/$OS_STANDARDS_REL"
  export OS_REPO_ROOT OS_CONFIG OS_ACTIVE_STACK OS_STACK_LABEL OS_PYTHON
  export OS_BUILD_CMD OS_TEST_CMD OS_RUN_CMD OS_LINT_CMD OS_COVERAGE_CMD
  export OS_AGENT_PATH OS_STANDARDS_PATH
}

os_load_env() {
  env_file="${OS_REPO_ROOT:-$(pwd)}/.env"
  if [ ! -f "$env_file" ]; then os_warn ".env not found"; return; fi
  JIRA_BASE_URL=$(grep "^JIRA_BASE_URL=" "$env_file" | cut -d= -f2- | tr -d "")
  JIRA_EMAIL=$(grep    "^JIRA_EMAIL="    "$env_file" | cut -d= -f2- | tr -d "")
  JIRA_TOKEN=$(grep    "^JIRA_TOKEN="    "$env_file" | cut -d= -f2- | tr -d "")
  export JIRA_BASE_URL JIRA_EMAIL JIRA_TOKEN
  os_success "Loaded .env"
}

os_require_jira_env() {
  missing=0
  if [ -z "$JIRA_BASE_URL" ]; then os_error "Missing: JIRA_BASE_URL"; missing=1; fi
  if [ -z "$JIRA_EMAIL" ];    then os_error "Missing: JIRA_EMAIL";    missing=1; fi
  if [ -z "$JIRA_TOKEN" ];    then os_error "Missing: JIRA_TOKEN";    missing=1; fi
  if [ "$missing" = "1" ]; then os_info "Edit your .env file."; exit 1; fi
}

os_print_config() {
  os_divider
  os_label "  OpenSpec - Active Configuration"
  os_divider
  os_info "Repo root : $OS_REPO_ROOT"
  os_info "Python    : ${OS_PYTHON:-not found}"
  os_info "Stack     : $OS_ACTIVE_STACK ($OS_STACK_LABEL)"
  os_info "Build     : $OS_BUILD_CMD"
  os_info "Test      : $OS_TEST_CMD"
  os_info "Coverage  : $OS_COVERAGE_CMD"
  os_info "Agent     : $OS_AGENT_PATH"
  os_info "Standards : $OS_STANDARDS_PATH"
  os_divider
}
