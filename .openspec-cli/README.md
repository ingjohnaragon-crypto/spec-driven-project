# OpenSpec CLI

Command-line tools that connect **Jira**, your **repository specs**, and **multiple AI agents**
in a unified spec-driven workflow for **Thought Machine Vault Smart Contracts**. Every `os-*`
command resolves the active **stack**, **agent**, and **language** from `openspec/config.yaml`
before building or delivering a prompt.

---

## Multi-agent model

OpenSpec separates three independent choices:

| Dimension | Command | What it controls |
|---|---|---|
| **Stack** | `os-stack <name>` | Tech context: agent role file, standards, lint/test/coverage commands |
| **Agent** | `os-agent <name>` | How prompts are delivered: clipboard vs CLI |
| **Language** | `os-language <code>` | Output language for plans, Jira, commits, PRs (`en` / `es`) |

### Supported agents

| Agent | Delivery | You do | Best for |
|---|---|---|---|
| `cursor` | Clipboard | Paste `.openspec-cli/.last-prompt.md` into Cursor | Interactive editing in IDE |
| `copilot` | Clipboard | Paste into VS Code Copilot Chat | GitHub Copilot users |
| `windsurf` | Clipboard | Paste into Windsurf | Windsurf users |
| `claude-code` | CLI | Prompt runs automatically in terminal | Fully autonomous implement + review-fix |
| `aider` | CLI | Prompt runs automatically in terminal | Terminal-first workflows |

**Clipboard agents** — `os-plan`, `os-enrich`, `os-review` copy the prompt; you paste it,
then save the AI output to the working files under `.openspec-cli/`.

**CLI agents** — `os-develop` and `os-review-fix` run autonomously (code changes in the repo).

### Stack

| Stack | Use case |
|---|---|
| `vault-smart-contracts` | Thought Machine Vault API 4.0 — the only shipped stack |

`config.yaml` keeps the registry shape so another stack could be added later.
The Vault stack uses `plan-vault-contract.md`, `develop-vault-contract.md`, and
`review-vault-pr.md` as its prompt templates.

---

## Installation

```bash
sh .openspec-cli/install.sh
source ~/.bashrc    # or ~/.zshrc
```

Re-run after pulling CLI updates to refresh `~/.openspec/lib`.

### Dependencies

| Tool | Required | Purpose |
|---|---|---|
| `python3` / `py` | Yes | Config parsing, Jira API, vault lint |
| `curl` | Yes | Jira + Vault HTTP |
| `git` | Yes | Branches and commits |
| `gh` | Recommended | PR creation and review publish |
| `contracts_api` | Vault only | `cd contracts_sdk/contracts_sdk && pip install .` |

---

## Setup

```bash
cp .env.example .env
# JIRA_BASE_URL, JIRA_EMAIL, JIRA_TOKEN, JIRA_PROJECT_KEY
# VAULT_* optional — for os-vault-simulate/deploy/account
gh auth login
os-stack --list && os-stack vault-smart-contracts
os-agent --list && os-agent cursor        # or claude-code
os-language --list && os-language es      # optional
```

---

## Complete workflow

### Clipboard agent (Cursor / Copilot / Windsurf)

```bash
os-enrich KAN-XX
# → paste AI output into ai-specs/changes/enriquecimientos/KAN-XX/ or .enriched-content.md
os-enrich-apply KAN-XX

os-plan KAN-XX
# → AI saves plan to ai-specs/changes/planes/KAN-XX/KAN-XX_backend.md

os-develop KAN-XX
# → creates feature/KAN-XX-backend; paste prompt if clipboard agent

os-vault-test --coverage                  # Vault stack
os-commit KAN-XX

os-review 20
os-review-apply 20
```

### CLI agent (Claude Code / Aider)

```bash
os-agent claude-code
os-plan KAN-XX          # prompt delivered automatically
os-develop KAN-XX       # implementation runs in terminal
os-vault-test --coverage
os-commit KAN-XX
os-review 20 && os-review-apply 20
os-review-fix 20        # auto-fix REQUEST CHANGES + re-review
```

---

## Commands reference

### Configuration

```bash
os-stack [--list | <stack>]
os-agent [--list | <agent>]
os-language [--list | en|es]
```

### Jira

```bash
os-tickets [status] [--project KEY]
os-create-ticket [--hu] [--project KEY] [summary] [type]
os-transition <TICKET> [--list | <state>]
os-enrich <TICKET>
os-enrich-apply <TICKET> [file]
```

### Development workflow

```bash
os-plan <TICKET>              # plan prompt → planes/<TICKET>/
os-develop <TICKET>           # branch + implement
os-commit [TICKET]            # commit + PR → develop
os-review <PR>                # review → .review-output.md
os-review-apply <PR> [file]   # publish to GitHub
os-review-fix <PR>            # fix loop (CLI agents)
```

### Vault Smart Contracts

```bash
os-vault-lint [file|dir]
os-vault-test [file] [--coverage]
os-vault-simulate contracts/<product>.py [start] [end] ['{"param":"val"}']
os-vault-deploy contracts/<product>.py <product_id> "<display name>"
os-vault-account <product_version_id> <customer_id> [denomination]
os-vault-balances <account_id>
```

---

## Working files

| File | Purpose |
|---|---|
| `.openspec-cli/.last-prompt.md` | Last prompt built (all commands) |
| `.openspec-cli/.enriched-content.md` | Fallback before `os-enrich-apply` |
| `.openspec-cli/.review-output.md` | Review before `os-review-apply` |
| `ai-specs/changes/planes/<TICKET>/` | Implementation plans |
| `ai-specs/changes/enriquecimientos/<TICKET>/` | Enriched tickets |

GitHub is the archive for reviews and PRs — not local `ai-specs/changes/` review files.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `command not found` | `source ~/.bashrc` or add `~/.openspec/bin` to PATH |
| Outdated install banner | Re-run `sh .openspec-cli/install.sh` |
| Stack standards empty | Check `openspec/config.yaml` standards path exists |
| Clipboard on Windows | `cat .openspec-cli/.last-prompt.md \| clip` |
| `os-vault-test` fails | Install SDK: `pip install contracts_sdk/contracts_sdk/.` |
| Agent CLI not found | Switch to clipboard: `os-agent cursor` |

---

## File reference

```
.openspec-cli/
├── install.sh              Canonical installer (run this)
├── README.md               This file
├── lib/
│   ├── agent.sh            Prompt delivery (clipboard / CLI / capture)
│   ├── config.sh           Stack + template resolution
│   ├── language.sh         Active language
│   ├── jira.sh             Jira REST helpers
│   ├── vault_lint.py       Sandbox AST linter
│   └── parse_*.py          YAML parsers
└── commands/
    ├── os-stack / os-agent / os-language
    ├── os-enrich / os-enrich-apply
    ├── os-plan / os-develop / os-commit
    ├── os-review / os-review-apply / os-review-fix
    ├── os-tickets / os-create-ticket / os-transition
    └── os-vault-lint / os-vault-test / os-vault-simulate / …
```
