# tests/test_fixed_term_deposit.py
# API 4.0 — Fixed-Term Deposit unit tests

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from contracts_api import (
    ActivationHookArguments,
    Balance,
    BalanceCoordinate,
    BalanceDefaultDict,
    DerivedParameterHookArguments,
    OptionalValue,
    Phase,
    PostPostingHookArguments,
    PrePostingHookArguments,
    RejectionReason,
    ScheduledEventHookArguments,
    UnionItemValue,
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import contracts.fixed_term_deposit as contract

UTC           = ZoneInfo("UTC")
DEFAULT_DENOM = "GBP"
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"

ACTIVATION_DATE  = datetime(2024, 1, 15, tzinfo=UTC)
FUTURE_MATURITY  = datetime(2025, 6, 30, tzinfo=UTC)
TODAY_MATURITY   = datetime(2024, 1, 15, tzinfo=UTC)
PAST_MATURITY    = datetime(2024, 1, 14, tzinfo=UTC)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_balance_dict(
    default_balance: Decimal = Decimal("0"),
    accrued_balance: Decimal = Decimal("0"),
    denomination: str = DEFAULT_DENOM,
) -> BalanceDefaultDict:
    balances = BalanceDefaultDict()
    for address, amount in [
        ("DEFAULT", default_balance),
        ("ACCRUED_INTEREST", accrued_balance),
    ]:
        key = BalanceCoordinate(
            account_address=address,
            asset=DEFAULT_ASSET,
            denomination=denomination,
            phase=Phase.COMMITTED,
        )
        credit = amount if amount >= 0 else Decimal("0")
        debit  = Decimal("0") if amount >= 0 else abs(amount)
        balances[key] = Balance(net=amount, credit=credit, debit=debit)
    return balances


def make_vault(
    default_balance: Decimal = Decimal("0"),
    accrued_balance: Decimal = Decimal("0"),
    denomination: str = DEFAULT_DENOM,
    annual_interest_rate: Decimal = Decimal("0.05"),
    maturity_date=FUTURE_MATURITY,
    allow_early_closure: str = "false",
    early_closure_penalty_rate: Decimal = Decimal("0.20"),
) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "test_ftd_account"

    # maturity_date is a date object; None simulates an unset OptionalShape parameter
    maturity_val      = OptionalValue(maturity_date) if maturity_date is not None else OptionalValue(None)
    early_closure_val = OptionalValue(UnionItemValue(allow_early_closure))

    param_map = {
        "denomination":             denomination,
        "annual_interest_rate":     annual_interest_rate,
        "maturity_date":            maturity_val,
        "allow_early_closure":      early_closure_val,
        "early_closure_penalty_rate": early_closure_penalty_rate,
    }

    vault.get_parameter_timeseries.side_effect = lambda name: MagicMock(
        latest=MagicMock(return_value=param_map.get(name, MagicMock()))
    )

    obs = MagicMock()
    obs.balances = make_balance_dict(default_balance, accrued_balance, denomination)
    vault.get_balances_observation.return_value = obs
    vault.get_hook_execution_id.return_value = "test-hook-exec-id"
    return vault


def make_posting(
    amount: Decimal,
    credit: bool = True,
    denomination: str = DEFAULT_DENOM,
) -> MagicMock:
    """Create a mock posting instruction with a DEFAULT address balance entry."""
    pi = MagicMock()
    pi.denomination = denomination
    key = BalanceCoordinate(
        account_address="DEFAULT",
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    net        = amount if credit else -amount
    credit_amt = amount if credit else Decimal("0")
    debit_amt  = Decimal("0") if credit else amount
    bal_dict   = BalanceDefaultDict()
    bal_dict[key] = Balance(net=net, credit=credit_amt, debit=debit_amt)
    pi.balances.return_value = bal_dict
    return pi


def make_pre_posting_args(posting) -> PrePostingHookArguments:
    return PrePostingHookArguments(
        effective_datetime=ACTIVATION_DATE,
        posting_instructions=[posting],
        client_transactions={},
    )


def make_scheduled_args(event_type: str, dt: datetime = ACTIVATION_DATE) -> ScheduledEventHookArguments:
    return ScheduledEventHookArguments(
        effective_datetime=dt,
        event_type=event_type,
    )


def make_post_posting_args() -> PostPostingHookArguments:
    return PostPostingHookArguments(
        effective_datetime=ACTIVATION_DATE,
        posting_instructions=[],
        client_transactions={},
    )


# ── 1. Activation tests ────────────────────────────────────────────────────────

class TestActivationHook:

    def test_activation_valid_future_maturity(self):
        vault  = make_vault(maturity_date=FUTURE_MATURITY)
        args   = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)
        result = contract.activation_hook(vault, args)

        assert contract.DAILY_ACCRUAL  in result.scheduled_events_return_value
        assert contract.MATURITY_EVENT in result.scheduled_events_return_value

    def test_activation_registers_both_schedules(self):
        vault  = make_vault(maturity_date=FUTURE_MATURITY)
        args   = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)
        result = contract.activation_hook(vault, args)

        events = result.scheduled_events_return_value
        assert events[contract.DAILY_ACCRUAL].expression  is not None
        assert events[contract.MATURITY_EVENT].expression is not None

    def test_activation_rejects_maturity_today(self):
        vault = make_vault(maturity_date=TODAY_MATURITY)
        args  = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)

        with pytest.raises(ValueError):
            contract.activation_hook(vault, args)

    def test_activation_rejects_maturity_past(self):
        vault = make_vault(maturity_date=PAST_MATURITY)
        args  = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)

        with pytest.raises(ValueError):
            contract.activation_hook(vault, args)

    def test_activation_rejects_unset_maturity_date(self):
        """Activation must fail when maturity_date is not provided."""
        vault = make_vault(maturity_date=None)
        args  = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)

        with pytest.raises(ValueError):
            contract.activation_hook(vault, args)


# ── 2. Pre-posting — deposits ──────────────────────────────────────────────────

class TestPrePostingDeposits:

    def test_initial_deposit_accepted(self):
        vault   = make_vault(default_balance=Decimal("0"))
        posting = make_posting(Decimal("1000"), credit=True)
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is None

    def test_second_deposit_rejected(self):
        vault   = make_vault(default_balance=Decimal("1000"))
        posting = make_posting(Decimal("500"), credit=True)
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_wrong_denomination_rejected(self):
        vault   = make_vault(denomination="GBP")
        posting = make_posting(Decimal("500"), credit=True, denomination="USD")
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.WRONG_DENOMINATION


# ── 3. Pre-posting — withdrawals ───────────────────────────────────────────────

class TestPrePostingWithdrawals:

    def test_withdrawal_before_maturity_rejected(self):
        vault   = make_vault(default_balance=Decimal("1000"), allow_early_closure="false")
        posting = make_posting(Decimal("100"), credit=False)
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_zero_amount_posting_accepted(self):
        vault   = make_vault(default_balance=Decimal("1000"))
        posting = make_posting(Decimal("0"), credit=False)
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is None


# ── 4. Daily accrual ───────────────────────────────────────────────────────────

class TestDailyAccrual:

    def _args(self, dt=ACTIVATION_DATE):
        return make_scheduled_args(contract.DAILY_ACCRUAL, dt)

    def test_daily_accrual_standard_rate(self):
        """5% AER on £1000 = 1000 * 0.05 / 365 = £0.14/day (ROUND_HALF_UP)"""
        vault  = make_vault(default_balance=Decimal("1000"), annual_interest_rate=Decimal("0.05"))
        result = contract.scheduled_event_hook(vault, self._args())

        assert len(result.posting_instructions_directives) == 1
        postings = result.posting_instructions_directives[0].posting_instructions[0].postings
        accrual_posting = next(p for p in postings if p.credit and p.account_address == "ACCRUED_INTEREST")
        assert accrual_posting.amount == Decimal("0.14")

    def test_daily_accrual_zero_rate(self):
        """0% AER produces no accrual instruction."""
        vault  = make_vault(default_balance=Decimal("1000"), annual_interest_rate=Decimal("0"))
        result = contract.scheduled_event_hook(vault, self._args())

        assert len(result.posting_instructions_directives) == 0

    def test_daily_accrual_zero_balance(self):
        """No posting generated when principal is zero."""
        vault  = make_vault(default_balance=Decimal("0"))
        result = contract.scheduled_event_hook(vault, self._args())

        assert len(result.posting_instructions_directives) == 0

    def test_daily_accrual_leap_year(self):
        """Feb 29 date: formula still divides by 365 (not 366)."""
        leap_dt = datetime(2024, 2, 29, tzinfo=UTC)
        vault   = make_vault(default_balance=Decimal("1000"), annual_interest_rate=Decimal("0.05"))
        result  = contract.scheduled_event_hook(vault, self._args(dt=leap_dt))

        postings = result.posting_instructions_directives[0].posting_instructions[0].postings
        accrual  = next(p for p in postings if p.credit and p.account_address == "ACCRUED_INTEREST")
        # 1000 * (0.05 / 365) rounded to 2dp = 0.14 — same regardless of leap year
        assert accrual.amount == Decimal("0.14")

    def test_daily_accrual_uses_decimal_precision(self):
        """Result is quantized to 2 decimal places with ROUND_HALF_UP."""
        vault  = make_vault(default_balance=Decimal("1000"), annual_interest_rate=Decimal("0.05"))
        result = contract.scheduled_event_hook(vault, self._args())

        postings = result.posting_instructions_directives[0].posting_instructions[0].postings
        accrual  = next(p for p in postings if p.credit and p.account_address == "ACCRUED_INTEREST")
        assert accrual.amount == accrual.amount.quantize(Decimal("0.01"))

    def test_daily_accrual_hook_id_in_instruction_details(self):
        """hook_execution_id stored in instruction_details (no client_transaction_id)."""
        vault = make_vault(default_balance=Decimal("1000"))
        vault.get_hook_execution_id.return_value = "exec-xyz-789"
        result = contract.scheduled_event_hook(vault, self._args())

        pi = result.posting_instructions_directives[0].posting_instructions[0]
        assert pi.instruction_details.get("hook_execution_id") == "exec-xyz-789"


# ── 5. Maturity disbursement ───────────────────────────────────────────────────

class TestMaturityEvent:

    def _args(self):
        return make_scheduled_args(contract.MATURITY_EVENT)

    def test_maturity_event_sweeps_accrued_interest(self):
        """ACCRUED_INTEREST balance is moved to DEFAULT."""
        vault  = make_vault(default_balance=Decimal("1000"), accrued_balance=Decimal("50"))
        result = contract.scheduled_event_hook(vault, self._args())

        assert len(result.posting_instructions_directives) == 1
        postings = result.posting_instructions_directives[0].posting_instructions[0].postings
        cr_default = next(p for p in postings if p.credit and p.account_address == "DEFAULT")
        assert cr_default.amount == Decimal("50")

    def test_maturity_event_zero_interest(self):
        """No CustomInstruction when accrued = 0."""
        vault  = make_vault(default_balance=Decimal("1000"), accrued_balance=Decimal("0"))
        result = contract.scheduled_event_hook(vault, self._args())

        assert len(result.posting_instructions_directives) == 0

    def test_maturity_payout_correct_total(self):
        """Both DEFAULT debit (ACCRUED_INTEREST) and credit (DEFAULT) have correct amount."""
        accrued = Decimal("38.36")
        vault   = make_vault(default_balance=Decimal("1000"), accrued_balance=accrued)
        result  = contract.scheduled_event_hook(vault, self._args())

        postings   = result.posting_instructions_directives[0].posting_instructions[0].postings
        dr_accrued = next(p for p in postings if not p.credit and p.account_address == "ACCRUED_INTEREST")
        cr_default = next(p for p in postings if p.credit and p.account_address == "DEFAULT")
        assert dr_accrued.amount == accrued
        assert cr_default.amount == accrued


# ── 6. Early closure ───────────────────────────────────────────────────────────

class TestEarlyClosure:

    def test_early_closure_disabled_rejects_withdrawal(self):
        """allow_early_closure=false → debit rejected."""
        vault   = make_vault(default_balance=Decimal("1000"), allow_early_closure="false")
        posting = make_posting(Decimal("1000"), credit=False)
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_early_closure_enabled_allows_withdrawal(self):
        """allow_early_closure=true → debit accepted."""
        vault   = make_vault(default_balance=Decimal("1000"), allow_early_closure="true")
        posting = make_posting(Decimal("1000"), credit=False)
        result  = contract.pre_posting_hook(vault, make_pre_posting_args(posting))

        assert result.rejection is None

    def test_early_closure_penalty_applied(self):
        """penalty_rate=0.20, accrued=£10 → net_payout=£8 to DEFAULT, £2 to PENALTY_INCOME."""
        vault  = make_vault(
            default_balance=Decimal("0"),
            accrued_balance=Decimal("10"),
            allow_early_closure="true",
            early_closure_penalty_rate=Decimal("0.20"),
        )
        result = contract.post_posting_hook(vault, make_post_posting_args())

        assert len(result.posting_instructions_directives) == 1
        cis        = result.posting_instructions_directives[0].posting_instructions
        postings   = cis[0].postings
        cr_default = next(p for p in postings if p.credit and p.account_address == "DEFAULT")
        assert cr_default.amount == Decimal("8.00")

        penalty_ci     = cis[1]
        cr_penalty     = next(p for p in penalty_ci.postings if p.credit)
        assert cr_penalty.account_address == "PENALTY_INCOME"
        assert cr_penalty.amount == Decimal("2.00")

    def test_early_closure_penalty_floor_zero(self):
        """penalty_rate=1.0, accrued=£1 → net_payout=0, ACCRUED_INTEREST still cleared."""
        vault  = make_vault(
            default_balance=Decimal("0"),
            accrued_balance=Decimal("1"),
            allow_early_closure="true",
            early_closure_penalty_rate=Decimal("1.00"),
        )
        result = contract.post_posting_hook(vault, make_post_posting_args())

        assert len(result.posting_instructions_directives) == 1
        postings   = result.posting_instructions_directives[0].posting_instructions[0].postings
        dr_accrued = next(p for p in postings if not p.credit and p.account_address == "ACCRUED_INTEREST")
        assert dr_accrued.amount == Decimal("1.00")

    def test_post_posting_noop_when_early_closure_disabled(self):
        """post_posting_hook returns empty directives when early closure is off."""
        vault  = make_vault(allow_early_closure="false")
        result = contract.post_posting_hook(vault, make_post_posting_args())

        assert len(result.posting_instructions_directives) == 0

    def test_post_posting_noop_when_principal_still_positive(self):
        """post_posting_hook is a no-op if principal > 0 after posting (partial withdrawal)."""
        vault  = make_vault(
            default_balance=Decimal("500"),
            accrued_balance=Decimal("10"),
            allow_early_closure="true",
        )
        result = contract.post_posting_hook(vault, make_post_posting_args())

        assert len(result.posting_instructions_directives) == 0

    def test_scheduled_event_hook_unknown_event_type(self):
        """Unknown event type returns empty result."""
        vault  = make_vault()
        args   = make_scheduled_args("UNKNOWN_EVENT")
        result = contract.scheduled_event_hook(vault, args)

        assert len(result.posting_instructions_directives) == 0

    def test_early_closure_accrued_interest_zeroed(self):
        """ACCRUED_INTEREST is fully zeroed after early closure regardless of penalty split."""
        vault  = make_vault(
            default_balance=Decimal("0"),
            accrued_balance=Decimal("10"),
            allow_early_closure="true",
            early_closure_penalty_rate=Decimal("0.20"),
        )
        result = contract.post_posting_hook(vault, make_post_posting_args())

        assert len(result.posting_instructions_directives) == 1
        all_postings = [
            p
            for ci in result.posting_instructions_directives[0].posting_instructions
            for p in ci.postings
        ]
        total_dr_accrued = sum(
            p.amount for p in all_postings
            if not p.credit and p.account_address == "ACCRUED_INTEREST"
        )
        assert total_dr_accrued == Decimal("10.00")


# ── 7. Derived parameters ──────────────────────────────────────────────────────

class TestDerivedParameters:

    def _args(self, dt: datetime) -> DerivedParameterHookArguments:
        return DerivedParameterHookArguments(effective_datetime=dt)

    def test_derived_accrued_interest_matches_balance(self):
        """accrued_interest derived param equals ACCRUED_INTEREST balance."""
        vault  = make_vault(accrued_balance=Decimal("25.50"))
        args   = self._args(ACTIVATION_DATE)
        result = contract.derived_parameter_hook(vault, args)

        assert result.parameters_return_value["accrued_interest"] == Decimal("25.50")

    def test_derived_days_to_maturity_correct(self):
        """Returns correct (maturity_date - today).days."""
        maturity = datetime(2024, 7, 15, tzinfo=UTC)
        today    = datetime(2024, 6, 15, tzinfo=UTC)
        vault    = make_vault(maturity_date=maturity)
        result   = contract.derived_parameter_hook(vault, self._args(today))

        assert result.parameters_return_value["days_to_maturity"] == 30

    def test_derived_days_to_maturity_at_maturity(self):
        """Returns 0 when effective_datetime is the maturity date."""
        maturity = datetime(2024, 6, 15, tzinfo=UTC)
        vault    = make_vault(maturity_date=maturity)
        result   = contract.derived_parameter_hook(vault, self._args(maturity))

        assert result.parameters_return_value["days_to_maturity"] == 0

    def test_derived_days_to_maturity_unset(self):
        """Returns 0 when maturity_date is not set."""
        vault  = make_vault(maturity_date=None)
        args   = self._args(ACTIVATION_DATE)
        result = contract.derived_parameter_hook(vault, args)

        assert result.parameters_return_value["days_to_maturity"] == 0
