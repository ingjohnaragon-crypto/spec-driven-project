# OpenSpec CLI

Command-line tools that connect Jira tickets to your AI agent (Copilot),
resolving the active stack from `openspec/config.yaml` automatically.

---

## Installation

```bash
sh .openspec-cli/install.sh
source ~/.bashrc
```

### Dependencies

| Tool | Required | Purpose |
|---|---|---|
| `python3` / `py` | Yes | YAML parsing and Jira API calls |
| `curl` | Yes | HTTP requests to Jira |
| `git` | Yes | Branch and commit operations |
| `gh` | Recommended | PR creation (`os-commit`) |

---

## Setup

```bash
cp .env.example .env
# Edit .env with your Jira credentials
gh auth login
```

`.env` file:
```
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_TOKEN=your_jira_api_token
```

---

## Complete workflow

```bash
# 1. Switch to the right stack for your project
os-stack --list
os-stack python-fastapi

# 2. Enrich the Jira ticket with technical detail
os-enrich KAN-6
cat .openspec-cli/.last-prompt.md | clip   # Windows
# Paste into Copilot Chat → copy Copilot output

# 3. Save Copilot output and upload to Jira
notepad .openspec-cli/.enriched-content.md  # paste Copilot output here
os-enrich-apply KAN-6                        # uploads to Jira automatically

# 4. Generate implementation plan
os-plan KAN-6
cat .openspec-cli/.last-prompt.md | clip
# Paste into Copilot Chat → generates ai-specs/changes/KAN-6_backend.md

# 5. Implement
os-develop KAN-6
cat .openspec-cli/.last-prompt.md | clip
# Paste into Copilot Chat → implements step by step

# 6. Commit and open PR
os-commit KAN-6
```

---

## Commands

### `os-stack [--list | <stack-name>]`

Lists available stacks or switches the active stack.

```bash
os-stack --list          # show all stacks
os-stack python-fastapi  # switch to Python/FastAPI
os-stack java-spring     # switch to Java/Spring Boot
os-stack node-express    # switch to Node.js/Express
os-stack go-gin          # switch to Go/Gin
os-stack frontend-react  # switch to React
os-stack frontend-angular # switch to Angular
```

### `os-plan <TICKET-ID>`

Fetches Jira ticket + resolves stack → builds Copilot prompt for implementation plan.

```bash
os-plan KAN-6
cat .openspec-cli/.last-prompt.md | clip   # Windows clipboard
```

### `os-develop <TICKET-ID>`

Creates feature branch + builds Copilot implementation prompt.

```bash
os-develop KAN-6
```

### `os-enrich <TICKET-ID>`

Builds Copilot prompt to enrich the Jira ticket with technical detail.

```bash
os-enrich KAN-6
cat .openspec-cli/.last-prompt.md | clip
```

### `os-enrich-apply <TICKET-ID> [file]`

Uploads enriched content to Jira ticket description.

```bash
# Save Copilot output to .enriched-content.md first
notepad .openspec-cli/.enriched-content.md

# Then upload
os-enrich-apply KAN-6

# Or specify a custom file
os-enrich-apply KAN-6 my-content.md
```

### `os-commit [TICKET-ID]`

Stages changes, generates conventional commit, pushes and opens PR.

```bash
os-commit KAN-6
os-commit        # ticket ID inferred from branch name
```

---

## Switching stacks

One command changes everything — agent, standards, and tooling commands:

| Stack | Label | Test command |
|---|---|---|
| `java-spring` | Java 17 + Spring Boot | `./gradlew test` |
| `python-fastapi` | Python 3.12 + FastAPI | `pytest` |
| `node-express` | Node.js + Express | `npm test` |
| `go-gin` | Go + Gin | `go test ./...` |
| `frontend-react` | React + Vite | `npm test` |
| `frontend-angular` | Angular | `ng test` |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `command not found` | Run `source ~/.bashrc` or add `~/.openspec/bin` to PATH |
| `openspec/config.yaml not found` | Run from inside the project repo |
| `.env not found` | Run `cp .env.example .env` and fill in values |
| Jira 404 error | Check ticket ID exists: `os-plan KAN-1` |
| Clipboard not working | Use `cat .openspec-cli/.last-prompt.md \| clip` (Windows) |
| Stack fields show wrong stack | Run `sh .openspec-cli/install.sh` to reinstall |

---

## File reference

```
.openspec-cli/
├── install.sh                  Install/update the CLI
├── README.md                   This file
├── .last-prompt.md             Last generated prompt (auto-updated)
├── .enriched-content.md        Paste Copilot enrichment output here
├── lib/
│   ├── colors.sh               Terminal color helpers
│   ├── config.sh               Reads openspec/config.yaml
│   ├── jira.sh                 Jira API helpers
│   └── parse_config.py         Python YAML parser for config.yaml
└── commands/
    ├── os-stack                Switch active stack
    ├── os-plan                 Generate plan prompt
    ├── os-develop              Create branch + implementation prompt
    ├── os-enrich               Generate enrichment prompt
    ├── os-enrich-apply         Upload enriched content to Jira
    └── os-commit               Commit, push, open PR
```
