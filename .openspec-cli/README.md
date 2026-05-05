# OpenSpec CLI

Command-line tools that connect Jira tickets to your AI agent (Copilot),
resolving the active stack from `openspec/config.yaml` automatically.

---

## How it works

```
Terminal                              Copilot Chat (VS Code)
─────────────────────────────         ──────────────────────────────
$ os-plan KAN-42
  ├─ Reads openspec/config.yaml       
  ├─ Resolves active stack            
  ├─ Fetches ticket from Jira API     
  ├─ Loads stack agent + standards    
  └─ Builds full prompt ──────────►  Paste → Copilot generates plan
                                      at ai-specs/changes/KAN-42_backend.md

$ os-develop KAN-42
  ├─ Creates branch feature/KAN-42-backend
  ├─ Loads existing plan              
  └─ Builds implementation prompt ──► Paste → Copilot implements step by step

$ os-commit KAN-42
  ├─ Stages relevant files
  ├─ Generates conventional commit message
  ├─ Commits + pushes
  └─ Opens PR via gh CLI  (no Copilot needed)

$ os-enrich KAN-42
  └─ Builds enrichment prompt ──────► Paste → Copilot enriches ticket
                                      Copy output back to Jira
```

---

## Installation

```bash
# From your project root
chmod +x .openspec-cli/install.sh
./.openspec-cli/install.sh

# Reload your shell
source ~/.zshrc   # or ~/.bashrc
```

### Dependencies

| Tool | Required | Purpose |
|---|---|---|
| `python3` | ✅ Yes | Parses `config.yaml` and Jira responses |
| `curl` | ✅ Yes | Jira API calls |
| `git` | ✅ Yes | Branch and commit operations |
| `gh` | ⚠ Recommended | PR creation (`os-commit`) |

---

## Setup

### 1. Environment variables

```bash
cp .env.example .env
# Edit .env and fill in your values
```

Required variables:

| Variable | Description |
|---|---|
| `JIRA_BASE_URL` | Your Jira instance, e.g. `https://your-org.atlassian.net` |
| `JIRA_EMAIL` | Your Jira account email |
| `JIRA_TOKEN` | Jira API token — generate at [Atlassian account settings](https://id.atlassian.com/manage-profile/security/api-tokens) |

### 2. GitHub CLI auth (for `os-commit`)

```bash
gh auth login
```

---

## Commands

### `os-plan <TICKET-ID>`

Generates a backend implementation plan for a Jira ticket.

```bash
os-plan KAN-42
```

**What it does:**
1. Reads the active stack from `openspec/config.yaml`
2. Fetches the ticket from Jira
3. Loads the stack agent + standards files
4. Builds a full Copilot prompt and copies it to the clipboard
5. Paste the prompt into Copilot Chat → it generates `ai-specs/changes/KAN-42_backend.md`

---

### `os-develop <TICKET-ID>`

Prepares the implementation context and creates the feature branch.

```bash
os-develop KAN-42
```

**What it does:**
1. Creates branch `feature/KAN-42-backend` (or switches to it if it exists)
2. Loads the existing plan from `ai-specs/changes/KAN-42_backend.md`
3. Builds an implementation prompt with full context and copies it to the clipboard
4. Paste into Copilot Chat → it implements the ticket step by step

> Run `os-plan` first to generate the plan before running `os-develop`.

---

### `os-commit [TICKET-ID]`

Commits changes, pushes, and opens a PR. No Copilot needed.

```bash
os-commit KAN-42
# or, if ticket ID is in the branch name already:
os-commit
```

**What it does:**
1. Detects changed files (skips `.env`, build artifacts)
2. Generates a conventional commit message
3. Shows a summary and asks for confirmation
4. Commits, pushes, and creates a PR via `gh pr create`

---

### `os-enrich <TICKET-ID>`

Enriches a Jira ticket with technical detail.

```bash
os-enrich KAN-42
```

**What it does:**
1. Fetches the ticket from Jira
2. Loads the stack agent, standards, API spec, and data model
3. Builds an enrichment prompt and copies it to the clipboard
4. Paste into Copilot Chat → it produces `[original]` and `[enhanced]` sections
5. Copy the output back to the Jira ticket description

---

## Switching stacks

Edit `openspec/config.yaml` and change the `stack:` value:

```yaml
stack: node-express   # was: java-spring
```

All commands will automatically use the new stack's agent, standards, and tooling commands.

---

## Prompt file

Every command saves the last generated prompt to:
```
.openspec-cli/.last-prompt.md
```

If the clipboard copy fails (Linux without `xclip`/`xsel`), open this file
and copy the content manually into Copilot Chat.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `openspec/config.yaml not found` | Run commands from inside the project repo |
| `Missing env var: JIRA_TOKEN` | Copy `.env.example` to `.env` and fill in values |
| `Failed to fetch ticket` | Verify `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` |
| Clipboard not working | Install `xclip` (Linux) or use `.last-prompt.md` |
| `gh: command not found` | Install GitHub CLI: https://cli.github.com |
| Stack agent not found | Check `openspec/config.yaml` `stacks.<stack>.agent` path |
