# plan-vault-contract

Ticket ID: $ARGUMENTS

## Goal
Generate a step-by-step Vault Smart Contract implementation plan for a Jira ticket,
ready for autonomous implementation with `os-develop`.

## Pre-flight checklist

1. Read `openspec/config.yaml` and resolve stack agent, standards, and tooling commands
2. Read `ai-specs/specs/base-standards.mdc`
3. Read existing plans under `ai-specs/changes/planes/` for related contracts
4. Use the Jira ticket content provided in the prompt (do not re-fetch)

## Process

1. Adopt the role in `ai-specs/.agents/stacks/vault-smart-contracts.md`
2. Identify hooks, parameters, postings, schedules, and test cases required
3. Propose the plan using the output format below
4. Save at `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`
5. **Plan only — do not write contract or test code**

## Language

Write the entire plan in the Active Language from the prompt.
When Active Language is Spanish, translate section headers (e.g. `## 1. Resumen`).
Keep Vault hook names and `contracts_api` types in English.

## Output format

Save `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`:

---

### `# Vault Implementation Plan: <TICKET-ID> <Feature Name>`

### `## 1. Overview`
Product behaviour, hooks involved, sandbox constraints. State active stack.

### `## 2. Architecture Context`
- Active stack: `vault-smart-contracts`
- Files:
  - `contracts/<product_name>.py` — Smart Contract (API 4.0)
  - `tests/test_<product_name>.py` — unit tests with `contracts_api` SDK mocks
  - Tooling: `os-vault-lint`, `os-vault-test`, optional `os-vault-simulate`

### `## 3. Implementation Steps`

#### Step 0: Feature branch
- Branch: `feature/<ticket-id>-backend` (created by `os-develop` from `develop`)

#### Step 1: Contract scaffold
- File: `contracts/<product_name>.py`
- Metadata: `api = "4.0.0"`, `version`, `display_name`, `summary`, `description`, `tside`
- `supported_denominations = ["GBP", "USD", "EUR", "COP"]` (or subset if ticket specifies)
- Parameters: shapes, levels (`TEMPLATE` / `INSTANCE`), `default_value` rules
- Constants: `DEFAULT_ADDRESS`, `DEFAULT_ASSET`, internal addresses (e.g. `ACCRUED_INTEREST`)

#### Step 2: Pure helper functions
- Balance helpers using `BalanceCoordinate` and `Phase.COMMITTED` on the **key**
- Money helpers using `Decimal` only — never `float`
- No mutable module-level state beyond allowed contract metadata globals

#### Step 3: Hook implementation
For each hook list signature, inputs, outputs, and business rules:
- `activation_hook` — scheduled events to register
- `pre_posting_hook` — validations; return `PrePostingHookResult(rejection=Rejection(...))`
- `post_posting_hook` — internal transfers via `CustomInstruction`
- `scheduled_event_hook` — accrual / maturity / disbursement logic
- `derived_parameter_hook` — if derived params use `Parameter(derived=True)` (not `DerivedParameter`)

#### Step 4: Unit tests (TDD order)
- File: `tests/test_<product_name>.py`
- Fixtures: `ZoneInfo("UTC")`, `BalanceDefaultDict`, `MagicMock` vault
- `PrePostingHookArguments` / `PostPostingHookArguments` must include `client_transactions={}`
- List named test cases: happy path, rejections, edge cases, denomination mismatch if applicable

#### Step 5: Sandbox lint and test gate
```bash
{{lint_command}}
{{test_command}}
{{coverage_command}}
```

#### Step 6: Documentation
- Update `ai-specs/specs/stacks/vault-smart-contracts-standards.mdc` if new patterns emerge
- Update `ai-specs/.agents/stacks/vault-smart-contracts.md` only if agent guidance changes

---

### `## 4. Implementation Order`
Numbered list from Step 0 through documentation.

### `## 5. Testing Checklist`
- [ ] `{{lint_command}}` — zero violations
- [ ] `{{test_command}}` — all tests green
- [ ] `{{coverage_command}}` — coverage >= 90%
- [ ] Rejection paths tested with correct `RejectionReason`
- [ ] Existing contract tests not broken

### `## 6. Tooling Reference`

| Purpose | Command |
|---|---|
| Build (SDK) | `{{build_command}}` |
| Lint | `{{lint_command}}` |
| Test | `{{test_command}}` |
| Coverage | `{{coverage_command}}` |
| Simulate (optional) | `os-vault-simulate contracts/<product>.py <start> <end> '<params>'` |

### `## 7. Rejection & validation catalogue`
List expected `RejectionReason` values and trigger conditions (not HTTP status codes).

### `## 8. Dependencies`
- `contracts_api` SDK from `contracts_sdk/contracts_sdk/` (`pip install .`)
- No stdlib imports in contract code

### `## 9. Notes`
Business rules, posting invariants, schedule timing, denomination policy (one currency per account).

### `## 10. Verification Checklist`
- [ ] Only `contracts_api` and `decimal` imports in contract files
- [ ] No `raise` for business rejections — return `PrePostingHookResult(rejection=...)`
- [ ] Phase read from `BalanceCoordinate`, not `Balance`
- [ ] `CustomInstruction` uses `instruction_details`, not `client_transaction_id`
- [ ] `supported_denominations` used (not a separate `SUPPORTED_DENOMINATIONS` alias)
- [ ] Coverage >= 90%; all tests pass

---

## Final message format

> I've created a plan at `ai-specs/changes/planes/<ticket-id>/<ticket-id>_backend.md`.
> Please review it before running `os-develop <ticket-id>`.
