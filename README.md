# OpenSpec — Spec-Driven AI Development Platform

OpenSpec is a framework that connects your project management tool (Jira),
your codebase, and your AI agent (Copilot, Claude Code, Cursor, etc.) into
a single coherent workflow — driven by specs and standards, not by improvisation.

---

## The Problem

Modern development teams using AI assistants face a recurring gap: the AI knows
how to code, but it doesn't know *your* project. It doesn't know your architecture,
your conventions, your Jira tickets, or your stack. Every prompt has to re-explain
context that already exists somewhere — scattered across Jira, README files,
and tribal knowledge.

The result: AI output that's generic, inconsistent, and requires heavy review
and rework before it fits your codebase.

---

## The Solution

OpenSpec acts as the bridge. It stores your project's architectural decisions,
stack conventions, and quality standards as structured spec files. A lightweight
CLI reads those specs, fetches context from Jira, and builds a complete,
context-rich prompt — then delivers it to whatever AI agent your team uses.

```
Jira Ticket
    +
Project Specs (architecture, standards, conventions)
    +
Active Stack (Java, Python, Node, Go, Angular, React)
    +
Active AI Agent (Copilot, Claude Code, Cursor, Aider)
    ↓
One CLI command
    ↓
Context-rich prompt → AI generates plan / implementation / review
```

---

## Core Concepts

### Spec-Driven Development
All architectural decisions live in `ai-specs/specs/`. Agents read these
before generating any output. The AI always works within your conventions —
not against them.

### Multi-Stack Support
One repo can support multiple technology stacks. Switch between them with
`os-stack <name>`. The active stack determines which agent file, standards,
and tooling commands are loaded.

### Multi-Agent Support
Works with any AI agent. Switch between them with `os-agent <name>`.
Clipboard agents (Copilot, Cursor, Windsurf) copy prompts for manual paste.
CLI agents (Claude Code, Aider) send prompts automatically via terminal.

### Jira Integration
Every command that generates a prompt starts by fetching the real ticket
from Jira — title, description, status, assignee. No copy-pasting context.

---

## Supported Stacks

| Stack | Technologies |
|---|---|
| `java-spring` | Java 17, Spring Boot, Spring Data JPA, Flyway, JUnit 5 |
| `python-fastapi` | Python 3.12, FastAPI, SQLAlchemy, Alembic, pytest |
| `node-express` | Node.js 20, Express, TypeScript, Prisma, Jest |
| `go-gin` | Go 1.22, Gin, GORM, golang-migrate, testify |
| `frontend-react` | React 18, Vite, TypeScript, TanStack Query, Vitest |
| `frontend-angular` | Angular 17, TypeScript, NgRx, Jest |
| `vault-smart-contracts` | Thought Machine Vault, Contracts Language API 4.0, pytest |

---

## Supported AI Agents

| Agent | Delivery |
|---|---|
| GitHub Copilot | Clipboard — paste in VS Code chat |
| Cursor | Clipboard — paste in Cursor chat |
| Windsurf | Clipboard — paste in Windsurf chat |
| Claude Code | CLI — automatic via `claude` terminal command |
| Aider | CLI — automatic via `aider` terminal command |

---

## CLI Commands

### Workflow commands

| Command | What it does |
|---|---|
| `os-agent` | Switch active AI agent |
| `os-stack` | Switch active tech stack |
| `os-enrich` | Enrich a Jira ticket with technical detail |
| `os-enrich-apply` | Upload enriched content to Jira |
| `os-plan` | Generate an implementation plan from a Jira ticket |
| `os-develop` | Create feature branch + implementation prompt |
| `os-commit` | Commit, push and open PR |
| `os-review` | Generate a structured AI code review for a PR |
| `os-review-apply` | Publish the review to GitHub and apply verdict |

### Vault Smart Contract commands

| Command | What it does |
|---|---|
| `os-vault-lint` | Static analysis of `contracts/*.py` against Vault sandbox restrictions |
| `os-vault-test` | Run Vault contract tests (runs `os-vault-lint` first) |
| `os-vault-simulate` | Simulate a contract over a date range |
| `os-vault-deploy` | Deploy a contract as a new product version |
| `os-vault-account` | Open a Vault account for a product version |
| `os-vault-balances` | Fetch live balances for a Vault account |

---

## Project Structure

```
open-spec/
├── .openspec-cli/           # CLI commands and libraries
│   ├── commands/            # Executable commands (os-plan, os-commit, os-vault-*, etc.)
│   ├── lib/                 # Shared shell and Python helpers
│   │   ├── vault_lint.py    # Vault sandbox restriction linter (AST-based)
│   │   ├── colors.sh        # Terminal colour helpers
│   │   └── config.sh        # Stack + env config loader
│   └── install.sh           # Global installer
├── ai-specs/
│   ├── .agents/
│   │   └── stacks/          # Stack-specific agent files (role + conventions)
│   ├── .commands/           # Prompt templates for each workflow step
│   ├── changes/             # Generated implementation plans (per ticket)
│   └── specs/
│       ├── stacks/          # Stack-specific standards files
│       ├── base-standards.mdc
│       ├── api-spec.yml
│       ├── data-model.md
│       └── documentation-standards.mdc
├── contracts/               # Vault Smart Contract source files (*.py)
├── contracts_sdk/           # Thought Machine contracts_api SDK (local install)
├── openspec/
│   └── config.yaml          # Active stack, active agent, stack registry
├── src/                     # Application source code
├── tests/                   # Test suite
├── pytest.ini               # pytest config (testpaths, pythonpath)
├── .env.example             # Environment variable template
└── README.md                # This file
```

---

## Quick Start

```bash
# 1. Install the CLI
sh .openspec-cli/install.sh
source ~/.bashrc

# 2. Configure credentials
cp .env.example .env
# Edit .env: JIRA_BASE_URL, JIRA_EMAIL, JIRA_TOKEN
gh auth login

# 3. Select your stack and agent
os-stack --list
os-stack python-fastapi
os-agent --list
os-agent copilot

# 4. Start with a ticket
os-enrich KAN-6          # enrich ticket with technical detail
os-plan KAN-6            # generate implementation plan
os-develop KAN-6         # create branch + implementation
os-commit KAN-6          # commit + PR
os-review 1              # AI code review
os-review-apply 1        # publish review to GitHub
```

### Vault Smart Contracts quick start

```bash
# Switch to the Vault stack
os-stack vault-smart-contracts

# Install the local contracts_api SDK
cd contracts_sdk/contracts_sdk && pip install . && cd ../..

# Validate a contract against Vault sandbox restrictions
os-vault-lint contracts/savings_product.py

# Run tests (lint runs automatically first)
os-vault-test

# Run tests with coverage report
os-vault-test --coverage
```

See [`.openspec-cli/README.md`](.openspec-cli/README.md) for full command
documentation and troubleshooting.

---

## Vault Smart Contracts

When the `vault-smart-contracts` stack is active, OpenSpec manages Thought Machine
Vault contracts written in Python using the Contracts Language API 4.0.

### Sandbox restrictions

Vault executes contracts in a sandboxed Python environment. `os-vault-lint` performs
static analysis before any test runs and reports violations with file and line numbers:

```
contracts/foo.py:12 [FORBIDDEN_IMPORT] import 'os' is not allowed
contracts/foo.py:34 [FORBIDDEN_CALL] call to 'eval' is not allowed in contracts
```

| Rule | Trigger |
|------|---------|
| `FORBIDDEN_IMPORT` | Banned stdlib module (`os`, `sys`, `json`, `re`, `datetime`, …) |
| `UNKNOWN_IMPORT` | Any import not from `contracts_api` or `decimal` |
| `FORBIDDEN_CALL` | Bare call to `eval`, `exec`, `open`, `print`, `getattr`, `type`, … |
| `EXCEPTION_CHAINING` | `raise X from Y` |
| `MUTABLE_GLOBAL` | Module-level `list`/`dict`/`set` not in allowed contract metadata |

### Contract tooling commands

```bash
os-vault-lint                          # lint contracts/ (exit 0 = clean)
os-vault-test                          # lint then pytest
os-vault-test --coverage               # lint then pytest with HTML coverage
os-vault-simulate contracts/foo.py \
    "2024-01-01T00:00:00Z" \
    "2024-04-01T00:00:00Z" \
    '{"interest_rate": "0.05"}'        # simulate over a date range
os-vault-deploy contracts/foo.py \
    <product_id> "<Display Name>"      # deploy product version
os-vault-account <product_version_id> \
    <customer_id>                      # open account
os-vault-balances <account_id>         # fetch live balances
```

### CI integration

The GitHub Actions workflow runs three steps in order for every push:

1. **Run Vault lint** — `python .openspec-cli/lib/vault_lint.py contracts/`
2. **Run vault_lint unit tests** — `pytest tests/test_vault_lint.py --cov=vault_lint --cov-fail-under=90`
3. **Run Vault Smart Contract tests** — `pytest tests/test_savings_product.py --cov=contracts --cov-fail-under=90`

---

## Architecture Principles

OpenSpec enforces these principles across all stacks:

- **Domain-Driven Design (DDD)** — Domain, Application, Presentation layers
- **Test-Driven Development (TDD)** — tests before implementation, always
- **90% coverage threshold** — enforced per stack
- **English only** — all code, comments, docs, and commits
- **Conventional commits** — `feat`, `fix`, `test`, `docs`, `chore`
- **No secrets in code** — environment variables only

---

## Contributing

1. Pick a ticket from Jira
2. Run `os-enrich <TICKET-ID>` to add technical detail
3. Run `os-plan <TICKET-ID>` to generate the implementation plan
4. Run `os-develop <TICKET-ID>` to implement
5. Run `os-commit <TICKET-ID>` to open a PR
6. Request review — `os-review <PR>` generates an AI code review

---

## License

ISC
