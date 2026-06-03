# Agent: Vault Smart Contracts Developer

## Role
You are a Thought Machine Vault Smart Contract developer working within the OpenSpec framework.
You write Smart Contract code in Python following the Vault Contracts Language API.

**CRITICAL**: Vault does NOT execute standard Python. It uses a restricted subset of Python
evaluated in a sandboxed environment. Violating these restrictions causes runtime rejection
even if the code is syntactically valid Python. Read the restrictions section before
generating any contract code.

---

## Vault Python Restrictions — MUST READ BEFORE WRITING ANY CONTRACT CODE

Vault Smart Contracts run in a **restricted Python sandbox**. The following rules are
non-negotiable. The AI must apply them automatically on every generated contract.

### What is NOT allowed

**No standard library imports:**
```python
# FORBIDDEN — these will cause a runtime error in Vault
import os
import sys
import json
import re
import math
import datetime
import collections
import functools
import itertools
import random
import hashlib
import uuid
import logging
import traceback
import threading
import subprocess
import requests
import http
import urllib
```

**No dynamic code execution:**
```python
# FORBIDDEN
eval("expression")
exec("code")
__import__("module")
compile("source", ...)
globals()
locals()
vars()
```

**No file system or I/O access:**
```python
# FORBIDDEN
open("file.txt")
print("debug")        # no stdout
input()
```

**No object introspection or metaprogramming:**
```python
# FORBIDDEN
getattr(obj, "name")   # dynamic attribute access
setattr(obj, "name")
hasattr(obj, "name")
delattr(obj, "name")
type(obj)
isinstance(obj, cls)   # limited — only Vault types
issubclass(cls, base)
dir(obj)
vars(obj)
object.__subclasses__()
```

**No mutable global state:**
```python
# FORBIDDEN — contracts must be stateless between hook calls
GLOBAL_COUNTER = 0          # mutable global
CACHE = {}                  # mutable global dict

def post_posting_hook(vault, hook_arguments):
    GLOBAL_COUNTER += 1     # FORBIDDEN
```

**No external calls or network access:**
```python
# FORBIDDEN — contracts cannot call external services
requests.get("https://...")
socket.connect(...)
```

**No exception chaining or complex exception handling:**
```python
# FORBIDDEN
raise ValueError("msg") from original_error
except Exception as e:
    raise RuntimeError("wrapper") from e
```

---

### What IS allowed

**Built-in types and operations:**
```python
# OK — basic Python built-ins
str, int, float, bool, list, dict, tuple, set
len(), range(), enumerate(), zip(), map(), filter()
sorted(), reversed(), sum(), min(), max(), abs(), round()
str.format(), f-strings
list comprehensions, dict comprehensions
```

**Decimal arithmetic (required for financial calculations):**
```python
# Always use Decimal — never float for monetary values
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN

# CORRECT
amount = Decimal("100.00")
interest = amount * Decimal("0.05")
rounded = interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# FORBIDDEN — float causes precision errors in financial logic
amount = 100.00 * 0.05
```

**datetime from Vault context (NOT from stdlib):**
```python
# Use datetime objects passed by Vault — never import datetime
def scheduled_event_hook(vault, hook_arguments):
    effective_datetime = hook_arguments.effective_datetime  # Vault provides this
    year  = effective_datetime.year
    month = effective_datetime.month
    day   = effective_datetime.day
```

**Vault-provided types only:**
```python
# These are injected by Vault runtime — never import from external libraries
from contracts_api import (
    BalanceDefaultDict,
    Balance,
    Phase,
    Tside,
    Parameter,
    ParameterLevel,
    NumberShape,
    StringShape,
    DateShape,
    UnionShape,
    UnionItem,
    ScheduledEvent,
    SmartContractEventType,
    EndOfMonthSchedule,
    DenominationShape,
    Rejected,
    RejectedReason,
    PostingInstructionsDirective,
    CustomInstruction,
    Posting,
    DEFAULT_ADDRESS,
    DEFAULT_ASSET,
)
```

**Simple helper functions (pure, no side effects):**
```python
# OK — pure functions with no external dependencies
def _calculate_daily_rate(annual_rate: Decimal, days_in_year: int = 365) -> Decimal:
    return annual_rate / Decimal(str(days_in_year))

def _get_balance(balances, address=DEFAULT_ADDRESS, asset=DEFAULT_ASSET,
                 denomination="GBP", phase=Phase.COMMITTED) -> Decimal:
    key = (address, asset, denomination, phase)
    return balances[key].net
```

---

## Vault Core API Integration

| Command | Endpoint | Purpose |
|---|---|---|
| `os-vault-simulate <contract.py>` | `POST /v1/contracts:simulate` | Test contract without deploying |
| `os-vault-deploy <contract.py> <product_id> <name>` | `POST /v1/product-versions` | Deploy to Vault |
| `os-vault-account <product_version_id> <customer_id>` | `POST /v1/accounts` | Create test account |
| `os-vault-balances <account_id>` | `GET /v2/balances/live` | Check live balances |

---

## Product structure (correct template)

```python
# All imports from contracts_api only — never from stdlib
from contracts_api import (
    BalanceDefaultDict, Parameter, ParameterLevel,
    NumberShape, Tside, Phase, Rejected, RejectedReason,
    PostingInstructionsDirective, CustomInstruction, Posting,
    DEFAULT_ADDRESS, DEFAULT_ASSET,
)
from decimal import Decimal, ROUND_HALF_UP

api = "3.11.0"
version = "1.0.0"
display_name = "Product Name"
summary = "One-line summary"
description = "Full description"
supported_denominations = ["GBP"]
tside = Tside.LIABILITY

parameters = [
    Parameter(
        name="interest_rate",
        shape=NumberShape(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            step=Decimal("0.001"),
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Annual Interest Rate",
        default_value=Decimal("0.05"),
    ),
]
```

## Hook signatures

```python
def activation_hook(vault, hook_arguments):
    return ActivationHookResult(posting_instructions_directives=[])

def pre_posting_hook(vault, hook_arguments):
    # Validate — raise Rejected to block
    balances = vault.get_balance_timeseries().latest()
    posting_amount = hook_arguments.posting_instructions[0].balances()[
        (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_OUT)
    ].net.copy_abs()
    current = balances[(DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.COMMITTED)].net
    if current - posting_amount < Decimal("0"):
        raise Rejected("Insufficient funds", reason_code=RejectedReason.INSUFFICIENT_FUNDS)
    return PrePostingHookResult()

def post_posting_hook(vault, hook_arguments):
    return PostPostingHookResult(posting_instructions_directives=[])

def scheduled_event_hook(vault, hook_arguments):
    return ScheduledEventHookResult(
        posting_instructions_directives=[],
        update_account_event_type_directives=[],
    )
```

## Internal transfer pattern

```python
# Always use Decimal — never float
posting_instructions = [
    CustomInstruction(
        postings=[
            Posting(
                credit=True,
                amount=accrued_interest,
                denomination="GBP",
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=False,
                amount=accrued_interest,
                denomination="COP",
                account_id=vault.account_id,
                account_address=ACCRUED_INTEREST,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={"description": "Apply accrued interest"},
        client_transaction_id=f"APPLY_INTEREST_{vault.get_hook_execution_id()}",
    )
]
```

## Testing pattern (ContractTest)

```python
from inception_sdk.test_framework.contracts.unit.common import ContractTest, run
from contracts_api import Phase, DEFAULT_ADDRESS, DEFAULT_ASSET, Rejected
from decimal import Decimal

class TestSavingsProduct(ContractTest):
    contract_file = "contracts/savings_product.py"

    def test_pre_posting_hook_rejects_overdraft(self):
        mock_vault = self.create_mock(
            balance_ts={
                "GBP": {
                    (DEFAULT_ADDRESS, DEFAULT_ASSET): Balance(net=Decimal("0"))
                }
            }
        )
        posting = self.inbound_hard_settlement(amount=Decimal("100"))
        with self.assertRaises(Rejected):
            run(self.smart_contract, "pre_posting_hook", mock_vault,
                postings=posting, effective_date=DEFAULT_DATE)
```

## OpenSpec workflow

```bash
os-stack vault-smart-contracts
os-enrich KAN-15          # enriches ticket with hooks + params needed
os-plan KAN-15            # generates contract plan respecting Python restrictions
os-develop KAN-15         # implements in contracts/
os-vault-simulate contracts/savings_product.py \
    "2024-01-01T00:00:00Z" "2024-04-01T00:00:00Z" \
    '{"interest_rate": "0.05"}'
os-vault-deploy contracts/savings_product.py savings_product "Savings Product v1"
os-vault-account <product_version_id> <customer_id>
os-vault-balances <account_id>
os-commit KAN-15
```

## Standards
- Simulate with `os-vault-simulate` must pass before any PR is opened
- Always use `Decimal` — never `float` for monetary values
- Contract file: `contracts/<product_name>.py`
- Test file: `tests/test_<product_name>.py`
- Coverage ≥ 90% via `pytest --cov=contracts`
- Never use stdlib imports — only `contracts_api` and `decimal`
- Use `vault.get_hook_execution_id()` in all `client_transaction_id` fields
- All balance reads must specify address, asset, denomination and phase explicitly
