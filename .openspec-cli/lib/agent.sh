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

# ── Deliver prompt to the active agent ───────────────────────
# Usage: os_deliver_prompt <prompt_file> [next_step_hint]
os_deliver_prompt() {
  PROMPT_FILE="$1"
  NEXT_HINT="${2:-}"

  if [ ! -f "$PROMPT_FILE" ]; then
    os_error "Prompt file not found: $PROMPT_FILE"
    exit 1
  fi

  case "$OS_AGENT_DELIVERY" in

    # ── Clipboard delivery (Copilot, Cursor, Windsurf) ──────
    clipboard)
      CLIPBOARD_OK=0

      if command -v clip.exe > /dev/null 2>&1; then
        cat "$PROMPT_FILE" | clip.exe && CLIPBOARD_OK=1
      elif command -v pbcopy > /dev/null 2>&1; then
        cat "$PROMPT_FILE" | pbcopy && CLIPBOARD_OK=1
      elif command -v xclip > /dev/null 2>&1; then
        cat "$PROMPT_FILE" | xclip -selection clipboard && CLIPBOARD_OK=1
      elif command -v xsel > /dev/null 2>&1; then
        cat "$PROMPT_FILE" | xsel --clipboard --input && CLIPBOARD_OK=1
      fi

      os_divider
      if [ "$CLIPBOARD_OK" = "1" ]; then
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

    # ── CLI delivery (Claude Code, Aider) ───────────────────
    cli)
      if [ "$OS_AGENT_COMMAND" = "null" ] || [ -z "$OS_AGENT_COMMAND" ]; then
        os_error "No CLI command configured for agent: $OS_ACTIVE_AGENT"
        exit 1
      fi

      if ! command -v "$OS_AGENT_COMMAND" > /dev/null 2>&1; then
        os_error "Agent command not found: $OS_AGENT_COMMAND"
        os_info  "Install $OS_AGENT_LABEL or switch agent: os-agent copilot"
        exit 1
      fi

      PROMPT_CONTENT=$(cat "$PROMPT_FILE")

      os_divider
      os_step "Sending prompt to $OS_AGENT_LABEL..."
      os_divider

      case "$OS_ACTIVE_AGENT" in
        claude-code)
          # Claude Code: pipe prompt via stdin with --print for non-interactive
          cat "$PROMPT_FILE" | "$OS_AGENT_COMMAND" $OS_AGENT_ARGS
          ;;
        aider)
          # Aider: pass prompt as --message argument
          "$OS_AGENT_COMMAND" $OS_AGENT_ARGS "$PROMPT_CONTENT"
          ;;
        *)
          # Generic: pipe via stdin
          cat "$PROMPT_FILE" | "$OS_AGENT_COMMAND" $OS_AGENT_ARGS
          ;;
      esac

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

# ── Print agent summary ───────────────────────────────────────
os_print_agent() {
  os_info "Agent     : $OS_ACTIVE_AGENT ($OS_AGENT_LABEL)"
  os_info "Delivery  : $OS_AGENT_DELIVERY"
  [ "$OS_AGENT_COMMAND" != "null" ] && \
    os_info "Command   : $OS_AGENT_COMMAND $OS_AGENT_ARGS" || true
}
