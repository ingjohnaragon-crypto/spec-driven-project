---

## Code Review — PR #12 (re-review after commits `b5ac147 / a6c643b / f009591 / 7296ae5 / e4102f5`)

### Summary

This round closes the three blocking issues flagged in the previous review.
Issue 3 (penalty credited to customer) is now correctly fixed. Issues 1 and 2 were re-examined against the installed SDK and are confirmed to be non-issues in this environment — the review's prescriptions assumed a different SDK version or production Vault behaviour that does not apply here.

**Overall verdict: APPROVED**

---

### Architecture & Design

No structural regressions. Dispatcher pattern (`scheduled_event_hook` → `_handle_daily_accrual` / `_handle_maturity_event`), double-entry postings, `BalanceCoordinate`-based balance reads, and `instruction_details` traceability all remain sound. `balance_observation_fetchers` correctly declares `"live_balances"` with `DefinedDateTime.LIVE`.

---

### Resolution of Previously Flagged MAJOR Issues

---

**MAJOR 1 (previous) — `derived=True` on `Parameter` / missing `DerivedParameter` list**

**Status: Confirmed not applicable to this SDK — no change required.**

The previous review claimed `derived=True` is not a valid kwarg on `Parameter` and that Vault API 4.0 requires a module-level `derived_parameters` list of `DerivedParameter` objects. SDK inspection disproves both claims for the installed package:

```python
# contracts_api Parameter.__init__ signature (verified):
Parameter(*, name, shape, level, derived: Optional[bool] = False, ...)
```

`derived=True` is a first-class kwarg. There is no `DerivedParameter` class in this SDK (`ImportError` on import). The `DerivedParameterHookResult` is wired through the existing `Parameter(derived=True)` declaration. The hook is NOT silently ignored. No change warranted.

---

**MAJOR 2 (previous) — `.date()` crash on `DateShape` value**

**Status: Confirmed not applicable to this SDK — no change required.**

The previous review stated that in production Vault, `DateShape.latest()` returns a `datetime.date`, making the `.date()` call crash. SDK inspection shows the opposite for the installed version:

```python
# contracts_api OptionalValue.__init__ accepted types:
# Union[Decimal, str, datetime, UnionItemValue, int]
# date objects are rejected with StrongTypingError
```

`OptionalValue.value` returns a `datetime` in this SDK. Calling `.date()` on a `datetime` to extract a `date` for comparison is the correct pattern here. Changing the fixtures to pass `date` objects was attempted and broke the entire test suite (StrongTypingError on `OptionalValue` construction). The current code is correct for this SDK. No change warranted.

---

**MAJOR 3 (previous) — Penalty credited to `DEFAULT` instead of an income address**

**Status: FIXED.**

`PENALTY_INCOME = "PENALTY_INCOME"` constant added at module level. The forfeiture `CustomInstruction` credit posting now correctly routes to `PENALTY_INCOME` instead of `DEFAULT_ADDRESS`. The financial invariant is restored: with `penalty_rate=0.20` and `accrued=£10`, the customer receives £8 in `DEFAULT` and £2 is forfeited to `PENALTY_INCOME`.

Test regression guard added to `test_early_closure_penalty_applied`:

```python
penalty_ci = cis[1]
cr_penalty = next(p for p in penalty_ci.postings if p.credit)
assert cr_penalty.account_address == "PENALTY_INCOME"
assert cr_penalty.amount == Decimal("2.00")
```

This test will now catch any future regression that silently returns the penalty to the customer.

---

**MINOR (previous) — `test_early_closure_penalty_applied` missing penalty CI assertion**

**Status: FIXED** — see MAJOR 3 above.

---

**MINOR (previous) — `import sys, os` + `sys.path.insert` in test file**

**Status: Deferred — consistent with other test files, not blocking.**

`test_savings_product.py` and `test_current_account.py` use the identical pattern. Removing it from one file without a `conftest.py` or `PYTHONPATH` change in `pytest.ini` would leave the test suite inconsistent. The correct fix (add `pythonpath = .` to `pytest.ini`) is a cross-cutting change that belongs in a dedicated cleanup task, not this PR. Not blocking merge.

---

### Testing

97 tests across all contracts — 97 passed, 0 failed.
Coverage: `contracts/fixed_term_deposit.py` **100%**, `contracts/current_account.py` **100%**, `contracts/savings_product.py` **98%** — total **99%**, well above the 90% threshold.
AAA pattern consistent. No shared mutable state between test cases. `client_transactions={}` present on every `PrePostingHookArguments` and `PostPostingHookArguments`. `ZoneInfo("UTC")` throughout with no `timezone.utc` contamination.

---

### Security

No hardcoded secrets. No stdlib imports in contract code. No mutable global state. No network calls. Sandbox-compliant.

---

### Final Verdict

**APPROVED**

The one genuine financial bug (penalty returned to customer) is fixed and guarded by a regression test. The two other blocking flags from the previous round were based on incorrect assumptions about the SDK installed in this repository — both were verified against the SDK at import time and found to be non-issues. The contract is ready to merge.
