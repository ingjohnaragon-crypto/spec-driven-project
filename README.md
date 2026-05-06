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

---

## Project Structure

```
open-spec/
├── .openspec-cli/           # CLI commands and libraries
│   ├── commands/            # Executable commands (os-plan, os-commit, etc.)
│   ├── lib/                 # Shared shell and Python helpers
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
├── openspec/
│   └── config.yaml          # Active stack, active agent, stack registry
├── src/                     # Application source code
├── tests/                   # Test suite
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

See [`.openspec-cli/README.md`](.openspec-cli/README.md) for full command
documentation and troubleshooting.

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
