# Backend Implementation Plan: KAN-8 Current Account with Overdraft Limit

## 1. Overview
This ticket delivers a Vault Contracts Language API 4.0 product for a current account with an authorized overdraft limit. The goal is to implement the contract behavior inside Vault hook logic, enforce overdraft validation, and provide developer-facing tests with OpenSpec CLI validation.

Active stack: `vault-smart-contracts` (`Thought Machine Vault Smart Contracts`)

## 2. Architecture Context
- Active stack: `vault-smart-contracts` (`Thought Machine Vault Smart Contracts`)
- Layers involved:
  - Contract implementation: `contracts/current_account.py`
  - Tests: `tests/test_current_account.py`
  - Tooling / validation: `os-vault-test`, `os-vault-lint`
- Files affected:
  - `contracts/current_account.py` — new Vault contract product
  - `tests/test_current_account.py` — new contract unit tests
  - `ai-specs/changes/KAN-8_backend.md` — implementation plan

## 3. Implementation Steps

### Step 0: Create Feature Branch
- Action: create and switch to a new branch.
- Branch: `feature/KAN-8-backend`
- Commands:
  ```bash
  git checkout main && git pull origin main
  git checkout -b feature/KAN-8-backend
  ```

### Step 1: Create contract scaffold
- File: `contracts/current_account.py`
- Implement contract metadata and parameters:
  - `api = "4.0.0"`
  - `version`, `display_name`, `summary`, `description`
  - `tside = Tside.LIABILITY`
  - `supported_denominations = ["GBP"]`
- Add constants:
  - `DEFAULT_ADDRESS = "DEFAULT"`
  - `DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"`
- Define parameters:
  - `denomination` as `DenominationShape`, `ParameterLevel.INSTANCE`, default `"GBP"`
  - `overdraft_limit` as `NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01"))`, `ParameterLevel.INSTANCE`

### Step 2: Implement balance helper functions
- Add pure helper functions with no side effects.
- Required helpers:
  - `_get_committed_balance(balances, denomination) -> Decimal`
  - `_calculate_overdraft_usage(current_balance: Decimal) -> Decimal`
  - `_calculate_available_balance(current_balance: Decimal, overdraft_limit: Decimal) -> Decimal`
- Ensure helpers use `BalanceCoordinate` and read `coord.phase == Phase.COMMITTED`.

### Step 3: Implement hook behavior
- `activation_hook`:
  - Return `ActivationHookResult(scheduled_events_return_value={})`
  - No additional scheduled events required unless a future interest or fee behavior is defined.
- `pre_posting_hook`:
  - Fetch `denomination` from `vault.get_parameter_timeseries(name="denomination").latest()`.
  - Fetch `overdraft_limit` from `vault.get_parameter_timeseries(name="overdraft_limit").latest()`.
  - Fetch balances via `vault.get_balances_observation(fetcher_id="live_balances").balances`.
  - Compute current committed balance.
  - Compute posting effect only from committed-phase postings.
  - Reject if `current_balance + posting_effect < -overdraft_limit`.
  - Return `PrePostingHookResult(rejection=Rejection(...))` with `RejectionReason.INSUFFICIENT_FUNDS`.
- `post_posting_hook`:
  - Return `PostPostingHookResult(posting_instructions_directives=[])`
  - No additional directives required for this feature.
- `scheduled_event_hook`:
  - Return `ScheduledEventHookResult(posting_instructions_directives=[], update_account_event_type_directives=[])`
  - No scheduled events required for the current ticket.

### Step 4: Define overdraft state calculations
- Within contract logic derive:
  - `overdraft_used = max(Decimal("0.00"), -current_balance)`
  - `overdraft_remaining = max(Decimal("0.00"), overdraft_limit - overdraft_used)`
  - `available_balance = current_balance + overdraft_limit`
- Use these values for validation and internal state commentary.

### Step 5: Add unit tests
- File: `tests/test_current_account.py`
- Test cases:
  - `test_withdrawal_with_positive_balance_is_allowed`
  - `test_withdrawal_within_overdraft_limit_is_allowed`
  - `test_withdrawal_exceeding_overdraft_limit_is_rejected`
  - `test_deposit_reduces_overdraft_usage`
  - `test_zero_balance_has_zero_overdraft_usage`
  - `test_parameter_retrieval_for_denomination_and_overdraft_limit`
  - `test_committed_balance_read_from_live_balances`
- Use mocks for `vault.get_parameter_timeseries`, `vault.get_balances_observation`, and `vault.get_hook_execution_id`.
- Ensure `PrePostingHookArguments` includes `client_transactions={}`.
- Use `ZoneInfo("UTC")` for any datetime test values.

### Step 6: Run validation and coverage
- Use OpenSpec tooling to verify implementation:
  - `os-vault-test`
  - `os-vault-test --coverage`
- Confirm contract syntax and sandbox restrictions with `vault-contract-validator validate contracts/` if available.

### Step 7: Update documentation
- If a contract catalog or developer guide is maintained, add a short note to the Vault smart contract standards or product documentation describing the new `current_account` contract and its `overdraft_limit` parameter.

## 4. Implementation Order
1. Step 0 — Create feature branch
2. Step 1 — Scaffold `contracts/current_account.py`
3. Step 2 — Add helper functions for committed balance and overdraft calculations
4. Step 3 — Implement Vault hooks and overdraft validation
5. Step 4 — Add derived overdraft state calculations
6. Step 5 — Add unit tests in `tests/test_current_account.py`
7. Step 6 — Run `os-vault-test` and `os-vault-test --coverage`
8. Step 7 — Update documentation if needed

## 5. Testing Checklist
- [ ] `python -m pytest tests/ -v` passes with 0 failures
- [ ] `pytest --cov=contracts --cov-report=html` reports coverage >= 90%
- [ ] `vault-contract-validator validate contracts/` reports no contract validation errors
- [ ] `os-vault-test` passes with all tests green
- [ ] `os-vault-test --coverage` passes with minimum 90% coverage
- [ ] New tests cover overdraft acceptance, rejection, and balance recovery

## 6. Tooling Reference
Commands resolved from `openspec/config.yaml`:

| Purpose | Command |
|---|---|
| Build | `pip install -r requirements.txt` |
| Test | `python -m pytest tests/ -v` |
| Run | `vault-contract-validator validate contracts/` |
| Coverage | `pytest --cov=contracts --cov-report=html` |

## 7. Error Response Format
Vault contract validation uses hook rejection objects instead of HTTP error payloads.

Use:
```python
return PrePostingHookResult(
    rejection=Rejection(
        message="Overdraft limit exceeded",
        reason_code=RejectionReason.INSUFFICIENT_FUNDS,
    )
)
```

## 8. Dependencies
- No new libraries required.
- Use only `contracts_api` and `decimal` imports in contract code.
- Ensure `tests/` only depends on existing test tooling in `requirements.txt`.

## 9. Notes
- Vault contracts cannot import standard library modules beyond `contracts_api` and `decimal`.
- Do not use `float` for monetary values; use `Decimal` exclusively.
- Do not use mutable global state between hook calls.
- Use `BalanceCoordinate.phase` when reading balances from `vault.get_balances_observation(fetcher_id="live_balances").balances`.
- `PrePostingHookArguments` must include `client_transactions={}` in API 4.0.
- `CustomInstruction` must use `instruction_details` for traceability if internal postings are added.

## 10. Implementation Verification Checklist
- [ ] Contract file is in `contracts/current_account.py`
- [ ] Test file is in `tests/test_current_account.py`
- [ ] `overdraft_limit` parameter is instance-level and validated
- [ ] Debit postings are rejected when they exceed the configured overdraft limit
- [ ] `RejectionReason.INSUFFICIENT_FUNDS` is used for invalid overdraft postings
- [ ] Contract passes static sandbox validation and runtime tests
- [ ] Coverage is >= 90%
- [ ] Documentation notes added if applicable
