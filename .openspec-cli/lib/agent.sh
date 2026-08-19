#!/bin/sh
# .openspec-cli/lib/agent.sh
# Resolves the active AI agent from openspec/config.yaml
# and delivers prompts according to the agent's delivery method.

# ── Resolve active agent from config ─────────────────────────
os_load_agent() {
  PARSER="$HOME/.openspec/lib/parse_config.py"

  # Read active agent name
  OS_ACTIVE_AGENT=$(grep "^agent:" "$OS_CONFIG" | head -1 \
    | sed 's/^agent:[[:space:]]*//' | tr -d '"' | tr -d "'" | tr -d '\r')

  OS_ACTIVE_AGENT="${OS_ACTIVE_AGENT:-copilot}"

  # Parse agent fields using dedicated Python script
  _agent_result=$(py -X utf8 "$HOME/.openspec/lib/parse_agent.py" \
    "$OS_CONFIG" "$OS_ACTIVE_AGENT" 2>/dev/null || echo "")

  OS_AGENT_LABEL=$(echo "$_agent_result"    | grep "^label="    | cut -d= -f2-)
  OS_AGENT_DELIVERY=$(echo "$_agent_result" | grep "^delivery=" | cut -d= -f2-)
  OS_AGENT_COMMAND=$(echo "$_agent_result"  | grep "^command="  | cut -d= -f2-)
  OS_AGENT_ARGS=$(echo "$_agent_result"     | grep "^args="     | cut -d= -f2-)

  # Defaults
  OS_AGENT_DELIVERY="${OS_AGENT_DELIVERY:-clipboard}"
  OS_AGENT_COMMAND="${OS_AGENT_COMMAND:-null}"

  export OS_ACTIVE_AGENT OS_AGENT_LABEL OS_AGENT_DELIVERY \
         OS_AGENT_COMMAND OS_AGENT_ARGS
}

# ── Low-level: invoke the active CLI agent on a prompt ───────
# Usage: os_agent_run <prompt_file> [output_file]
# Handles the per-agent invocation style (stdin vs argument), so
# callers never need to know how a given CLI agent expects input.
#   - No output_file: agent stdout/stderr are inherited (the user
#     watches it work — used when the agent edits files directly).
#   - output_file given: agent stdout is captured there, stderr
#     discarded (used when the response text itself is the result).
os_agent_run() {
  _PROMPT_FILE="$1"
  _OUTPUT_FILE="${2:-}"

  if [ "$OS_AGENT_COMMAND" = "null" ] || [ -z "$OS_AGENT_COMMAND" ]; then
    os_error "No CLI command configured for agent: $OS_ACTIVE_AGENT"
    return 1
  fi

  if ! command -v "$OS_AGENT_COMMAND" > /dev/null 2>&1; then
    os_error "Agent command not found: $OS_AGENT_COMMAND"
    os_info  "Install $OS_AGENT_LABEL or switch agent: os-agent copilot"
    return 1
  fi

  case "$OS_ACTIVE_AGENT" in
    aider)
      # Aider takes the prompt as an argument (--message "<text>"), not stdin
      _PROMPT_CONTENT=$(cat "$_PROMPT_FILE")
      if [ -n "$_OUTPUT_FILE" ]; then
        "$OS_AGENT_COMMAND" $OS_AGENT_ARGS "$_PROMPT_CONTENT" > "$_OUTPUT_FILE" 2>/dev/null
      else
        "$OS_AGENT_COMMAND" $OS_AGENT_ARGS "$_PROMPT_CONTENT"
      fi
      ;;
    *)
      # Generic / claude-code: prompt is piped via stdin
      if [ -n "$_OUTPUT_FILE" ]; then
        "$OS_AGENT_COMMAND" $OS_AGENT_ARGS < "$_PROMPT_FILE" > "$_OUTPUT_FILE" 2>/dev/null
      else
        "$OS_AGENT_COMMAND" $OS_AGENT_ARGS < "$_PROMPT_FILE"
      fi
      ;;
  esac
}

# ── Low-level: copy a file's content to the system clipboard ─
# Usage: os_copy_to_clipboard <file>  → 0 if copied, 1 if no
# clipboard tool was found (Windows/macOS/Linux X11).
os_copy_to_clipboard() {
  _FILE="$1"
  if command -v clip.exe > /dev/null 2>&1; then
    cat "$_FILE" | clip.exe && return 0
  elif command -v pbcopy > /dev/null 2>&1; then
    cat "$_FILE" | pbcopy && return 0
  elif command -v xclip > /dev/null 2>&1; then
    cat "$_FILE" | xclip -selection clipboard && return 0
  elif command -v xsel > /dev/null 2>&1; then
    cat "$_FILE" | xsel --clipboard --input && return 0
  fi
  return 1
}

# ── Deliver prompt to the active agent (fire-and-forget) ─────
# Usage: os_deliver_prompt <prompt_file> [next_step_hint]
# Used when the caller has nothing further to do once the agent
# has been shown the prompt (e.g. os-plan).
os_deliver_prompt() {
  PROMPT_FILE="$1"
  NEXT_HINT="${2:-}"

  if [ ! -f "$PROMPT_FILE" ]; then
    os_error "Prompt file not found: $PROMPT_FILE"
    exit 1
  fi

  case "$OS_AGENT_DELIVERY" in

    clipboard)
      os_divider
      if os_copy_to_clipboard "$PROMPT_FILE"; then
        os_success "Prompt copied to clipboard!"
        os_info    "Paste into $OS_AGENT_LABEL chat (Ctrl+V / Cmd+V)"
      else
        os_warn "Clipboard not available — copy manually:"
        os_info "  cat $PROMPT_FILE | clip"
      fi

      if [ -n "$NEXT_HINT" ]; then
        os_divider
        os_label "  Next steps:"
        echo "$NEXT_HINT" | while IFS= read -r line; do
          os_info "$line"
        done
      fi
      os_divider
      ;;

    cli)
      os_divider
      os_step "Sending prompt to $OS_AGENT_LABEL..."
      os_divider
      os_agent_run "$PROMPT_FILE" || exit 1
      os_divider
      os_success "Done — $OS_AGENT_LABEL completed the task."
      os_divider
      ;;

    *)
      os_error "Unknown delivery method: $OS_AGENT_DELIVERY"
      os_info  "Valid options: clipboard, cli"
      exit 1
      ;;
  esac
}

# ── Deliver a prompt to an agent that acts autonomously ──────
# Usage: os_deliver_prompt_autonomous <prompt_file> [wait_message]
# Used when the agent edits files directly (os-develop, os-review-fix).
#   - CLI agents: run inline so the user watches it work.
#   - Clipboard agents: copy the prompt; if wait_message is set,
#     block on Enter so the caller can safely continue afterwards
#     (e.g. run tests). If omitted, control returns immediately.
os_deliver_prompt_autonomous() {
  PROMPT_FILE="$1"
  WAIT_MESSAGE="${2:-}"

  if [ "${OS_AGENT_DELIVERY:-clipboard}" = "cli" ]; then
    os_step "Sending prompt to $OS_AGENT_LABEL..."
    os_info "The agent will work autonomously — review the results when it finishes."
    os_agent_run "$PROMPT_FILE"
  else
    if os_copy_to_clipboard "$PROMPT_FILE"; then
      os_success "Prompt copied to clipboard!"
    else
      os_warn "Clipboard not available — copy manually:"
      os_info "  cat $PROMPT_FILE | clip"
    fi
    os_info "1. Paste in $OS_AGENT_LABEL"
    os_info "2. Let it complete the task"
    if [ -n "$WAIT_MESSAGE" ]; then
      os_info "3. $WAIT_MESSAGE"
      read -r _dummy
    fi
  fi
}

# ── Deliver a prompt and capture the agent's text response ───
# Usage: os_deliver_prompt_capture <prompt_file> <output_file>
# Used when the agent's reply itself is the artifact (os-enrich,
# os-review, os-create-ticket --hu).
#   - CLI agents: run and capture stdout automatically.
#   - Clipboard agents: copy the prompt, then read the pasted
#     response from the user (CTRL+D on Unix, CTRL+Z+Enter on
#     Windows) into output_file.
os_deliver_prompt_capture() {
  PROMPT_FILE="$1"
  OUTPUT_FILE="$2"

  if [ "${OS_AGENT_DELIVERY:-clipboard}" = "cli" ]; then
    os_step "Sending prompt to $OS_AGENT_LABEL..."
    os_agent_run "$PROMPT_FILE" "$OUTPUT_FILE"
  else
    if os_copy_to_clipboard "$PROMPT_FILE"; then
      os_success "Prompt copied to clipboard!"
    else
      os_warn "Clipboard not available — copy manually:"
      os_info "  cat $PROMPT_FILE | clip"
    fi
    os_info "1. Paste in $OS_AGENT_LABEL"
    os_info "2. Copy the AI output"
    os_info "3. Press Enter here when ready..."
    read -r _dummy
    os_step "Paste the response (CTRL+Z + Enter to finish on Windows, CTRL+D on Unix):"
    OUTPUT=""
    while IFS= read -r line; do
      OUTPUT="${OUTPUT}${line}
"
    done
    printf '%s' "$OUTPUT" > "$OUTPUT_FILE"
  fi
}

# ── Print agent summary ───────────────────────────────────────
os_print_agent() {
  os_info "Agent     : $OS_ACTIVE_AGENT ($OS_AGENT_LABEL)"
  os_info "Delivery  : $OS_AGENT_DELIVERY"
  [ "$OS_AGENT_COMMAND" != "null" ] && \
    os_info "Command   : $OS_AGENT_COMMAND $OS_AGENT_ARGS" || true
}
