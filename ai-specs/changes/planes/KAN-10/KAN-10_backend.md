# Backend Implementation Plan: KAN-10 — Depósito a Plazo Fijo (Fixed-Term Deposit)

## 1. Overview

Implement a Vault Smart Contract (`contracts/fixed_term_deposit.py`) that models a
Fixed-Term Deposit: a liability product where a customer locks a principal for a defined
period and earns a guaranteed daily-accrued interest rate. Principal + interest are
automatically disbursed on the maturity date via a scheduled event. Early closure is
optionally supported with a configurable penalty.

Active stack: `vault-smart-contracts` (Thought Machine Vault Contracts Language API 4.0)

---

## 2. Architecture Context

| Layer | File | Role |
|---|---|---|
| Contract Definition | `contracts/fixed_term_deposit.py` | Parameters, event types, fetchers, hooks |
| Tests | `tests/test_fixed_term_deposit.py` | 22 unit tests with `contracts_api` SDK |

**No** migrations, services, repositories, or HTTP endpoints — Vault contracts are
self-contained state machines driven by hooks and scheduled events.

**Balance addresses used:**

| Address | Purpose |
|---|---|
| `DEFAULT` | Customer principal |
| `ACCRUED_INTEREST` | Running daily interest (internal) |

---

## 3. Implementation Steps

### Step 0: Create Feature Branch
- **Branch**: `feature/KAN-10-backend`
- **Commands**:
  ```bash
  git checkout develop && git pull origin develop
  git checkout -b feature/KAN-10-backend
  ```

---

### Step 1: Contract Skeleton — Imports, Metadata, Constants
- **File**: `contracts/fixed_term_deposit.py`
- **Content**:
  - `api = "4.0.0"`, `version = "1.0.0"`, `tside = Tside.LIABILITY`
  - `display_name`, `summary`, `description`
  - `supported_denominations = ["GBP"]`
  - Constants: `DEFAULT_ADDRESS = "DEFAULT"`, `ACCRUED_INTEREST = "ACCRUED_INTEREST"`, `DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"`
  - Event name constants: `DAILY_ACCRUAL = "DAILY_ACCRUAL"`, `MATURITY_EVENT = "MATURITY_EVENT"`
- **Imports required**:
  ```python
  from contracts_api import (
      ActivationHookArguments, ActivationHookResult,
      PrePostingHookArguments, PrePostingHookResult,
      PostPostingHookArguments, PostPostingHookResult,
      ScheduledEventHookArguments, ScheduledEventHookResult,
      DerivedParameterHookArguments, DerivedParameterHookResult,
      BalancesObservationFetcher, BalanceCoordinate, BalanceDefaultDict,
      CustomInstruction, Posting, PostingInstructionsDirective,
      Parameter, ParameterLevel, NumberShape, DenominationShape,
      DateShape, OptionalShape, UnionShape, UnionItem, OptionalValue,
      ScheduledEvent, ScheduleExpression, SmartContractEventType,
      DerivedParameter, NumberShape as DerivedNumberShape,
      Rejection, RejectionReason, Phase, Tside, DefinedDateTime,
  )
  from decimal import Decimal, ROUND_HALF_UP
  from zoneinfo import ZoneInfo
  ```
  > No `import datetime`, `import os`, or any stdlib. `ZoneInfo` is the only external import.

---

### Step 2: Parameters Definition
- **File**: `contracts/fixed_term_deposit.py` — `parameters` list
- **5 parameters**:

  | `name` | Shape | Level | Default | Notes |
  |---|---|---|---|---|
  | `denomination` | `DenominationShape()` | `INSTANCE` | `"GBP"` | Single denomination enforced in pre_posting |
  | `annual_interest_rate` | `NumberShape(min_value=0, max_value=1, step=0.0001)` | `TEMPLATE` | `Decimal("0.05")` | AER; 0.05 = 5% |
  | `maturity_date` | `DateShape()` | `INSTANCE` | *(required)* | Validated in activation_hook |
  | `allow_early_closure` | `OptionalShape(UnionShape([UnionItem("true","True"), UnionItem("false","False")]))` | `TEMPLATE` | `OptionalValue("false")` | Enables withdrawal before maturity with penalty |
  | `early_closure_penalty_rate` | `NumberShape(min_value=0, max_value=1, step=0.0001)` | `TEMPLATE` | `Decimal("0.20")` | Fraction of accrued interest forfeited (0.20 = 20%) |

---

### Step 3: Event Types + Balance Observation Fetchers
- **File**: `contracts/fixed_term_deposit.py`

  ```python
  # event_types: declares which scheduled events this contract can fire
  event_types = [
      SmartContractEventType(name=DAILY_ACCRUAL),
      SmartContractEventType(name=MATURITY_EVENT),
  ]
  event_types_groups = []

  # fetchers: declares what balance snapshots hooks can request
  balance_observation_fetchers = [
      BalancesObservationFetcher(
          fetcher_id="live_balances",
          at=DefinedDateTime.LIVE,
      )
  ]
  ```

---

### Step 4: `activation_hook`
- **Purpose**: Validate `maturity_date` is in the future; register both scheduled events.
- **Logic**:
  1. `maturity_date = vault.get_parameter_timeseries(name="maturity_date").latest()`
  2. `effective_date = hook_arguments.effective_datetime.date()`
  3. If `maturity_date <= effective_date` → raise `InvalidContractParameter` (reject activation)
  4. Build `DAILY_ACCRUAL` schedule:
     ```
     ScheduleExpression(hour="23", minute="59", second="59")
     ```
  5. Build `MATURITY_EVENT` schedule (one-shot using maturity_date fields):
     ```
     ScheduleExpression(
         year=str(maturity_date.year),
         month=str(maturity_date.month),
         day=str(maturity_date.day),
         hour="0", minute="0", second="0",
     )
     ```
  6. Return `ActivationHookResult(scheduled_events_return_value={DAILY_ACCRUAL: ..., MATURITY_EVENT: ...})`
- **Error**: `InvalidContractParameter` with message `"maturity_date must be strictly in the future."`

---

### Step 5: `pre_posting_hook`
- **Purpose**: Enforce denomination, reject early withdrawals, reject second deposits. Allow early closure if flag is set.
- **Logic** (execute for each posting instruction):
  1. `denomination = vault.get_parameter_timeseries(name="denomination").latest()`
  2. For each posting in `hook_arguments.posting_instructions`:
     - If posting denomination ≠ denomination → reject `WRONG_DENOMINATION`
  3. Compute `posting_net` = sum of `balance.net` for `coord.phase == Phase.COMMITTED` across all postings
  4. Read `principal = _get_committed_balance(balances, "DEFAULT", denomination)`
  5. **If `posting_net < 0`** (withdrawal/debit):
     - Read `allow_early_closure = vault.get_parameter_timeseries(name="allow_early_closure").latest()`
     - If `allow_early_closure` is `None` or value is `"false"` → reject `AGAINST_TERMS_AND_CONDITIONS`: `"Withdrawals are not permitted before maturity."`
     - Otherwise → allow (no rejection; `post_posting_hook` will apply penalty)
  6. **If `posting_net > 0`** (deposit/credit) and `principal > 0` → reject `AGAINST_TERMS_AND_CONDITIONS`: `"Only one deposit is accepted at account opening."`
  7. Return `PrePostingHookResult()` (no rejection = accepted)
- **Helper**: `_get_committed_balance(balances, address, denomination) -> Decimal`
  Uses `BalanceCoordinate(account_address=address, asset=DEFAULT_ASSET, denomination=denomination, phase=Phase.COMMITTED)`

---

### Step 6: `post_posting_hook` — Early Closure Penalty
- **Purpose**: When early closure is allowed and principal just reached 0, apply penalty to accrued interest and move net interest to DEFAULT.
- **Logic**:
  1. Read `allow_early_closure` — if `"false"` or `None`, return immediately (no-op)
  2. Read `denomination`
  3. Fetch live balances
  4. `principal_after = _get_committed_balance(balances, "DEFAULT", denomination)`
  5. `accrued = _get_committed_balance(balances, "ACCRUED_INTEREST", denomination)`
  6. If `principal_after == 0` and `accrued > 0`:
     - `penalty_rate = vault.get_parameter_timeseries(name="early_closure_penalty_rate").latest()`
     - `penalty = (accrued * penalty_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)`
     - `net_payout = max(accrued - penalty, Decimal("0"))`
     - Build `CustomInstruction` to move `net_payout` from `ACCRUED_INTEREST` → `DEFAULT`
     - If `accrued - net_payout > 0`: build second `CustomInstruction` to zero remaining `ACCRUED_INTEREST` (forfeited penalty, debit ACCRUED_INTEREST, credit internal penalty address or just net to zero)
  7. Return `PostPostingHookResult(posting_instructions_directives=[...])`
- **Note**: If `accrued == 0` → return `PostPostingHookResult(posting_instructions_directives=[])`

---

### Step 7: `scheduled_event_hook` — DAILY_ACCRUAL
- **Purpose**: Accrue daily interest from principal into `ACCRUED_INTEREST`.
- **Logic**:
  1. Check `hook_arguments.event_type == DAILY_ACCRUAL`
  2. `denomination = vault.get_parameter_timeseries(name="denomination").latest()`
  3. `annual_rate = vault.get_parameter_timeseries(name="annual_interest_rate").latest()`
  4. `principal = _get_committed_balance(balances, "DEFAULT", denomination)`
  5. If `principal <= 0` → return `ScheduledEventHookResult(posting_instructions_directives=[])`
  6. `daily_rate = (annual_rate / Decimal("365")).quantize(Decimal("0.0000000001"), ROUND_HALF_UP)`
  7. `interest = (principal * daily_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)`
  8. If `interest == 0` → return no-op (rate is 0%)
  9. Build `CustomInstruction`:
     - `Posting(credit=False, amount=interest, account_address=DEFAULT_ADDRESS, ...)` — debit DEFAULT (cost of liability)
     - `Posting(credit=True,  amount=interest, account_address=ACCRUED_INTEREST, ...)` — credit ACCRUED_INTEREST
     - `instruction_details={"description": "Daily interest accrual", "hook_execution_id": str(vault.get_hook_execution_id())}`
  10. Return `ScheduledEventHookResult(posting_instructions_directives=[PostingInstructionsDirective(posting_instructions=[...])])`

---

### Step 8: `scheduled_event_hook` — MATURITY_EVENT
- **Purpose**: Sweep accrued interest back to DEFAULT; full principal + interest now available for withdrawal.
- **Logic**:
  1. Check `hook_arguments.event_type == MATURITY_EVENT`
  2. `denomination = vault.get_parameter_timeseries(name="denomination").latest()`
  3. `accrued = _get_committed_balance(balances, "ACCRUED_INTEREST", denomination)`
  4. If `accrued == 0` → return `ScheduledEventHookResult(posting_instructions_directives=[])`
  5. Build `CustomInstruction`:
     - `Posting(credit=True,  amount=accrued, account_address=DEFAULT_ADDRESS, ...)` — credit DEFAULT
     - `Posting(credit=False, amount=accrued, account_address=ACCRUED_INTEREST, ...)` — debit ACCRUED_INTEREST
     - `instruction_details={"description": "Maturity disbursement", ...}`
  6. Return `ScheduledEventHookResult(...)`

---

### Step 9: `derived_parameter_hook`
- **Purpose**: Expose read-only computed values: `accrued_interest` and `days_to_maturity`.
- **Logic**:
  1. `denomination = vault.get_parameter_timeseries(name="denomination").latest()`
  2. `accrued = _get_committed_balance(balances, "ACCRUED_INTEREST", denomination)`
  3. `maturity_date = vault.get_parameter_timeseries(name="maturity_date").latest()`
  4. `today = hook_arguments.effective_datetime.date()`
  5. `days = max((maturity_date - today).days, 0)`
  6. Return `DerivedParameterHookResult(parameters_return_value={"accrued_interest": accrued, "days_to_maturity": days})`
- **`derived_parameters` list** (at module level):
  ```python
  derived_parameters = [
      DerivedParameter(name="accrued_interest",  shape=NumberShape(), display_name="Accrued Interest"),
      DerivedParameter(name="days_to_maturity",  shape=NumberShape(), display_name="Days to Maturity"),
  ]
  ```

---

### Step 10: Helper Functions
- **File**: `contracts/fixed_term_deposit.py` (module-level, pure, no side effects)

  ```python
  def _get_committed_balance(balances, address: str, denomination: str) -> Decimal
  def _get_early_closure_flag(vault) -> bool
  ```

  `_get_committed_balance`: builds `BalanceCoordinate` with `Phase.COMMITTED` on the key, returns `balances[coord].net`.

  `_get_early_closure_flag`: reads `allow_early_closure` optional param; returns `True` only if value is explicitly `"true"`.

---

### Step 11: Test File — 22 Tests
- **File**: `tests/test_fixed_term_deposit.py`
- **Test helper functions** (`make_vault`, `make_balance_dict`, `make_posting`) follow the pattern from `tests/test_savings_product.py`
- **22 tests** (one `unittest.TestCase` class or grouped functions):

  | # | Test name | Scenario |
  |---|---|---|
  | 1 | `test_activation_valid_future_maturity` | activation succeeds, DAILY_ACCRUAL + MATURITY_EVENT registered |
  | 2 | `test_activation_rejects_maturity_today` | maturity_date == today → rejected |
  | 3 | `test_activation_rejects_maturity_past` | maturity_date yesterday → rejected |
  | 4 | `test_initial_deposit_accepted` | first credit on empty account → no rejection |
  | 5 | `test_second_deposit_rejected` | second credit on funded account → AGAINST_TERMS |
  | 6 | `test_wrong_denomination_rejected` | USD on GBP account → WRONG_DENOMINATION |
  | 7 | `test_withdrawal_before_maturity_rejected` | debit, allow_early_closure=false → AGAINST_TERMS |
  | 8 | `test_zero_amount_posting_accepted` | zero-value debit → no rejection |
  | 9 | `test_daily_accrual_standard_rate` | 5% AER on £1000 → £0.14 accrued |
  | 10 | `test_daily_accrual_zero_rate` | 0% AER → no CustomInstruction generated |
  | 11 | `test_daily_accrual_zero_balance` | principal = 0 → no posting |
  | 12 | `test_daily_accrual_leap_year` | Feb 29 date, still divides by 365 |
  | 13 | `test_daily_accrual_decimal_precision` | result quantized to 2 d.p. ROUND_HALF_UP |
  | 14 | `test_maturity_event_sweeps_accrued_interest` | ACCRUED_INTEREST → DEFAULT |
  | 15 | `test_maturity_event_zero_interest` | accrued = 0 → no CustomInstruction |
  | 16 | `test_maturity_payout_correct_total` | principal + accrued end up in DEFAULT |
  | 17 | `test_early_closure_disabled_rejects_withdrawal` | allow_early_closure=false, debit → AGAINST_TERMS |
  | 18 | `test_early_closure_enabled_allows_withdrawal` | allow_early_closure=true, debit → accepted |
  | 19 | `test_early_closure_penalty_applied` | penalty_rate=0.20, accrued=£10 → net=£8 |
  | 20 | `test_early_closure_penalty_floor_zero` | penalty > accrued → net = £0, not negative |
  | 21 | `test_derived_accrued_interest_matches_balance` | returns ACCRUED_INTEREST balance value |
  | 22 | `test_derived_days_to_maturity_correct` | returns correct (maturity - today).days, floor 0 |

---

### Step 12: Update Documentation
- `ai-specs/specs/data-model.md` — add `fixed_term_deposit` entry: parameters, balance addresses, event types
- No `api-spec.yml` changes (Vault contracts have no HTTP endpoints)
- `CLAUDE.md` — add `fixed_term_deposit.py` to "Completado" section after PR merges

---

## 4. Implementation Order

```
0  → Create feature/KAN-10-backend
1  → Contract skeleton (imports, metadata, constants)
2  → Parameters list (5 params)
3  → event_types + balance_observation_fetchers
10 → Helper functions (_get_committed_balance, _get_early_closure_flag)
4  → activation_hook
5  → pre_posting_hook
7  → scheduled_event_hook DAILY_ACCRUAL
8  → scheduled_event_hook MATURITY_EVENT
6  → post_posting_hook (early closure penalty)
9  → derived_parameter_hook + derived_parameters list
11 → Test file (22 tests)
   → os-vault-test (all green)
   → os-vault-test --coverage (>= 90%)
12 → Documentation update
```

> Helpers first because hooks depend on them. `post_posting_hook` last among hooks
> because it depends on the balance state established by the other hooks being correct.

---

## 5. Testing Checklist

- [ ] `python -m pytest tests/test_fixed_term_deposit.py -v` — 22/22 pass
- [ ] `pytest --cov=contracts --cov-report=html` — coverage >= 90%
- [ ] `python -m pytest tests/ -v` — existing savings + current account tests still green
- [ ] No `import` of stdlib modules in `contracts/fixed_term_deposit.py`
- [ ] No `timezone.utc` anywhere — only `ZoneInfo("UTC")`
- [ ] No `client_transaction_id` on any `CustomInstruction`
- [ ] Phase read from `BalanceCoordinate` (key), never from `Balance` (value)

---

## 6. Tooling Reference

| Purpose | Command |
|---|---|
| Install deps | `pip install -r requirements.txt` |
| Run all tests | `python -m pytest tests/ -v` |
| Single file | `python -m pytest tests/test_fixed_term_deposit.py -v` |
| Coverage | `pytest --cov=contracts --cov-report=html` |
| Validate contract | `vault-contract-validator validate contracts/fixed_term_deposit.py` |

---

## 7. Rejection / Error Format (Vault API 4.0)

Vault contracts do not return HTTP JSON errors. Rejections are returned via:

```python
return PrePostingHookResult(
    rejection=Rejection(
        message="Human-readable message in English",
        reason_code=RejectionReason.<CODE>,
    )
)
```

| Scenario | `RejectionReason` |
|---|---|
| Wrong denomination | `WRONG_DENOMINATION` |
| Withdrawal before maturity | `AGAINST_TERMS_AND_CONDITIONS` |
| Second deposit | `AGAINST_TERMS_AND_CONDITIONS` |
| Invalid maturity date (activation) | `InvalidContractParameter` (raised, not returned) |

---

## 8. Dependencies

No new packages required. The existing `contracts_sdk/` local install provides
`contracts_api`. Verify with:

```bash
py -c "from contracts_api import BalancesObservationFetcher, DerivedParameter, DateShape; print('OK')"
```

If `DerivedParameter` or `DateShape` are missing, check the SDK version in `contracts_sdk/`.

---

## 9. Notes

- **`DateShape` parameters** return a `datetime.date` object from `.latest()` — use `.year`, `.month`, `.day` to build `ScheduleExpression` for MATURITY_EVENT.
- **`OptionalShape` parameter** — `allow_early_closure.latest()` returns `OptionalValue`. Read `.is_set()` and `.value` (or compare directly to `"true"`).
- **DAILY_ACCRUAL after maturity** — once MATURITY_EVENT fires, the DAILY_ACCRUAL event will continue to fire daily but the DEFAULT balance will have been disbursed. The no-op guard (`if principal <= 0: return`) prevents spurious postings.
- **Tside = LIABILITY** — for a LIABILITY account, a customer deposit is a `credit` to DEFAULT (increases balance). A payout at maturity is a `debit` from DEFAULT. Keep debit/credit semantics consistent with this.
- **Test isolation** — each test must create its own `MagicMock` vault; do not share mocks between tests.

---

## 10. Implementation Verification Checklist

- [ ] `contracts/fixed_term_deposit.py` — no stdlib imports, no mutable globals
- [ ] `api = "4.0.0"` declared at module level
- [ ] All 5 parameters declared in `parameters` list
- [ ] `event_types` declares both `DAILY_ACCRUAL` and `MATURITY_EVENT`
- [ ] `balance_observation_fetchers` declares `"live_balances"` with `DefinedDateTime.LIVE`
- [ ] `derived_parameters` declares both `accrued_interest` and `days_to_maturity`
- [ ] All 5 hooks implemented and return the correct result type
- [ ] All `CustomInstruction` use `instruction_details` — no `client_transaction_id`
- [ ] Phase read only from `BalanceCoordinate`, never from `Balance`
- [ ] All datetimes use `ZoneInfo("UTC")` — no `timezone.utc`
- [ ] 22 tests, all green, coverage >= 90%
- [ ] `tests/test_savings_product.py` and `tests/test_current_account.py` still pass

---

> I've created a plan at `ai-specs/changes/KAN-10_backend.md`.
> Please review it before proceeding with implementation.
