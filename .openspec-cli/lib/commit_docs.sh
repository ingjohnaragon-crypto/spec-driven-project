#!/bin/sh
# commit_docs.sh — helpers for os-commit: stage ticket docs + rich PR body

# Extract markdown section body after a heading that starts with START until next ## heading
os_md_section() {
  _file="$1"
  _start="$2"
  [ -f "$_file" ] || return 0
  awk -v start="$_start" '
    BEGIN { grab = 0 }
    {
      if (index($0, start) == 1) { grab = 1; next }
      if (grab && substr($0, 1, 3) == "## ") { exit }
      if (grab) print
    }
  ' "$_file"
}

os_md_story_points() {
  _file="$1"
  [ -f "$_file" ] || return 0
  grep -oE 'STORY_POINTS:[0-9]+' "$_file" 2>/dev/null | head -1 | cut -d: -f2
}

os_ticket_plan_file() {
  _id="$1"
  _p="$OS_REPO_ROOT/ai-specs/changes/planes/${_id}/${_id}_backend.md"
  [ -f "$_p" ] && echo "$_p"
}

os_ticket_enrich_file() {
  _id="$1"
  _base="$OS_REPO_ROOT/ai-specs/changes/enriquecimientos/${_id}"
  if [ -f "${_base}/${_id}_enriched.md" ]; then
    echo "${_base}/${_id}_enriched.md"
  elif [ -f "${_base}/${_id}_enriched.md.applied" ]; then
    echo "${_base}/${_id}_enriched.md.applied"
  fi
}

os_bullet_or_none() {
  if [ -n "$(printf '%s' "$1" | tr -d '[:space:]')" ]; then
    printf '%s\n' "$1"
  else
    echo "- _(ninguno)_"
  fi
}

# Always stage plan + enrichment for the ticket (documentation archive)
os_stage_ticket_docs() {
  _id="$1"
  [ -n "$_id" ] || return 0

  _plan_dir="$OS_REPO_ROOT/ai-specs/changes/planes/${_id}"
  _enrich_dir="$OS_REPO_ROOT/ai-specs/changes/enriquecimientos/${_id}"

  # Keep a stable .md copy when only .applied remains (post enrich-apply)
  if [ -f "${_enrich_dir}/${_id}_enriched.md.applied" ] \
    && [ ! -f "${_enrich_dir}/${_id}_enriched.md" ]; then
    cp "${_enrich_dir}/${_id}_enriched.md.applied" \
      "${_enrich_dir}/${_id}_enriched.md"
    os_info "Restored docs copy: ai-specs/changes/enriquecimientos/${_id}/${_id}_enriched.md"
  fi

  if [ -d "$_plan_dir" ]; then
    git add "$_plan_dir"
    os_success "Staged plan docs: ai-specs/changes/planes/${_id}/"
  fi
  if [ -d "$_enrich_dir" ]; then
    git add "$_enrich_dir"
    os_success "Staged enrichment docs: ai-specs/changes/enriquecimientos/${_id}/"
  fi
}

# Build PR body to a UTF-8 file and print its path (never echo body to the shell).
# Usage: PR_BODY_FILE="$(os_build_pr_body_file TICKET STAGED LANG)"
os_build_pr_body_file() {
  _ticket="$1"
  _staged="$2"
  _lang="${3:-es}"
  _builder=""
  if [ -f "$OS_REPO_ROOT/.openspec-cli/lib/build_pr_body.py" ]; then
    _builder="$OS_REPO_ROOT/.openspec-cli/lib/build_pr_body.py"
  elif [ -f "$HOME/.openspec/lib/build_pr_body.py" ]; then
    _builder="$HOME/.openspec/lib/build_pr_body.py"
  else
    os_error "build_pr_body.py not found. Re-run: sh .openspec-cli/install.sh"
    return 1
  fi
  _staged_tmp="$(mktemp)"
  _out="$OS_REPO_ROOT/.openspec-cli/.pr-body.md"
  printf '%s\n' "$_staged" | tr -d '\r' > "$_staged_tmp"
  "${OS_PYTHON:-py}" -X utf8 "$_builder" \
    "$_ticket" \
    --lang "$_lang" \
    --staged-file "$_staged_tmp" \
    --repo-root "$OS_REPO_ROOT" \
    --output "$_out"
  _rc=$?
  rm -f "$_staged_tmp"
  [ "$_rc" -eq 0 ] || return "$_rc"
  printf '%s\n' "$_out"
}

# Back-compat: stdout body (avoid on Windows — use os_build_pr_body_file)
os_build_pr_body() {
  _file="$(os_build_pr_body_file "$@")" || return 1
  cat "$_file"
}

os_build_commit_body() {
  _ticket="$1"
  _staged="$(printf '%s' "$2" | tr -d '\r')"
  _lang="${3:-es}"
  _file_count=$(printf '%s\n' "$_staged" | sed '/^$/d' | wc -l | tr -d ' ')

  _plan="$(os_ticket_plan_file "$_ticket")"
  _points=""
  [ -n "$_plan" ] && _points="$(os_md_story_points "$_plan")"

  _contracts=$(printf '%s\n' "$_staged" | grep -E '^contracts/.*\.py$' | sed 's|.*/||;s|\.py$||' | tr '\n' ', ' | sed 's/, $//')
  _has_docs=no
  printf '%s\n' "$_staged" | grep -E '^ai-specs/changes/(planes|enriquecimientos)/' >/dev/null && _has_docs=yes

  if [ "$_lang" = "es" ]; then
    echo "- Implementa ${_ticket}: ${_contracts:-cambios Vault}"
    [ -n "$_points" ] && echo "- Story points: ${_points}"
    echo "- Archivos: ${_file_count}"
    [ "$_has_docs" = "yes" ] && echo "- Incluye plan y enriquecimiento en ai-specs/changes/"
    echo "- Stack: $OS_ACTIVE_STACK"
    echo "- Rama: $CURRENT_BRANCH"
  else
    echo "- Implements ${_ticket}: ${_contracts:-Vault changes}"
    [ -n "$_points" ] && echo "- Story points: ${_points}"
    echo "- Files: ${_file_count}"
    [ "$_has_docs" = "yes" ] && echo "- Includes plan and enrichment under ai-specs/changes/"
    echo "- Stack: $OS_ACTIVE_STACK"
    echo "- Branch: $CURRENT_BRANCH"
  fi
}
