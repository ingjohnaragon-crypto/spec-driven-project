# OpenSpec CLI

Command-line tools that connect Jira tickets to your AI agent, resolving
the active stack and AI agent automatically from `openspec/config.yaml`.

---

## Installation

```bash
sh .openspec-cli/install.sh
source ~/.bashrc
```

### Dependencies

| Tool | Required | Purpose |
|---|---|---|
| `python3` / `py` | Yes | YAML parsing, Jira API, config resolution |
| `curl` | Yes | HTTP requests to Jira |
| `git` | Yes | Branch and commit operations |
| `gh` | Recommended | PR creation and review (`os-commit`, `os-review-apply`) |

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
# 1. Select your AI agent and stack
os-agent --list
os-agent copilot          # or claude-code, cursor, windsurf, aider
os-stack --list
os-stack python-fastapi

# 2. Enrich the Jira ticket with technical detail
os-enrich KAN-6
cat .openspec-cli/.last-prompt.md | clip   # Windows
# Paste into your AI agent → copy output

# 3. Save output and upload to Jira
notepad .openspec-cli/.enriched-content.md  # paste AI output here
os-enrich-apply KAN-6                        # uploads to Jira automatically

# 4. Generate implementation plan
os-plan KAN-6
# Prompt is delivered automatically to your active agent
# → AI generates ai-specs/changes/planes/KAN-6/KAN-6_backend.md

# 5. Implement
os-develop KAN-6
# → AI implements step by step on branch feature/KAN-6-backend

# 6. Commit and open PR
os-commit KAN-6

# 7. Review the PR
os-review 1
notepad .openspec-cli/.review-output.md     # paste AI review output here
os-review-apply 1                            # publishes review to GitHub
```

---

## Commands

### `os-agent [--list | <agent-name>]`

Lists available AI agents or switches the active agent.

```bash
os-agent --list          # show all agents with delivery method
os-agent copilot         # clipboard delivery (paste manually in VS Code)
os-agent cursor          # clipboard delivery (paste manually in Cursor)
os-agent windsurf        # clipboard delivery (paste manually in Windsurf)
os-agent claude-code     # CLI delivery (sends prompt directly via terminal)
os-agent aider           # CLI delivery (sends prompt directly via terminal)
```

### `os-stack [--list | <stack-name>]`

Lists available stacks or switches the active stack.

```bash
os-stack --list           # show all stacks
os-stack python-fastapi   # switch to Python/FastAPI
os-stack java-spring      # switch to Java/Spring Boot
os-stack node-express     # switch to Node.js/Express
os-stack go-gin           # switch to Go/Gin
os-stack frontend-react   # switch to React + Vite
os-stack frontend-angular # switch to Angular
os-stack vault-smart-contracts
```

### `os-language [--list | <language-code>]`

Switches the output language for plans, enrichments, reviews, commits and PRs.

```bash
os-language --list
os-language en
os-language es
```

### `os-plan <TICKET-ID>`

Fetches Jira ticket, resolves active stack + agent, delivers implementation
plan prompt to the configured agent.

```bash
os-plan KAN-6
# Clipboard agents: cat .openspec-cli/.last-prompt.md | clip
# CLI agents: prompt is sent automatically
```

### `os-develop <TICKET-ID>`

Creates the feature branch and delivers the implementation prompt.

```bash
os-develop KAN-6
# Creates branch: feature/KAN-6-backend
```

### `os-enrich <TICKET-ID>`

Builds a prompt to enrich the Jira ticket with technical detail.

```bash
os-enrich KAN-6
```

### `os-enrich-apply <TICKET-ID> [file]`

Uploads enriched content to Jira ticket description.

```bash
notepad .openspec-cli/.enriched-content.md  # paste AI output here
os-enrich-apply KAN-6
os-enrich-apply KAN-6 my-content.md         # or specify a custom file
```

### `os-review <PR-NUMBER>`

Downloads the PR diff and builds a structured code review prompt.

```bash
os-review 1
notepad .openspec-cli/.review-output.md     # paste AI review output here
```

### `os-review-apply <PR-NUMBER> [file]`

Publishes the AI review as a GitHub PR comment and applies verdict
(approve / request changes).

```bash
os-review-apply 1
os-review-apply 1 my-review.md             # or specify a custom file
```

### `os-commit [TICKET-ID]`

Stages relevant changes, generates a conventional commit message,
pushes and opens a PR via GitHub CLI.

```bash
os-commit KAN-6
os-commit        # ticket ID inferred from branch name
```

---

## Switching stacks

One command changes everything — agent file, standards, and tooling commands:

| Stack | Label | Test command |
|---|---|---|
| `java-spring` | Java 17 + Spring Boot | `./gradlew test` |
| `python-fastapi` | Python 3.12 + FastAPI | `pytest` |
| `node-express` | Node.js + Express | `npm test` |
| `go-gin` | Go + Gin | `go test ./...` |
| `frontend-react` | React + Vite | `npm test` |
| `frontend-angular` | Angular | `ng test --watch=false` |

## Switching AI agents

| Agent | Delivery | Requires |
|---|---|---|
| `copilot` | Clipboard — paste manually | GitHub Copilot in VS Code |
| `cursor` | Clipboard — paste manually | Cursor editor |
| `windsurf` | Clipboard — paste manually | Windsurf editor |
| `claude-code` | CLI — automatic | `claude` CLI installed |
| `aider` | CLI — automatic | `aider` installed |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `command not found` | Run `source ~/.bashrc` or add `~/.openspec/bin` to PATH |
| `openspec/config.yaml not found` | Run commands from inside the project repo |
| `.env not found` | Run `cp .env.example .env` and fill in values |
| Jira 404 error | Verify ticket exists: run with a known ticket ID |
| Clipboard not working (Windows) | Use `cat .openspec-cli/.last-prompt.md \| clip` |
| Stack fields show wrong stack | Run `sh .openspec-cli/install.sh` to reinstall |
| Agent command not found | Install the CLI tool or switch to `copilot`: `os-agent copilot` |
| Python not found | Install Python 3 and ensure `py`, `python3` or `python` is in PATH |

---

## File reference

```
.openspec-cli/
├── install.sh                   Install/update the CLI globally
├── README.md                    This file
├── .last-prompt.md              Last generated prompt (auto-updated by every command)
├── .enriched-content.md         Paste AI enrichment output here before os-enrich-apply
├── .review-output.md            Paste AI review output here before os-review-apply
├── lib/
│   ├── colors.sh                Terminal color and print helpers
│   ├── config.sh                Reads and resolves openspec/config.yaml
│   ├── agent.sh                 Resolves active AI agent and delivers prompts
│   │                            (os_deliver_prompt / autonomous / capture)
│   ├── language.sh              Resolves active output language
│   ├── jira.sh                  Jira Cloud REST API v3 helpers
│   ├── parse_config.py          Python YAML parser for stack fields
│   ├── parse_agent.py           Python YAML parser for agent fields
│   ├── parse_language.py        Python YAML parser for language fields
│   └── parse_stack.py           Python parser for active stack name
└── commands/
    ├── os-agent                 Switch active AI agent
    ├── os-stack                 Switch active tech stack
    ├── os-language              Switch active output language
    ├── os-plan                  Generate implementation plan prompt
    ├── os-develop               Create branch + implementation prompt
    ├── os-enrich                Generate ticket enrichment prompt
    ├── os-enrich-apply          Upload enriched content to Jira
    ├── os-review                Generate PR code review prompt
    ├── os-review-apply          Publish review to GitHub PR
    └── os-commit                Commit, push and open PR
```
