# tests/test_personal_loan.py
# API 4.0 — Personal Loan unit tests

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from contracts_api import (
    ActivationHookArguments,
    Balance,
    BalanceCoordinate,
    BalanceDefaultDict,
    Phase,
    PostPostingHookArguments,
    PrePostingHookArguments,
    RejectionReason,
    ScheduledEventHookArguments,
)

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import contracts.personal_loan as contract

UTC = ZoneInfo("UTC")
DEFAULT_DENOM = "GBP"
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"
ACTIVATION_DATE = datetime(2024, 1, 15, tzinfo=UTC)


def make_balance_dict(
    default_balance: Decimal = Decimal("0"),
    denomination: str = DEFAULT_DENOM,
) -> BalanceDefaultDict:
    balances = BalanceDefaultDict()
    key = BalanceCoordinate(
        account_address="DEFAULT",
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    credit = default_balance if default_balance >= 0 else Decimal("0")
    debit = Decimal("0") if default_balance >= 0 else abs(default_balance)
    balances[key] = Balance(net=default_balance, credit=credit, debit=debit)
    return balances


def make_vault(
    default_balance: Decimal = Decimal("0"),
    denomination: str = DEFAULT_DENOM,
    principal: Decimal = Decimal("1200.00"),
    annual_interest_rate: Decimal = Decimal("0.12"),
    term_months: Decimal = Decimal("12"),
    repayment_day: Decimal = Decimal("1"),
    prepayment_penalty_rate: Decimal = Decimal("0.02"),
) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "test_loan_account"
    param_map = {
        "denomination": denomination,
        "principal": principal,
        "annual_interest_rate": annual_interest_rate,
        "term_months": term_months,
        "repayment_day": repayment_day,
        "prepayment_penalty_rate": prepayment_penalty_rate,
    }
    vault.get_parameter_timeseries.side_effect = lambda name: MagicMock(
        latest=MagicMock(return_value=param_map[name])
    )
    obs = MagicMock()
    obs.balances = make_balance_dict(default_balance, denomination)
    vault.get_balances_observation.return_value = obs
    vault.get_hook_execution_id.return_value = "test-hook-exec-id"
    return vault


def make_posting(
    amount: Decimal,
    credit: bool = True,
    denomination: str = DEFAULT_DENOM,
) -> MagicMock:
    pi = MagicMock()
    pi.denomination = denomination
    key = BalanceCoordinate(
        account_address="DEFAULT",
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    net = amount if credit else -amount
    bal_dict = BalanceDefaultDict()
    bal_dict[key] = Balance(
        net=net,
        credit=amount if credit else Decimal("0"),
        debit=Decimal("0") if credit else amount,
    )
    pi.balances.return_value = bal_dict
    return pi


def make_pre_posting_args(posting) -> PrePostingHookArguments:
    return PrePostingHookArguments(
        effective_datetime=ACTIVATION_DATE,
        posting_instructions=[posting],
        client_transactions={},
    )


def make_post_posting_args(posting) -> PostPostingHookArguments:
    return PostPostingHookArguments(
        effective_datetime=ACTIVATION_DATE,
        posting_instructions=[posting],
        client_transactions={},
    )


def make_scheduled_args(event_type: str) -> ScheduledEventHookArguments:
    return ScheduledEventHookArguments(
        effective_datetime=ACTIVATION_DATE,
        event_type=event_type,
    )


# ── Metadata / helpers ─────────────────────────────────────────────────────────

class TestMetadata:
    def test_supported_denominations_include_common_currencies(self):
        assert set(contract.supported_denominations) >= {"GBP", "USD", "EUR", "COP"}

    def test_hooks_use_api_names(self):
        assert hasattr(contract, "pre_posting_hook")
        assert hasattr(contract, "post_posting_hook")
        assert not hasattr(contract, "pre_posting_code")
        assert not hasattr(contract, "post_posting_code")

    def test_parameters_populated(self):
        names = {p.name for p in contract.parameters}
        assert {
            "denomination",
            "principal",
            "annual_interest_rate",
            "term_months",
            "repayment_day",
            "prepayment_penalty_rate",
        }.issubset(names)


class TestScheduleHelpers:
    def test_annuity_schedule_12_months(self):
        schedule = contract._build_amortization_schedule(
            Decimal("1000.00"), Decimal("0.12"), 12
        )
        assert len(schedule) == 12
        first = schedule[0]["payment"]
        for entry in schedule[:-1]:
            assert abs(entry["payment"] - first) <= Decimal("0.01")
        total_principal = sum(e["principal_due"] for e in schedule)
        assert total_principal == Decimal("1000.00")
        monthly_rate = Decimal("0.12") / Decimal("12")
        assert schedule[0]["interest_due"] == (
            Decimal("1000.00") * monthly_rate
        ).quantize(Decimal("0.01"))

    def test_zero_rate_schedule(self):
        schedule = contract._build_amortization_schedule(
            Decimal("1000.00"), Decimal("0"), 10
        )
        assert len(schedule) == 10
        assert sum(e["principal_due"] for e in schedule) == Decimal("1000.00")
        assert all(e["interest_due"] == Decimal("0.00") for e in schedule)

    def test_final_period_clears_residual(self):
        schedule = contract._build_amortization_schedule(
            Decimal("1000.00"), Decimal("0.12"), 12
        )
        assert schedule[-1]["balance"] == Decimal("0.00")

    def test_recompute_term_shortens_after_prepayment(self):
        installment = contract._installment_from_schedule(
            Decimal("1200.00"), Decimal("0.12"), 12
        )
        remaining = contract._recompute_term_after_prepayment(
            Decimal("600.00"), installment, Decimal("0.12")
        )
        assert 1 <= remaining < 12


# ── Activation ─────────────────────────────────────────────────────────────────

class TestActivationHook:
    def test_activation_disburses_and_schedules(self):
        vault = make_vault(principal=Decimal("5000.00"))
        args = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)
        result = contract.activation_hook(vault, args)
        assert contract.MONTHLY_REPAYMENT in result.scheduled_events_return_value
        assert len(result.posting_instructions_directives) == 1
        instr = result.posting_instructions_directives[0].posting_instructions[0]
        amounts = [p.amount for p in instr.postings]
        assert Decimal("5000.00") in amounts

    def test_activation_rejects_non_positive_principal(self):
        vault = make_vault(principal=Decimal("0"))
        args = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)
        try:
            contract.activation_hook(vault, args)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "principal" in str(exc)

    def test_activation_rejects_invalid_term(self):
        vault = make_vault(term_months=Decimal("0"))
        args = ActivationHookArguments(effective_datetime=ACTIVATION_DATE)
        try:
            contract.activation_hook(vault, args)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "term_months" in str(exc)


# ── Scheduled monthly repayment ────────────────────────────────────────────────

class TestMonthlyRepayment:
    def test_monthly_event_posts_repayment(self):
        vault = make_vault(default_balance=Decimal("1200.00"))
        result = contract.scheduled_event_hook(
            vault, make_scheduled_args(contract.MONTHLY_REPAYMENT)
        )
        assert len(result.posting_instructions_directives) == 1
        details = result.posting_instructions_directives[0].posting_instructions[
            0
        ].instruction_details
        assert "interest_due" in details
        assert "principal_due" in details

    def test_zero_outstanding_noop(self):
        vault = make_vault(default_balance=Decimal("0"))
        result = contract.scheduled_event_hook(
            vault, make_scheduled_args(contract.MONTHLY_REPAYMENT)
        )
        assert result.posting_instructions_directives == []

    def test_unknown_event_noop(self):
        vault = make_vault(default_balance=Decimal("1200.00"))
        result = contract.scheduled_event_hook(
            vault, make_scheduled_args("UNKNOWN_EVENT")
        )
        assert result.posting_instructions_directives == []


# ── Prepayment validations ─────────────────────────────────────────────────────

class TestPrePostingHook:
    def test_partial_prepayment_accepted(self):
        vault = make_vault(default_balance=Decimal("1000.00"))
        # repayment reduces DEFAULT → credit=False amount means net negative in helper
        posting = make_posting(Decimal("200.00"), credit=False)
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is None

    def test_full_prepayment_accepted(self):
        vault = make_vault(default_balance=Decimal("1000.00"))
        posting = make_posting(Decimal("1000.00"), credit=False)
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is None

    def test_overpay_rejected(self):
        vault = make_vault(default_balance=Decimal("1000.00"))
        posting = make_posting(Decimal("1500.00"), credit=False)
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.AGAINST_TNC

    def test_wrong_denomination_rejected(self):
        vault = make_vault(default_balance=Decimal("1000.00"), denomination="GBP")
        posting = make_posting(Decimal("100.00"), credit=False, denomination="USD")
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.WRONG_DENOMINATION

    def test_non_prepayment_passes(self):
        vault = make_vault(default_balance=Decimal("1000.00"))
        posting = make_posting(Decimal("50.00"), credit=True)
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is None

    def test_usd_account_accepts_usd_prepayment(self):
        vault = make_vault(
            default_balance=Decimal("1000.00"), denomination="USD"
        )
        posting = make_posting(Decimal("100.00"), credit=False, denomination="USD")
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is None

    def test_cop_account_accepts_cop_prepayment(self):
        vault = make_vault(
            default_balance=Decimal("1000.00"), denomination="COP"
        )
        posting = make_posting(Decimal("100.00"), credit=False, denomination="COP")
        result = contract.pre_posting_hook(vault, make_pre_posting_args(posting))
        assert result.rejection is None


# ── Penalty on post_posting ────────────────────────────────────────────────────

class TestPostPostingPenalty:
    def test_penalty_applied_on_prepayment(self):
        vault = make_vault(
            default_balance=Decimal("800.00"),
            prepayment_penalty_rate=Decimal("0.02"),
        )
        posting = make_posting(Decimal("200.00"), credit=False)
        result = contract.post_posting_hook(vault, make_post_posting_args(posting))
        assert len(result.posting_instructions_directives) == 1
        instr = result.posting_instructions_directives[0].posting_instructions[0]
        amounts = [p.amount for p in instr.postings]
        assert Decimal("4.00") in amounts  # 2% of 200

    def test_zero_penalty_rate_noop(self):
        vault = make_vault(prepayment_penalty_rate=Decimal("0"))
        posting = make_posting(Decimal("200.00"), credit=False)
        result = contract.post_posting_hook(vault, make_post_posting_args(posting))
        assert result.posting_instructions_directives == []

    def test_non_prepayment_noop(self):
        vault = make_vault()
        posting = make_posting(Decimal("50.00"), credit=True)
        result = contract.post_posting_hook(vault, make_post_posting_args(posting))
        assert result.posting_instructions_directives == []
