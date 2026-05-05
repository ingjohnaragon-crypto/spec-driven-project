#!/bin/sh
# .openspec-cli/lib/jira.sh
# Jira Cloud REST API v3 helpers.
# Requires: curl, py/python3

# ── Fetch a Jira ticket ──────────────────────────────────────
os_jira_fetch_ticket() {
  ticket_id="$1"
  os_step "Fetching ticket $ticket_id from Jira..."

  response=$(curl -s \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Accept: application/json" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id")

  if echo "$response" | grep -q "errorMessages"; then
    msg=$(echo "$response" | py -c \
      "import sys,json; d=json.load(sys.stdin); print(d['errorMessages'][0])" \
      2>/dev/null || echo "$response")
    os_error "Jira error: $msg"
    exit 1
  fi

  JIRA_TICKET_ID="$ticket_id"

  JIRA_SUMMARY=$(echo "$response" | py -c \
    "import sys,json; d=json.load(sys.stdin); print(d['fields']['summary'])" \
    2>/dev/null || echo "")

  JIRA_STATUS=$(echo "$response" | py -c \
    "import sys,json; d=json.load(sys.stdin); print(d['fields']['status']['name'])" \
    2>/dev/null || echo "")

  JIRA_TYPE=$(echo "$response" | py -c \
    "import sys,json; d=json.load(sys.stdin); print(d['fields']['issuetype']['name'])" \
    2>/dev/null || echo "")

  JIRA_ASSIGNEE=$(echo "$response" | py -c \
    "import sys,json; d=json.load(sys.stdin); a=d['fields'].get('assignee') or {}; print(a.get('displayName','Unassigned'))" \
    2>/dev/null || echo "Unassigned")

  JIRA_DESCRIPTION=$(echo "$response" | py -c \
"import sys,json
d=json.load(sys.stdin)
raw=d['fields'].get('description') or {}
def adf(n):
  if not n: return ''
  t=n.get('type','')
  if t=='text': return n.get('text','')
  if t=='hardBreak': return '\n'
  return ''.join(adf(c) for c in n.get('content',[]))+(('\n') if t in ('paragraph','heading','listItem','bulletList','orderedList') else '')
print(adf(raw).strip() or 'No description provided.')
" 2>/dev/null || echo "No description provided.")

  export JIRA_TICKET_ID JIRA_SUMMARY JIRA_STATUS JIRA_TYPE \
         JIRA_ASSIGNEE JIRA_DESCRIPTION

  os_success "Ticket: [$JIRA_STATUS] $JIRA_SUMMARY"
}

# ── Print ticket summary ─────────────────────────────────────
os_jira_print_ticket() {
  os_divider
  os_label "  Jira Ticket: $JIRA_TICKET_ID"
  os_divider
  os_info "Summary  : $JIRA_SUMMARY"
  os_info "Type     : $JIRA_TYPE"
  os_info "Status   : $JIRA_STATUS"
  os_info "Assignee : $JIRA_ASSIGNEE"
  os_divider
  if [ -n "$JIRA_DESCRIPTION" ] && [ "$JIRA_DESCRIPTION" != "No description provided." ]; then
    os_label "  Description:"
    echo "$JIRA_DESCRIPTION" | head -10
    os_divider
  fi
}

# ── Get valid transitions ────────────────────────────────────
os_jira_get_transitions() {
  ticket_id="$1"
  curl -s \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Accept: application/json" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id/transitions" \
  | py -c \
    "import sys,json; [print(t['id']+'|'+t['name']) for t in json.load(sys.stdin).get('transitions',[])]" \
    2>/dev/null
}

# ── Transition ticket to new status ─────────────────────────
os_jira_transition() {
  ticket_id="$1"
  transition_name="$2"

  os_step "Fetching transitions for $ticket_id..."
  transitions=$(os_jira_get_transitions "$ticket_id")

  transition_id=$(echo "$transitions" | grep -i "$transition_name" | head -1 | cut -d'|' -f1)

  if [ -z "$transition_id" ]; then
    os_warn "Transition '$transition_name' not found. Available transitions:"
    echo "$transitions" | sed 's/|/ -> /' | sed 's/^/  /'
    return 1
  fi

  result=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"transition\":{\"id\":\"$transition_id\"}}" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id/transitions")

  if [ "$result" = "204" ]; then
    os_success "Ticket $ticket_id moved to: $transition_name"
  else
    os_warn "Could not transition ticket (HTTP $result)"
  fi
}
