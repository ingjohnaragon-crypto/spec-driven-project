#!/bin/sh
# .openspec-cli/lib/language.sh
# Resolves the active output language from openspec/config.yaml.
# Applies to everything the framework generates: code, comments, docs,
# Jira content, commit messages, PR titles/bodies.

# ── Resolve active language from config ──────────────────────
os_load_language() {
  OS_ACTIVE_LANGUAGE=$(grep "^language:" "$OS_CONFIG" | head -1 \
    | sed 's/^language:[[:space:]]*//' | tr -d '"' | tr -d "'" | tr -d '\r')

  OS_ACTIVE_LANGUAGE="${OS_ACTIVE_LANGUAGE:-en}"

  _language_result=$(py -X utf8 "$HOME/.openspec/lib/parse_language.py" \
    "$OS_CONFIG" "$OS_ACTIVE_LANGUAGE" 2>/dev/null || echo "")

  OS_LANGUAGE_LABEL=$(echo "$_language_result" | grep "^label=" | cut -d= -f2-)
  OS_LANGUAGE_LABEL="${OS_LANGUAGE_LABEL:-$OS_ACTIVE_LANGUAGE}"

  case "$OS_ACTIVE_LANGUAGE" in
    es)
      OS_LANGUAGE_DIRECTIVE="Escribe TODA la salida en español: identificadores de código (variables, funciones, clases, archivos), comentarios de código, mensajes de log y error, mensajes de commit, títulos y descripciones de PR, contenido de tickets de Jira y documentación técnica. Incluye los encabezados de sección. Mantén sin traducir las palabras reservadas de Python, los nombres de hooks Vault (pre_posting_code, post_posting_code, scheduled_code, activation_hook, etc.), los tipos de contracts_api y los nombres de APIs/paquetes de terceros."
      ;;
    *)
      OS_LANGUAGE_DIRECTIVE="Write ALL output in English: source code identifiers (variables, functions, classes, files), code comments, log and error messages, commit messages, PR titles/descriptions, Jira ticket content, and technical documentation. Section headers must also be in English. Keep Vault hook names, contracts_api types, and third-party APIs untranslated."
      ;;
  esac

  export OS_ACTIVE_LANGUAGE OS_LANGUAGE_LABEL OS_LANGUAGE_DIRECTIVE
}

# ── Print active language summary ────────────────────────────
os_print_language() {
  os_info "Language  : $OS_ACTIVE_LANGUAGE ($OS_LANGUAGE_LABEL)"
}
