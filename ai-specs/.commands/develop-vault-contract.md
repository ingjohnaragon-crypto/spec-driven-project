# develop-vault-contract

Implement the Jira ticket: $ARGUMENTS

## Autonomous execution (mandatory)

- **Do not ask the human questions.** Do not pause for product/design choices.
- Every ambiguous rule is already locked in the plan section
  `## 2.1 Decisiones bloqueadas` (or equivalent). Follow it exactly.
- If something is still missing, choose the option that matches
  `contracts/fixed_term_deposit.py` + Vault API 4.0 sandbox rules, document the
  choice in a short code comment, and continue.
- Deliver a **complete** contract + tests — not a skeleton, not TODOs, not
  `try/except` wrappers around `contracts_api` imports.
- Correct hook names only: `activation_hook`, `pre_posting_hook`,
  `post_posting_hook`, `scheduled_event_hook`, `derived_parameter_hook`.
  Never invent `pre_posting_code` / `post_posting_code`.

## Pre-flight checklist

1. Read active stack agent and standards from `openspec/config.yaml`
2. Read `ai-specs/specs/base-standards.mdc`
3. Read the plan at `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`
4. Skim golden reference: `contracts/fixed_term_deposit.py` and
   `tests/test_fixed_term_deposit.py` — mirror structure, metadata, posting
   helpers, and test style
5. **You are already on branch `feature/<ticket-id>-backend`** — do not recreate it

## Vault sandbox rules (mandatory)

- Allowed imports in `contracts/*.py`: `contracts_api`, `decimal` only
- No stdlib (`os`, `datetime`, `json`, …), no `eval`/`print`/`getattr`, no mutable globals
- Allowed module-level metadata: `api`, `version`, `supported_denominations`, `parameters`, etc.
- Money: always `Decimal`, never `float`
- Rejections: return `PrePostingHookResult(rejection=Rejection(...))` — never `raise Rejected`
- API 4.0: `client_transactions={}` in pre/post posting args; phase on `BalanceCoordinate` key

## Implementation steps

### Step 1 — Understand the ticket
- Map acceptance criteria → hooks, parameters, and tests from the plan
- Contract: `contracts/<product_name>.py`
- Tests: `tests/test_<product_name>.py`
- Apply every locked decision from plan §2.1

### Step 2 — Write tests first (TDD)
- Add failing tests **before** changing contract logic
- Copy patterns from `tests/test_fixed_term_deposit.py`:
  - `unittest.mock.MagicMock` for `vault`
  - `ZoneInfo("UTC")` for datetimes
  - Grouped test classes by behaviour
  - Mock `vault.get_balances_observation().balances`, not `get_balance_timeseries()`
- Cover: activation, schedule events, happy postings, rejections, edge cases,
  multi-denomination (`GBP`/`USD`/`EUR`/`COP` as applicable)
- Confirm failures for the right reason:
  ```bash
  {{test_command}}
  ```

### Step 3 — Implement the full contract
- Follow the plan step order
- Populate real `parameters = [...]` (no empty tuples)
- Keep helpers pure; use `_get_committed_balance` / `_posting_net_effect` style from FTD
- For derived params: `Parameter(derived=True)` + `derived_parameter_hook`
- Remove any prior skeleton/fallback code if replacing an incomplete file

### Step 4 — Sandbox lint
```bash
{{lint_command}}
```
Fix every violation before proceeding.

### Step 5 — Tests and coverage
```bash
{{build_command}}
{{coverage_command}}
```
Coverage must be >= 90%. Add tests for uncovered branches before stopping.
Quality bar: depth comparable to `test_fixed_term_deposit.py` for a full product.

### Step 6 — Optional simulation
Only if the ticket requires Core simulation and credentials exist:
```bash
os-vault-simulate contracts/<product>.py "<start>" "<end>" '<params_json>'
```

### Step 7 — Update specs (if needed)
- `ai-specs/specs/stacks/vault-smart-contracts-standards.mdc` — new reusable patterns only
- Do **not** update `data-model.md` or `api-spec.yml`

### Step 8 — Hand off to commit
When lint and coverage pass, tell the user to run:
```bash
os-vault-test --coverage
os-commit $ARGUMENTS
```

## Rules
- **No human decision gates** during implementation
- **TDD mandatory** — tests before contract implementation
- **Use resolved tooling commands** — never hardcode unrelated linters
- Prefer English for code identifiers; follow Active Language for user-facing docs
- Stage only files for this ticket: `contracts/`, `tests/`, related spec updates
- Do not commit `.env`, `htmlcov/`, or `__pycache__/`
