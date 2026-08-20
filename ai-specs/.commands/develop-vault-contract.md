# develop-vault-contract

Implement the Jira ticket: $ARGUMENTS

## Pre-flight checklist

1. Read active stack agent and standards from `openspec/config.yaml`
2. Read `ai-specs/specs/base-standards.mdc`
3. Read the plan at `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md` if it exists
4. **You are already on branch `feature/<ticket-id>-backend`** — do not recreate the branch

## Vault sandbox rules (mandatory)

- Allowed imports in `contracts/*.py`: `contracts_api`, `decimal` only
- No stdlib (`os`, `datetime`, `json`, …), no `eval`/`print`/`getattr`, no mutable globals
- Allowed module-level metadata: `api`, `version`, `supported_denominations`, `parameters`, etc.
- Money: always `Decimal`, never `float`
- Rejections: return `PrePostingHookResult(rejection=Rejection(...))` — never `raise Rejected`
- API 4.0: `client_transactions={}` in pre/post posting args; phase on `BalanceCoordinate` key

## Implementation steps

### Step 1 — Understand the ticket
- Map acceptance criteria to hooks, parameters, and test cases from the plan
- Identify contract file: `contracts/<product_name>.py`
- Identify test file: `tests/test_<product_name>.py`

### Step 2 — Write tests first (TDD)
- Add failing tests **before** changing contract logic
- Use `unittest.mock.MagicMock` for `vault`, `ZoneInfo("UTC")` for datetimes
- Mock `vault.get_balances_observation().balances`, not `get_balance_timeseries()`
- Confirm tests fail for the expected reason:
  ```bash
  {{test_command}}
  ```

### Step 3 — Implement contract changes
- Follow the plan step order
- Keep helpers pure (no side effects, no global mutation)
- Use `_posting_net_effect(..., denomination)` pattern when filtering by currency
- For derived params: `Parameter(derived=True)` + `derived_parameter_hook`

### Step 4 — Sandbox lint
```bash
{{lint_command}}
```
Fix every violation before proceeding. Common fixes:
- Replace `SUPPORTED_DENOMINATIONS = [...]` with `supported_denominations = [...]`
- Remove forbidden imports and `raise X from Y`

### Step 5 — Tests and coverage
```bash
{{build_command}}
{{coverage_command}}
```
Coverage must be >= 90%. Add tests for uncovered branches before continuing.

### Step 6 — Optional simulation
If the ticket requires end-to-end behaviour against Vault Core (and credentials exist):
```bash
os-vault-simulate contracts/<product>.py "<start>" "<end>" '<params_json>'
```

### Step 7 — Update specs (if needed)
- `ai-specs/specs/stacks/vault-smart-contracts-standards.mdc` — new reusable patterns only
- Do **not** update `data-model.md` or `api-spec.yml` (not applicable to Vault contracts)

### Step 8 — Hand off to commit
When lint and coverage pass, tell the user to run:
```bash
os-vault-test --coverage
os-commit $ARGUMENTS
```

## Rules
- **TDD mandatory** — tests before contract implementation
- **Use resolved tooling commands** — never hardcode `pytest` or `ruff` for Vault
- Code, comments, and commit messages in English (unless Active Language is Spanish for user-facing text)
- Stage only files for this ticket: `contracts/`, `tests/`, related spec updates
- Do not commit `.env`, `htmlcov/`, or `__pycache__/`
