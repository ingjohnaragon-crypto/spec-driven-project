#!/bin/sh
# .openspec-cli/lib/jira.sh
# Jira Cloud REST API v3 helpers.
# Requires: curl, python3

# ── Fetch a Jira ticket ──────────────────────────────────────
# Usage: os_jira_fetch_ticket KAN-42
# Sets: JIRA_TICKET_ID, JIRA_SUMMARY, JIRA_DESCRIPTION,
#       JIRA_STATUS, JIRA_TYPE, JIRA_ASSIGNEE
os_jira_fetch_ticket() {
  ticket_id="$1"
  os_step "Fetching ticket $ticket_id from Jira..."

  response=$(curl -s \
    --fail-with-body \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Accept: application/json" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id" 2>&1)

  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    os_error "Failed to fetch ticket $ticket_id"
    os_error "Response: $response"
    os_info  "Check JIRA_BASE_URL, JIRA_EMAIL and JIRA_TOKEN in your .env"
    exit 1
  fi

  # Parse fields with python3
  parsed=$(python3 - "$response" << 'PYEOF'
import sys, json

raw = sys.argv[1]
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"PARSE_ERROR|{e}")
    sys.exit(1)

fields = data.get("fields", {})

summary     = fields.get("summary", "")
status      = fields.get("status", {}).get("name", "")
issue_type  = fields.get("issuetype", {}).get("name", "")
assignee    = (fields.get("assignee") or {}).get("displayName", "Unassigned")

# Flatten Atlassian Document Format description to plain text
def adf_to_text(node):
    if not node:
        return ""
    if isinstance(node, str):
        return node
    text = ""
    node_type = node.get("type", "")
    if node_type == "text":
        text += node.get("text", "")
    elif node_type == "hardBreak":
        text += "\n"
    elif node_type in ("paragraph", "heading", "bulletList",
                       "orderedList", "listItem", "blockquote"):
        for child in node.get("content", []):
            text += adf_to_text(child)
        text += "\n"
    else:
        for child in node.get("content", []):
            text += adf_to_text(child)
    return text

description_raw = fields.get("description", {})
description = adf_to_text(description_raw).strip() if description_raw else "No description provided."

# Escape pipe characters used as delimiter
def esc(s):
    return str(s).replace("|", "¦").replace("\n", "\\n")

print(f"{esc(summary)}|{esc(status)}|{esc(issue_type)}|{esc(assignee)}|{esc(description)}")
PYEOF
)

  if echo "$parsed" | grep -q "^PARSE_ERROR"; then
    os_error "Could not parse Jira response: $parsed"
    exit 1
  fi

  JIRA_TICKET_ID="$ticket_id"
  JIRA_SUMMARY=$(echo "$parsed"     | cut -d'|' -f1 | sed 's/\\n/\n/g')
  JIRA_STATUS=$(echo "$parsed"      | cut -d'|' -f2)
  JIRA_TYPE=$(echo "$parsed"        | cut -d'|' -f3)
  JIRA_ASSIGNEE=$(echo "$parsed"    | cut -d'|' -f4)
  JIRA_DESCRIPTION=$(echo "$parsed" | cut -d'|' -f5 | sed 's/\\n/\n/g')

  export JIRA_TICKET_ID JIRA_SUMMARY JIRA_STATUS JIRA_TYPE JIRA_ASSIGNEE JIRA_DESCRIPTION

  os_success "Ticket fetched: [$JIRA_STATUS] $JIRA_SUMMARY"
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
  os_label "  Description:"
  echo "$JIRA_DESCRIPTION" | head -20
  if [ "$(echo "$JIRA_DESCRIPTION" | wc -l)" -gt 20 ]; then
    os_info "... (truncated — full description included in prompt)"
  fi
  os_divider
}

# ── Update ticket description in Jira ───────────────────────
# Usage: os_jira_update_description KAN-42 "new content"
os_jira_update_description() {
  ticket_id="$1"
  new_content="$2"

  body=$(python3 - "$new_content" << 'PYEOF'
import sys, json

text = sys.argv[1]
# Wrap in ADF paragraph nodes
paragraphs = []
for line in text.split('\n'):
    line = line.strip()
    if line:
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": line}]
        })

doc = {
    "fields": {
        "description": {
            "type": "doc",
            "version": 1,
            "content": paragraphs if paragraphs else [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            ]
        }
    }
}
print(json.dumps(doc))
PYEOF
)

  response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -d "$body" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id")

  if [ "$response" = "204" ]; then
    os_success "Ticket $ticket_id updated in Jira"
  else
    os_error "Failed to update ticket $ticket_id (HTTP $response)"
  fi
}

# ── Get valid transitions for a ticket ──────────────────────
os_jira_get_transitions() {
  ticket_id="$1"
  curl -s \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Accept: application/json" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id/transitions" \
  | python3 - << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())
for t in data.get("transitions", []):
    print(f"{t['id']}|{t['name']}")
PYEOF
}

# ── Transition a ticket to a new status ─────────────────────
os_jira_transition() {
  ticket_id="$1"
  transition_id="$2"

  curl -s -o /dev/null -w "%{http_code}" \
    -X POST \
    -u "$JIRA_EMAIL:$JIRA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"transition\":{\"id\":\"$transition_id\"}}" \
    "$JIRA_BASE_URL/rest/api/3/issue/$ticket_id/transitions"
}
