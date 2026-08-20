# Copilot instructions for OpenSpec

## Project shape

This repository is a spec-driven AI workflow, not a conventional app service. The important architecture is spread across several files:

- `openspec/config.yaml` is the source of truth for the active stack, active agent, and language. It also defines the stack-specific build/test/lint commands.
- `ai-specs/` stores the reusable architectural standards and prompts used to drive AI-assisted development. The active stack for this repo is `vault-smart-contracts`.
- `contracts/` contains the Vault Smart Contract implementations (`savings_product.py`, `current_account.py`, `fixed_term_deposit.py`).
- `tests/` contains the contract test suite and validation scripts.
- `.openspec-cli/` contains the CLI workflow (`os-*` commands) and the `vault_lint.py` sandbox validator.
- `contracts_sdk/contracts_sdk/` is the local Thought Machine SDK that must be installed before running Vault contract checks.

The repo expects AI work to be guided by stored specs and stack conventions, not by ad hoc assumptions.

## Build, test, and lint commands

This repo is currently configured for the Vault Smart Contracts stack. Use the repo-root commands below from the repository root.

### Initial setup

```bash
python -m pip install -r requirements.txt
cd contracts_sdk/contracts_sdk && python -m pip install .
cd ../..
```

### Lint

```bash
python .openspec-cli/lib/vault_lint.py contracts/
```

This is the enforced Vault sandbox validation. It checks the restricted Python subset used by Thought Machine smart contracts.

### Test single files

```bash
pytest tests/test_vault_lint.py -v
pytest tests/test_savings_product.py -v
pytest tests/test_current_account.py -v
pytest tests/test_fixed_term_deposit.py -v
```

### Full validation

```bash
pytest tests/ -v --cov=contracts --cov-report=term-missing --cov-fail-under=90
```

This project is expected to maintain at least 90% coverage on the contract code.

### Stack-level commands from the project config

The active stack declares the following canonical commands in `openspec/config.yaml`:

```bash
python .openspec-cli/lib/vault_lint.py contracts/
python -m pytest tests/ -v
python .openspec-cli/lib/vault_lint.py contracts/ && python -m pytest tests/ -v --cov=contracts --cov-report=html --cov-fail-under=90
```

## Key conventions

### Vault contract rules are specific and enforced

The repo is built around Thought Machine Vault API 4.0. Smart contracts are not ordinary Python and must follow the sandbox restrictions enforced by `vault_lint.py`.

Do not introduce patterns like these into `contracts/*.py`:

- stdlib imports such as `os`, `sys`, `json`, `re`, `math`, `datetime`, `collections`, `random`, etc.
- `eval`, `exec`, `__import__`, `globals`, `locals`, `type`, `dir`, `getattr`, `setattr`
- `print`, `open`, `input`
- mutable global state; avoid module-level caches or counters
- network access or side effects
- `raise ... from ...` exception chaining

Use only the Vault-compatible subset and keep logic pure and deterministic.

### Money handling must use `Decimal`

This repo uses financial logic and decimal arithmetic throughout. Prefer:

```python
from decimal import Decimal, ROUND_HALF_UP
```

and avoid floats for money calculations. Quantization and rounding are expected to be explicit and intentional.

### Vault API 4.0 semantics are different from older examples

The project includes repo-specific rules from the Vault API 4.0 migration. When changing contracts, follow these patterns instead of older 3.x guidance:

- use `ZoneInfo` for timezone-aware datetimes; avoid `datetime.timezone.utc`
- phase data lives on `BalanceCoordinate`, not on the balance object itself
- rejection is returned via `PrePostingHookResult(rejection=...)`, not by raising `Rejected`
- `CustomInstruction` does not take `client_transaction_id`
- `PrePostingHookArguments` requires `client_transactions={}`
- prefer `vault.get_balances_observation(fetcher_id="live_balances")` over legacy balance time-series APIs

These are not just style preferences; they are compatibility constraints for the installed SDK.

### Contract and test structure

- Contract source files live under `contracts/` and are designed to be sandbox-safe, deterministic, and testable.
- Tests live under `tests/` and are executed directly with `pytest`.
- The repo expects the full suite, lint pass, and coverage threshold to pass before considering a change complete.
- Keep the contract logic composable and helper-driven rather than relying on runtime mutation or hidden state.

### Workflow conventions for this repo

The repo is intentionally structured around ticket-driven, spec-driven development:

- `os-stack` selects the stack/context model
- `os-agent` selects how prompts are delivered
- `os-plan`, `os-develop`, and `os-review` rely on the active stack and project specs in `ai-specs/`
- for Vault work, the default stack and expected validation path are contract lint + pytest + coverage

When editing contract behavior, match the conventions in `ai-specs/.agents/stacks/vault-smart-contracts.md` and `ai-specs/specs/stacks/vault-smart-contracts-standards.mdc` rather than assuming generic Python rules.

## Working effectively in this repo

- Keep changes aligned with the active Vault stack; do not silently switch to generic Python patterns.
- Prefer targeted, contract-specific tests before broad validation.
- If a change touches contract semantics, validate both linting and the relevant contract test files.
- Treat `vault_lint.py` as a required gate for any contract change.
- Preserve the project’s spec-driven workflow: the repo expects context from `openspec/` and `ai-specs/` to influence implementation decisions.
