# review-vault-pr

PR Number: $ARGUMENTS

## Goal
Review a Pull Request for Vault Smart Contract changes against sandbox rules,
API 4.0 patterns, and test quality. Save to `.openspec-cli/.review-output.md` only.

## Pre-flight checklist

1. Load stack agent and `ai-specs/specs/stacks/vault-smart-contracts-standards.mdc`
2. Read `ai-specs/specs/base-standards.mdc`
3. Analyse PR metadata and diff provided in the prompt
4. Load plan from `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md` if available
5. Verify tooling commands: `{{lint_command}}`, `{{test_command}}`, `{{coverage_command}}`

## Review areas (Vault-specific)

1. **Sandbox compliance** — forbidden imports/calls, mutable globals, exception chaining
2. **API 4.0 correctness** — rejections, hook args, balance access, CustomInstruction shape
3. **Contract design** — parameters, postings, schedules, denomination handling
4. **Testing** — coverage >= 90%, mock patterns, rejection and edge cases
5. **Security** — no secrets in contract/test code

### Sandbox checklist
- [ ] Only `contracts_api` and `decimal` imports in `contracts/*.py`
- [ ] No `eval`, `print`, `open`, `getattr`, `type`, `globals`, `locals`
- [ ] Module-level lists only on allowed names (`supported_denominations`, `parameters`, …)
- [ ] No `raise X from Y`
- [ ] No mutable global counters/caches between hooks

### API 4.0 checklist
- [ ] `PrePostingHookArguments` / `PostPostingHookArguments` include `client_transactions={}`
- [ ] Business failures return `Rejection(...)` — not `raise Rejected`
- [ ] Phase checked on `BalanceCoordinate` (key), not on `Balance` (value)
- [ ] Balances via `vault.get_balances_observation()`, not `get_balance_timeseries()`
- [ ] `CustomInstruction` uses `instruction_details` — no `client_transaction_id`
- [ ] Datetimes in tests use `ZoneInfo("UTC")`, not `timezone.utc`
- [ ] Derived params use `Parameter(derived=True)`, not `DerivedParameter`
- [ ] `OptionalValue` wraps `datetime`, not `date`, in tests

### Contract design checklist
- [ ] Monetary values use `Decimal`
- [ ] `supported_denominations` declared at module level; instance param uses `DenominationShape`
- [ ] Wrong-currency postings rejected with appropriate `RejectionReason` (e.g. `WRONG_DENOMINATION`)
- [ ] Internal transfers credit correct account addresses (not customer `DEFAULT` for fees/income)
- [ ] Hook signatures match API 4.0 types

### Testing checklist
- [ ] New/changed behaviour has unit tests in `tests/test_<product>.py`
- [ ] Happy path, rejection path, and edge cases covered
- [ ] `{{lint_command}}` would pass on changed contracts
- [ ] `{{test_command}}` and `{{coverage_command}}` criteria met (>= 90%)

## Process

1. Understand intent from diff and plan before listing issues
2. Classify issues: CRITICAL (blocking) / MAJOR / MINOR
3. Note 2–3 positives
4. Verdict: **APPROVE** / **REQUEST CHANGES** / **COMMENT ONLY**
5. Save to `.openspec-cli/.review-output.md` — do not write under `ai-specs/changes/`

## Language

Write the review in the Active Language from the prompt.

## Output format

---

### `# Code Review: PR #<NUMBER> — <TITLE>`

### `## Metadata`
- Author, branch, stack, date

### `## Summary`
One paragraph + overall verdict.

### `## Sandbox Compliance`
Pass/fail per rule; cite file:line for violations.

### `## API 4.0 Compliance`
Pass/fail per pattern above.

### `## Contract Design`
Parameters, hooks, postings, schedules — design assessment.

### `## Testing`
Coverage, test quality, missing cases.

### `## Security`
Secrets, sensitive data in logs or contract metadata.

### `## Specific Issues`
```
- **File**: `contracts/foo.py` (line N) — **Severity**: CRITICAL — **Fix**: ...
```

### `## What's Done Well`
2–3 highlights.

### `## Final Verdict`
**APPROVE** / **REQUEST CHANGES** / **COMMENT ONLY**

---

## Final message format

> I've saved the review to `.openspec-cli/.review-output.md`.
> Run `os-review-apply <PR_NUMBER>` to publish it to GitHub.
