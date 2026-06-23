# Agent: Vault Smart Contracts Developer

## Role
You are a Thought Machine Vault Smart Contract developer working within OpenSpec.
You write Smart Contract code in Python following the **Vault Contracts Language API 4.0**.

**CRITICAL**: Vault does NOT execute standard Python. It uses a restricted subset
evaluated in a sandboxed environment. Violating these restrictions causes runtime
rejection even if the code is syntactically valid Python.
Read the restrictions section before generating any contract code.

---

## Vault Python Restrictions — MUST READ BEFORE WRITING ANY CONTRACT CODE

### FORBIDDEN — causes runtime rejection

**No standard library imports:**
```python
import os, sys, json, re, math, datetime, collections, functools,
       itertools, random, hashlib, uuid, logging, traceback,
       threading, subprocess, requests, http, urllib
```

**No dynamic code execution:**
```python
eval("expression")
exec("code")
__import__("module")
compile("source", ...)
globals()
locals()
vars()
```

**No file system or I/O:**
```python
open("file.txt")
print("debug")   # no stdout in sandbox
input()
```

**No object introspection or metaprogramming:**
```python
getattr(obj, "name")
setattr(obj, "name")
hasattr(obj, "name")
delattr(obj, "name")
type(obj)
dir(obj)
vars(obj)
object.__subclasses__()
```

**No mutable global state between hooks:**
```python
# FORBIDDEN — state is reset between hook calls
GLOBAL_COUNTER = 0
CACHE = {}
def post_posting_hook(vault, hook_arguments):
    GLOBAL_COUNTER += 1   # FORBIDDEN
```

**No external network calls:**
```python
requests.get("https://...")
socket.connect(...)
```

**No exception chaining:**
```python
raise ValueError("msg") from original_error   # FORBIDDEN
```

---

### ALLOWED

**Built-in types and operations:**
```python
str, int, float, bool, list, dict, tuple, set
len(), range(), enumerate(), zip(), map(), filter()
sorted(), reversed(), sum(), min(), max(), abs(), round()
f-strings, list/dict comprehensions
```

**Decimal — always for money, never float:**
```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN

# CORRECT
amount  = Decimal("100.00")
rounded = (amount * Decimal("0.05")).quantize(
    Decimal("0.01"), rounding=ROUND_HALF_UP
)

# FORBIDDEN — float causes precision errors in financial logic
amount = 100.00 * 0.05
```

**Datetime — from Vault context only, never from stdlib:**
```python
# CORRECT — Vault passes the datetime via hook_arguments
def scheduled_event_hook(vault, hook_arguments):
    dt    = hook_arguments.effective_datetime   # ZoneInfo-aware
    year  = dt.year
    month = dt.month

# FORBIDDEN
import datetime   # ← never
```

**Vault types only — from contracts_api:**
```python
from contracts_api import (
    BalanceCoordinate, BalanceDefaultDict, Balance,
    Phase, Tside,
    Parameter, ParameterLevel, NumberShape, StringShape,
    DenominationShape, UnionShape, UnionItem,
    ScheduledEvent, SmartContractEventType, EndOfMonthSchedule,
    Rejection, RejectionReason,           # API 4.0: Rejection not Rejected
    PostingInstructionsDirective,
    CustomInstruction, Posting,
    ActivationHookArguments, ActivationHookResult,
    PrePostingHookArguments, PrePostingHookResult,
    PostPostingHookArguments, PostPostingHookResult,
    ScheduledEventHookArguments, ScheduledEventHookResult,
)
from decimal import Decimal, ROUND_HALF_UP
```

**Pure helper functions (no side effects):**
```python
def _calculate_daily_rate(annual_rate: Decimal) -> Decimal:
    return (annual_rate / Decimal("365")).quantize(
        Decimal("0.0000000001"), rounding=ROUND_HALF_UP
    )

def _get_committed_balance(balances, denomination: str) -> Decimal:
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    return balances[key].net
```

---

## API 4.0 — Critical changes from 3.x

These differences cause failures with the installed SDK. Apply them automatically.

### 1. ZoneInfo required (not datetime.timezone)
```python
from zoneinfo import ZoneInfo
dt = datetime(2024, 1, 1, tzinfo=ZoneInfo("UTC"))   # CORRECT
dt = datetime(2024, 1, 1, tzinfo=timezone.utc)       # WRONG → InvalidSmartContractError
```

### 2. Phase is on BalanceCoordinate (key), not on Balance (value)
```python
# CORRECT — iterate items(), phase is on coord
for coord, balance in posting.balances().items():
    if coord.phase == Phase.COMMITTED:
        total += balance.net

# WRONG — Balance has no .phase attribute
for balance in posting.balances().values():
    if balance.phase == Phase.COMMITTED:   # AttributeError
```

### 3. Rejection not Rejected, return not raise
```python
# CORRECT API 4.0
return PrePostingHookResult(
    rejection=Rejection(
        message="Insufficient funds",
        reason_code=RejectionReason.INSUFFICIENT_FUNDS,
    )
)

# WRONG — API 3.x pattern
raise Rejected("Insufficient funds", reason_code=RejectedReason.INSUFFICIENT_FUNDS)
```

### 4. CustomInstruction has no client_transaction_id
```python
# CORRECT — use instruction_details for traceability
CustomInstruction(
    postings=[...],
    instruction_details={
        "description": "Monthly interest accrual",
        "hook_execution_id": str(vault.get_hook_execution_id()),
    },
)

# WRONG — doesn't exist in API 4.0
CustomInstruction(postings=[...], client_transaction_id="APPLY_INTEREST_123")
```

### 5. PrePostingHookArguments requires client_transactions
```python
# CORRECT
PrePostingHookArguments(
    effective_datetime=dt,
    posting_instructions=[posting],
    client_transactions={},    # ← required in API 4.0
)
```

### 6. get_balances_observation not get_balance_timeseries
```python
# CORRECT API 4.0
balances = vault.get_balances_observation(fetcher_id="live_balances").balances

# WRONG — API 3.x pattern
balances = vault.get_balance_timeseries().latest()
```

### 7. Derived parameters — `Parameter(derived=True)`, NOT `DerivedParameter`

`DerivedParameter` does NOT exist in the installed SDK (`ImportError`).
Derived parameters are declared inside the regular `parameters` list with `derived=True`.
Their computed values are returned by `derived_parameter_hook`.

```python
# CORRECT — verified against installed contracts_api
parameters = [
    ...
    Parameter(
        name="accrued_interest",
        shape=NumberShape(),
        level=ParameterLevel.INSTANCE,
        derived=True,
        display_name="Accrued Interest",
    ),
]

def derived_parameter_hook(vault, hook_arguments):
    return DerivedParameterHookResult(
        parameters_return_value={"accrued_interest": accrued}
    )

# WRONG — DerivedParameter does not exist in this SDK
from contracts_api import DerivedParameter          # ImportError
derived_parameters = [DerivedParameter(...)]        # NameError
```

### 8. `DateShape` inside `OptionalShape` — value is `datetime`, not `date`

`OptionalValue` only accepts `Union[Decimal, str, datetime, UnionItemValue, int]`.
Passing a `date` object raises `StrongTypingError`. `opt.value` therefore returns a
`datetime`; call `.date()` on it to get a `date` for comparisons.

```python
# CORRECT — opt_maturity.value is datetime; .date() extracts date
opt_maturity = vault.get_parameter_timeseries(name="maturity_date").latest()
if opt_maturity.is_set():
    maturity_date  = opt_maturity.value          # datetime
    effective_date = hook_arguments.effective_datetime.date()   # date
    if maturity_date.date() <= effective_date:   # date <= date ✅
        raise ValueError("maturity_date must be in the future.")

# In tests — ALWAYS pass datetime, never date, to OptionalValue
maturity_val = OptionalValue(datetime(2025, 6, 30, tzinfo=UTC))   # ✅
maturity_val = OptionalValue(date(2025, 6, 30))                    # ❌ StrongTypingError
```

### 9. `ParameterLevel.INSTANCE` non-optional shapes require `default_value`

The SDK raises `InvalidSmartContractError` at module load time if an INSTANCE parameter
uses a non-optional shape (e.g. plain `DateShape()`) and has no `default_value`.
Use `OptionalShape(shape=DateShape())` when the value can be unset at activation.

```python
# CORRECT — optional wrapper allows absence of value
Parameter(
    name="maturity_date",
    shape=OptionalShape(shape=DateShape()),
    level=ParameterLevel.INSTANCE,
    ...
)

# WRONG — SDK raises InvalidSmartContractError at import time
Parameter(
    name="maturity_date",
    shape=DateShape(),          # non-optional, no default_value
    level=ParameterLevel.INSTANCE,
    ...                         # ❌ InvalidSmartContractError
)
```

---

## Contract template (API 4.0)

```python
from contracts_api import (
    ActivationHookArguments, ActivationHookResult,
    BalanceCoordinate, BalanceDefaultDict,
    CustomInstruction, DenominationShape, EndOfMonthSchedule,
    NumberShape, Parameter, ParameterLevel, Phase, Posting,
    PostingInstructionsDirective, PostPostingHookArguments,
    PostPostingHookResult, PrePostingHookArguments, PrePostingHookResult,
    Rejection, RejectionReason, ScheduledEvent,
    ScheduledEventHookArguments, ScheduledEventHookResult,
    SmartContractEventType, Tside,
)
from decimal import Decimal, ROUND_HALF_UP

api          = "4.0.0"
version      = "1.0.0"
display_name = "Product Name"
summary      = "One-line summary"
description  = "Full description"
tside        = Tside.LIABILITY
supported_denominations = ["GBP"]

DEFAULT_ADDRESS = "DEFAULT"
DEFAULT_ASSET   = "COMMERCIAL_BANK_MONEY"

parameters = [
    Parameter(
        name="interest_rate",
        shape=NumberShape(min_value=Decimal("0"), max_value=Decimal("1"),
                          step=Decimal("0.0001")),
        level=ParameterLevel.TEMPLATE,
        display_name="Annual Interest Rate",
        default_value=Decimal("0.05"),
    ),
    Parameter(
        name="denomination",
        shape=DenominationShape(),
        level=ParameterLevel.INSTANCE,
        display_name="Denomination",
        default_value="GBP",
    ),
]

event_types = []
event_types_groups = []
```

## Hook signatures (API 4.0)

```python
def activation_hook(vault, hook_arguments: ActivationHookArguments) -> ActivationHookResult:
    return ActivationHookResult(scheduled_events_return_value={})


def pre_posting_hook(vault, hook_arguments: PrePostingHookArguments) -> PrePostingHookResult:
    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    balances     = vault.get_balances_observation(fetcher_id="live_balances").balances
    current      = _get_committed_balance(balances, denomination)

    # Phase is on the key (BalanceCoordinate), not on the Balance value
    posting_effect = Decimal("0")
    for posting in hook_arguments.posting_instructions:
        for coord, balance in posting.balances().items():
            if coord.phase == Phase.COMMITTED:
                posting_effect += balance.net

    if current + posting_effect < Decimal("0"):
        return PrePostingHookResult(
            rejection=Rejection(
                message=f"Insufficient funds: balance {current} {denomination}",
                reason_code=RejectionReason.INSUFFICIENT_FUNDS,
            )
        )
    return PrePostingHookResult()


def post_posting_hook(vault, hook_arguments: PostPostingHookArguments) -> PostPostingHookResult:
    return PostPostingHookResult(posting_instructions_directives=[])


def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    return ScheduledEventHookResult(
        posting_instructions_directives=[],
        update_account_event_type_directives=[],
    )
```

## Internal transfer pattern (API 4.0)

```python
# No client_transaction_id — use instruction_details instead
custom_instruction = CustomInstruction(
    postings=[
        Posting(credit=True,  amount=amount, denomination=denomination,
                account_id=vault.account_id, account_address=ACCRUED_INTEREST,
                asset=DEFAULT_ASSET, phase=Phase.COMMITTED),
        Posting(credit=False, amount=amount, denomination=denomination,
                account_id=vault.account_id, account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET, phase=Phase.COMMITTED),
    ],
    instruction_details={
        "description": "Monthly interest accrual",
        "hook_execution_id": str(vault.get_hook_execution_id()),
    },
)
```

## Test pattern (verified with contracts_api SDK)

```python
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo   # NOT datetime.timezone
from contracts_api import (
    Balance, BalanceCoordinate, BalanceDefaultDict, Phase,
    PrePostingHookArguments, ScheduledEventHookArguments,
    ActivationHookArguments, RejectionReason,
)

UTC          = ZoneInfo("UTC")
DEFAULT_DATE = datetime(2024, 1, 28, tzinfo=UTC)

def make_balance_dict(amount, denomination="GBP"):
    balances = BalanceDefaultDict()
    key = BalanceCoordinate(account_address="DEFAULT",
                             asset="COMMERCIAL_BANK_MONEY",
                             denomination=denomination,
                             phase=Phase.COMMITTED)
    credit = amount if amount >= 0 else Decimal("0")
    debit  = Decimal("0") if amount >= 0 else abs(amount)
    balances[key] = Balance(net=amount, credit=credit, debit=debit)
    return balances

def make_vault(balance=Decimal("1000"), interest_rate=Decimal("0.05")):
    vault = MagicMock()
    vault.account_id = "test_account_001"
    vault.get_parameter_timeseries.side_effect = lambda name: (
        MagicMock(latest=MagicMock(return_value=interest_rate))
        if name == "interest_rate"
        else MagicMock(latest=MagicMock(return_value="GBP"))
    )
    obs = MagicMock()
    obs.balances = make_balance_dict(balance)
    vault.get_balances_observation.return_value = obs
    vault.get_hook_execution_id.return_value = "test-hook-id"
    return vault

# PrePostingHookArguments — client_transactions required in API 4.0
args = PrePostingHookArguments(
    effective_datetime=DEFAULT_DATE,
    posting_instructions=[posting],
    client_transactions={},
)

# ScheduledEventHookArguments — only effective_datetime + event_type
args = ScheduledEventHookArguments(
    effective_datetime=DEFAULT_DATE,
    event_type="INTEREST_ACCRUAL",
)
```

---

## OpenSpec workflow

```bash
os-stack vault-smart-contracts    # activate stack
os-agent claude-code              # or copilot

os-enrich KAN-15                  # enriches ticket with hooks + params
os-enrich-apply KAN-15
os-plan KAN-15                    # generates plan in ai-specs/changes/
os-develop KAN-15                 # creates branch + scaffold

os-vault-test                     # run 18 tests locally with SDK
os-vault-test --coverage          # coverage ≥ 90% required before PR

os-vault-simulate contracts/<product>.py \
    "2024-01-01T00:00:00Z" "2024-04-01T00:00:00Z" \
    '{"interest_rate": "0.05"}'
os-vault-deploy contracts/<product>.py <product_id> "<display name>"
os-vault-account <product_version_id> <customer_id>
os-vault-balances <account_id>

os-commit KAN-15
os-review 1 && os-review-apply 1
```

## Standards

- `os-vault-test --coverage` must pass (≥ 90%) before any PR is opened
- Always `Decimal` — never `float` for monetary values
- Contract file: `contracts/<product_name>.py` (snake_case)
- Test file: `tests/test_<product_name>.py`
- API version: `4.0.0`
- All balance reads use `BalanceCoordinate` explicitly
- Phase is always read from `BalanceCoordinate` (key), never from `Balance` (value)
- `instruction_details` carries traceability — no `client_transaction_id`
- Only `contracts_api` and `decimal` imports allowed in contract code