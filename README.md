# OpenSpec — Spec-Driven Framework for Vault Smart Contracts

OpenSpec connects your project management tool (Jira), your codebase, and your
AI agent (Copilot, Claude Code, Cursor, …) into a single spec-driven workflow
for building **Thought Machine Vault Smart Contracts**.

Built by John Aragón as the MVP for the **Accelerathon GFT × Thought Machine**.

---

## The Problem

An AI assistant knows how to write Python, but it doesn't know that Vault runs a
**restricted Python sandbox** — no stdlib, no `print`, `Decimal` only for money,
`ZoneInfo` not `timezone.utc`, `Rejection` not `raise`, `update_permission` required
on every instance parameter. Every prompt has to re-explain the Contracts Language
API 4.0, the sandbox rules, and the deploy schema of the shared labs environment.

The result: contract code that lints clean as Python but is rejected at load time
or at deploy time.

---

## The Solution

OpenSpec stores the Vault stack's rules — API 4.0 gotchas, sandbox restrictions,
Core API deploy schema, project conventions — as structured spec files. A
lightweight CLI reads those specs, fetches the ticket from Jira, and builds a
complete, context-rich prompt, then delivers it to whatever AI agent your team uses.

```
Jira Ticket
    +
Vault specs (sandbox rules, API 4.0 changes, Core API deploy findings)
    +
Active AI Agent (Copilot, Claude Code, Cursor, Aider)
    ↓
One CLI command
    ↓
Context-rich prompt → AI generates plan / contract / review
    ↓
os-vault-lint (8 enforced rules) + pytest ≥ 90% coverage
```

---

## Core Concepts

### Spec-Driven Development
The Vault stack's knowledge lives in `ai-specs/`:
`.agents/stacks/vault-smart-contracts.md` (role + API 4.0 rules),
`specs/stacks/vault-smart-contracts-standards.mdc` (enforced standards), and
`specs/stacks/vault-core-api-gotchas.md` (Core API deploy/account/balances findings).
Agents read these before generating any output.

### Enforced sandbox linting
`os-vault-lint` runs AST static analysis on `contracts/*.py` before any test and
fails the build on a sandbox violation — see [Sandbox restrictions](#sandbox-restrictions).

### Multi-Agent Support
Switch agents with `os-agent <name>`. Clipboard agents (Copilot, Cursor, Windsurf)
copy the prompt for manual paste; CLI agents (Claude Code, Aider) run it directly.

### Jira Integration
Every command that generates a prompt starts by fetching the real ticket from Jira —
title, description, status, assignee. No copy-pasting context.

### Single stack, extensible shape
`openspec/config.yaml` keeps a stack registry so another stack could be added later,
but this repo ships only `vault-smart-contracts`.

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

### Configuration

| Command | What it does |
|---|---|
| `os-stack [--list\|<name>]` | List or switch active stack (only `vault-smart-contracts` today) |
| `os-agent [--list\|<name>]` | List or switch active AI agent |
| `os-language [--list\|<code>]` | Output language for plans, Jira, commits and PRs |

### Jira

| Command | What it does |
|---|---|
| `os-tickets [status]` | List all project tickets, optionally filtered by status |
| `os-create-ticket --hu` | Create a ticket with an AI-generated user story |
| `os-create-ticket "<title>" <type>` | Create a ticket quickly (Task, Bug, Story…) |
| `os-enrich <KAN-XX>` | Enrich a ticket with technical detail |
| `os-enrich-apply <KAN-XX>` | Upload enriched content to Jira |
| `os-transition <KAN-XX> [--list\|<state>]` | List transitions or move ticket to a state |

### Development workflow

| Command | What it does |
|---|---|
| `os-plan <KAN-XX>` | Generate an implementation plan from a Jira ticket |
| `os-develop <KAN-XX>` | Create feature branch + implementation prompt |
| `os-commit <KAN-XX>` | Commit, push and open PR → develop (never straight to develop/main) |
| `os-review <PR>` | Generate a structured AI code review for a PR |
| `os-review-apply <PR>` | Publish the review to GitHub and apply verdict |
| `os-review-fix <PR>` | Auto-fix REQUEST CHANGES feedback, re-review and re-publish |

### Vault Smart Contract commands

| Command | What it does |
|---|---|
| `os-vault-lint` | AST static analysis of `contracts/*.py` against the Vault sandbox |
| `os-vault-test [--coverage]` | Run contract tests (runs `os-vault-lint` first) |
| `os-vault-simulate` | Simulate a contract over a date range (streaming NDJSON) |
| `os-vault-deploy` | Deploy a contract as a new product version |
| `os-vault-account` | Open a Vault account for a product version |
| `os-vault-balances` | Fetch live balances for a Vault account |
| `os-vault-customer` | Create a customer in the sandbox |
| `os-vault-products` | List product versions (`--mine` by default in the shared sandbox) |
| `os-vault-posting` | Send a posting instruction batch |

---

## Project Structure

```
open-spec/
├── .openspec-cli/           # CLI commands and libraries
│   ├── commands/            # Executable commands (os-plan, os-commit, os-vault-*, …)
│   ├── lib/                 # Shared shell and Python helpers
│   │   ├── vault_lint.py    # Vault sandbox restriction linter (AST-based)
│   │   ├── config.sh        # Stack + env config loader
│   │   └── vault_*.py       # Core API payload builders / result printers
│   └── install.sh           # Global installer
├── ai-specs/
│   ├── .agents/stacks/
│   │   └── vault-smart-contracts.md      # Agent: role + API 4.0 rules
│   ├── .commands/                        # Prompt templates (plan/develop/review/enrich)
│   ├── changes/
│   │   ├── planes/KAN-XX/                # Generated implementation plans
│   │   └── enriquecimientos/KAN-XX/      # Ticket enrichments
│   └── specs/
│       ├── stacks/
│       │   ├── vault-smart-contracts-standards.mdc
│       │   └── vault-core-api-gotchas.md
│       ├── base-standards.mdc
│       └── documentation-standards.mdc
├── contracts/               # Vault Smart Contract source files (*.py)
├── contracts_sdk/           # Thought Machine contracts_api SDK (local install)
├── openspec/config.yaml     # Active stack, active agent, language
├── tests/                   # Contract test suite + vault_lint tests
├── pytest.ini               # pytest config (testpaths, pythonpath)
├── .env.example             # Environment variable template
└── .github/workflows/ci.yml # CI: lint + lint tests + contract tests
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

# 3. Install the local contracts_api SDK
cd contracts_sdk/contracts_sdk && pip install . && cd ../..
pip install -r requirements.txt

# 4. Select the stack and your agent
os-stack vault-smart-contracts
os-agent claude-code            # or copilot / cursor / windsurf / aider

# 5. Work a ticket
os-enrich KAN-15                 # enrich ticket with hooks + params
os-enrich-apply KAN-15
os-plan KAN-15                   # implementation plan → ai-specs/changes/planes/
os-develop KAN-15               # feature branch + contract scaffold
os-vault-test --coverage        # lint + pytest ≥ 90% before PR
os-commit KAN-15                # commit + PR → develop
os-review 1 && os-review-apply 1
```

On Windows, run these from Git Bash — PowerShell has no `sh` by default.

See [`.openspec-cli/README.md`](.openspec-cli/README.md) for full command
documentation and troubleshooting.

---

## Vault Smart Contracts

Contracts are Python written against the **Contracts Language API 4.0**, verified
against the locally-installed `contracts_api` SDK.

### Sandbox restrictions

Vault executes contracts in a sandboxed Python environment. `os-vault-lint` performs
AST static analysis before any test runs and reports violations with file and line:

```
contracts/foo.py:12 [FORBIDDEN_IMPORT] import 'os' is not allowed
contracts/foo.py:34 [INSTANCE_UPDATE_PERMISSION] INSTANCE parameter 'denomination' must set update_permission=...
```

| Rule | Trigger |
|------|---------|
| `FORBIDDEN_IMPORT` | Banned stdlib module (`os`, `sys`, `json`, `re`, `datetime`, …) |
| `UNKNOWN_IMPORT` | Any import not from `contracts_api`, `decimal` or `zoneinfo` |
| `FORBIDDEN_CALL` | Bare call to `eval`, `exec`, `open`, `print`, `getattr`, `type`, … |
| `FLOAT_USED` | `float()` call or float literal — use `Decimal` |
| `TIMEZONE_UTC` | `timezone.utc` — use `ZoneInfo("UTC")` |
| `CLIENT_TRANSACTION_ID` | `client_transaction_id=` — use `instruction_details` |
| `PHASE_ON_BALANCE` | `.phase` read from a `Balance` value instead of the `BalanceCoordinate` key |
| `MUTABLE_GLOBAL` | Module-level `list`/`dict`/`set` not in allowed contract metadata |
| `EXCEPTION_CHAINING` | `raise X from Y` |
| `INSTANCE_UPDATE_PERMISSION` | `Parameter(level=INSTANCE)` without `update_permission` |
| `DERIVED_UPDATE_PERMISSION` | `update_permission` on a `derived=True` / TEMPLATE parameter |

The displayed checklist covers **8 rules**; a clean run prints `✔ 8/8 Vault rules — CLEAN`.

### Contracts

| Contract | Description | Tests |
| --- | --- | --- |
| `contracts/savings_product.py` | Basic savings account with monthly interest accrual | 23 ✅ |
| `contracts/current_account.py` | Current account with authorized overdraft limit | 23 ✅ |
| `contracts/fixed_term_deposit.py` | Daily accrual, maturity disbursement, early closure with penalty | 34 ✅ |
| `contracts/personal_loan.py` | Amortising loan, monthly repayments, prepayment penalty | 23 ✅ |
| `contracts/cuenta_joven.py` | Youth account: daily withdrawal limit + bonus interest rate | 32 ✅ |

### CI integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to
`main` / `master` / `develop`:

1. **Vault lint** — `python .openspec-cli/lib/vault_lint.py contracts/`
2. **vault_lint unit tests** — `pytest tests/test_vault_lint.py --cov=vault_lint --cov-fail-under=90`
3. **Contract-test guardrail** — `python .openspec-cli/lib/check_contract_tests.py`
   (every `contracts/*.py` must have a matching `tests/test_*.py`)
4. **Smart Contract tests** — `pytest tests/ --ignore=tests/test_vault_lint.py --cov=contracts --cov-fail-under=90`

---

## Vault sandbox — the rules that bite

Full detail in `ai-specs/.agents/stacks/vault-smart-contracts.md`. The essentials:

| Area | Rule |
|---|---|
| Money | `Decimal` only, never `float` |
| Datetime | `ZoneInfo("UTC")`, never `timezone.utc`; get it from `hook_arguments.effective_datetime` |
| Balances | phase is on `BalanceCoordinate` (key), not on `Balance` (value) |
| Rejections | `return …HookResult(rejection=Rejection(...))`, never `raise` |
| Instructions | no `client_transaction_id` — use `instruction_details` |
| Parameters | every INSTANCE param needs `update_permission`; DERIVED/TEMPLATE never do |
| Derived params | `Parameter(derived=True)` inside `parameters`, not `DerivedParameter` |
| Deploy | own `product_id` prefix (`openspec_…`), bump `version` per deploy, `X-Auth-Token` header |

---

## Architecture Principles

- **Test-Driven Development** — tests before implementation, always
- **90% coverage threshold** — enforced by `os-vault-test --coverage` and CI
- **English only** — all code, comments, docs, and commits
- **Conventional commits** — `feat`, `fix`, `test`, `docs`, `chore`
- **No secrets in code** — environment variables only
- **Never commit straight to `develop`/`main`** — `os-commit` always branches

---

## Contributing

1. Pick a ticket from Jira
2. `os-enrich <KAN-XX>` → add technical detail, then `os-enrich-apply`
3. `os-plan <KAN-XX>` → implementation plan
4. `os-develop <KAN-XX>` → implement the contract + tests
5. `os-vault-test --coverage` → must be green (≥ 90%)
6. `os-commit <KAN-XX>` → open a PR to `develop`
7. `os-review <PR>` → AI code review

---

## License

ISC
