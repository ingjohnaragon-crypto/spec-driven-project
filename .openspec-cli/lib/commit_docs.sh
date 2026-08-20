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

# Build a detailed PR body from plan + enrichment + staged files
os_build_pr_body() {
  _ticket="$1"
  _staged="$2"
  _lang="${3:-es}"

  _plan="$(os_ticket_plan_file "$_ticket")"
  _enrich="$(os_ticket_enrich_file "$_ticket")"
  _points=""
  [ -n "$_plan" ] && _points="$(os_md_story_points "$_plan")"
  [ -z "$_points" ] && [ -n "$_enrich" ] && _points="$(os_md_story_points "$_enrich")"

  _plan_title=""
  if [ -n "$_plan" ]; then
    _plan_title="$(head -1 "$_plan" | sed 's/^#[[:space:]]*//')"
  fi

  _resumen=""
  if [ -n "$_plan" ]; then
    _resumen="$(os_md_section "$_plan" "## 1. Resumen")"
  fi
  if [ -z "$_resumen" ] && [ -n "$_enrich" ]; then
    _resumen="$(os_md_section "$_enrich" "## Descripción mejorada")"
  fi

  _decisiones=""
  if [ -n "$_plan" ]; then
    _decisiones="$(os_md_section "$_plan" "### 2.1 Decisiones")"
  fi

  _aceptacion=""
  if [ -n "$_enrich" ]; then
    _aceptacion="$(os_md_section "$_enrich" "## Criterios de aceptación")"
  fi

  _contracts="$(printf '%s\n' "$_staged" | grep -E '^contracts/.*\.py$' | sed 's/^/- /' || true)"
  _tests="$(printf '%s\n' "$_staged" | grep -E '^tests/' | sed 's/^/- /' || true)"
  _docs="$(printf '%s\n' "$_staged" | grep -E '^ai-specs/changes/(planes|enriquecimientos)/' | sed 's/^/- /' || true)"
  _tooling="$(printf '%s\n' "$_staged" | grep -E '^(\.openspec-cli/|ai-specs/\.commands/)' | sed 's/^/- /' || true)"

  _contracts_block="$(os_bullet_or_none "$_contracts")"
  _tests_block="$(os_bullet_or_none "$_tests")"
  _docs_block="$(os_bullet_or_none "$_docs")"
  _tooling_block="$(os_bullet_or_none "$_tooling")"
  _jira_url="${JIRA_BASE_URL:-}/browse/${_ticket}"

  if [ "$_lang" = "es" ]; then
    printf '%s\n' "## Resumen"
    printf '%s\n' "${_plan_title:-Implementa $_ticket}"
    printf '\n'
    printf '%s\n' "Stack: \`$OS_ACTIVE_STACK\` ($OS_STACK_LABEL)"
    [ -n "$_points" ] && printf '%s\n' "Story points: **$_points**"
    printf '\n'
    printf '%s\n' "${_resumen:-Implementa $_ticket en el stack activo.}"
    printf '\n'
    printf '%s\n' "## Decisiones clave"
    printf '%s\n' "${_decisiones:-_(ver plan de implementación)_}"
    printf '\n'
    printf '%s\n' "## Criterios de aceptación"
    printf '%s\n' "${_aceptacion:-_(ver enriquecimiento)_}"
    printf '\n'
    printf '%s\n' "## Contratos"
    printf '%s\n' "$_contracts_block"
    printf '\n'
    printf '%s\n' "## Tests"
    printf '%s\n' "$_tests_block"
    printf '\n'
    printf '%s\n' "## Documentación (plan / enriquecimiento)"
    printf '%s\n' "$_docs_block"
    printf '\n'
    printf '%s\n' "## Tooling / templates"
    printf '%s\n' "$_tooling_block"
    printf '\n'
    printf '%s\n' "## Checklist"
    printf '%s\n' "- [ ] Tests pasan (\`os-vault-test\` / \`$OS_TEST_CMD\`)"
    printf '%s\n' "- [ ] Cobertura >= 90% (\`$OS_COVERAGE_CMD\`)"
    printf '%s\n' "- [ ] Plan y enriquecimiento versionados en \`ai-specs/changes/\`"
    printf '%s\n' "- [ ] El contrato respeta las restricciones del sandbox Vault"
    printf '\n'
    printf '%s\n' "## Referencias"
    [ -n "$_plan" ] && printf '%s\n' "- Plan: \`ai-specs/changes/planes/${_ticket}/${_ticket}_backend.md\`"
    [ -n "$_enrich" ] && printf '%s\n' "- Enriquecimiento: \`ai-specs/changes/enriquecimientos/${_ticket}/\`"
    printf '%s\n' "- Jira: [${_ticket}](${_jira_url})"
  else
    printf '%s\n' "## Summary"
    printf '%s\n' "${_plan_title:-Implements $_ticket}"
    printf '\n'
    printf '%s\n' "Stack: \`$OS_ACTIVE_STACK\` ($OS_STACK_LABEL)"
    [ -n "$_points" ] && printf '%s\n' "Story points: **$_points**"
    printf '\n'
    printf '%s\n' "${_resumen:-Implements $_ticket on the active stack.}"
    printf '\n'
    printf '%s\n' "## Key decisions"
    printf '%s\n' "${_decisiones:-_(see implementation plan)_}"
    printf '\n'
    printf '%s\n' "## Acceptance criteria"
    printf '%s\n' "${_aceptacion:-_(see enrichment)_}"
    printf '\n'
    printf '%s\n' "## Contracts"
    printf '%s\n' "$_contracts_block"
    printf '\n'
    printf '%s\n' "## Tests"
    printf '%s\n' "$_tests_block"
    printf '\n'
    printf '%s\n' "## Documentation (plan / enrichment)"
    printf '%s\n' "$_docs_block"
    printf '\n'
    printf '%s\n' "## Tooling / templates"
    printf '%s\n' "$_tooling_block"
    printf '\n'
    printf '%s\n' "## Checklist"
    printf '%s\n' "- [ ] Tests pass (\`os-vault-test\` / \`$OS_TEST_CMD\`)"
    printf '%s\n' "- [ ] Coverage >= 90% (\`$OS_COVERAGE_CMD\`)"
    printf '%s\n' "- [ ] Plan and enrichment versioned under \`ai-specs/changes/\`"
    printf '%s\n' "- [ ] Contract respects Vault Python sandbox restrictions"
    printf '\n'
    printf '%s\n' "## References"
    [ -n "$_plan" ] && printf '%s\n' "- Plan: \`ai-specs/changes/planes/${_ticket}/${_ticket}_backend.md\`"
    [ -n "$_enrich" ] && printf '%s\n' "- Enrichment: \`ai-specs/changes/enriquecimientos/${_ticket}/\`"
    printf '%s\n' "- Jira: [${_ticket}](${_jira_url})"
  fi
}

os_build_commit_body() {
  _ticket="$1"
  _staged="$2"
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
