# tests/test_savings_product.py
# API 4.0 — corrected for actual SDK signatures

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from contracts_api import (
    Balance,
    BalanceCoordinate,
    BalanceDefaultDict,
    Phase,
    PrePostingHookArguments,
    ScheduledEventHookArguments,
    ActivationHookArguments,
    RejectionReason,
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import contracts.savings_product as contract

UTC           = ZoneInfo("UTC")
DEFAULT_DATE  = datetime(2024, 1, 28, tzinfo=UTC)
DEFAULT_DENOM = "GBP"
DEFAULT_ADDRESS = "DEFAULT"
DEFAULT_ASSET   = "COMMERCIAL_BANK_MONEY"


def make_balance_dict(amount: Decimal,
                      denomination: str = DEFAULT_DENOM) -> BalanceDefaultDict:
    balances = BalanceDefaultDict()
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    credit = amount if amount >= 0 else Decimal("0")
    debit  = Decimal("0") if amount >= 0 else abs(amount)
    balances[key] = Balance(net=amount, credit=credit, debit=debit)
    return balances


def make_vault(balance: Decimal = Decimal("1000"),
               interest_rate: Decimal = Decimal("0.05"),
               denomination: str = DEFAULT_DENOM) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "test_account_001"
    vault.get_parameter_timeseries.side_effect = lambda name: (
        MagicMock(latest=MagicMock(return_value=interest_rate))
        if name == "interest_rate"
        else MagicMock(latest=MagicMock(return_value=denomination))
    )
    obs = MagicMock()
    obs.balances = make_balance_dict(balance, denomination)
    vault.get_balances_observation.return_value = obs
    vault.get_hook_execution_id.return_value = "test-hook-id-001"
    return vault


def make_posting_instruction(amount: Decimal,
                              credit: bool = False) -> MagicMock:
    """
    API 4.0: posting.balances() returns {BalanceCoordinate: Balance}.
    Phase is on the KEY (BalanceCoordinate), not on the Balance value.
    """
    pi  = MagicMock()
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=DEFAULT_DENOM,
        phase=Phase.COMMITTED,
    )
    net        = amount if credit else -amount
    credit_amt = amount if credit else Decimal("0")
    debit_amt  = Decimal("0") if credit else amount
    bal_dict   = BalanceDefaultDict()
    bal_dict[key] = Balance(net=net, credit=credit_amt, debit=debit_amt)
    pi.balances.return_value = bal_dict
    return pi


# ══════════════════════════════════════════════════════════════
# activation_hook
# ══════════════════════════════════════════════════════════════
class TestActivationHook:

    def test_creates_interest_accrual_schedule(self):
        vault = make_vault()
        args  = ActivationHookArguments(effective_datetime=DEFAULT_DATE)

        result = contract.activation_hook(vault, args)

        assert "INTEREST_ACCRUAL" in result.scheduled_events_return_value

    def test_schedule_start_matches_effective_date(self):
        vault  = make_vault()
        args   = ActivationHookArguments(effective_datetime=DEFAULT_DATE)
        result = contract.activation_hook(vault, args)

        schedule = result.scheduled_events_return_value["INTEREST_ACCRUAL"]
        assert schedule.start_datetime == DEFAULT_DATE


# ══════════════════════════════════════════════════════════════
# pre_posting_hook
# ══════════════════════════════════════════════════════════════
class TestPrePostingHook:

    def _make_args(self, posting) -> PrePostingHookArguments:
        return PrePostingHookArguments(
            effective_datetime=DEFAULT_DATE,
            posting_instructions=[posting],
            client_transactions={},
        )

    def test_allows_deposit(self):
        vault   = make_vault(balance=Decimal("500"))
        posting = make_posting_instruction(Decimal("100"), credit=True)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None

    def test_allows_withdrawal_within_balance(self):
        vault   = make_vault(balance=Decimal("500"))
        posting = make_posting_instruction(Decimal("300"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None

    def test_rejects_overdraft(self):
        vault   = make_vault(balance=Decimal("100"))
        posting = make_posting_instruction(Decimal("500"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.INSUFFICIENT_FUNDS

    def test_rejects_one_cent_over_balance(self):
        vault   = make_vault(balance=Decimal("100"))
        posting = make_posting_instruction(Decimal("100.01"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is not None

    def test_allows_exact_balance_withdrawal(self):
        vault   = make_vault(balance=Decimal("100"))
        posting = make_posting_instruction(Decimal("100"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None

    def test_rejection_message_contains_amounts(self):
        vault   = make_vault(balance=Decimal("50"))
        posting = make_posting_instruction(Decimal("200"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert "50"  in result.rejection.message
        assert "200" in result.rejection.message


# ══════════════════════════════════════════════════════════════
# scheduled_event_hook
# ══════════════════════════════════════════════════════════════
class TestScheduledEventHook:

    def _make_args(self, event_type: str = "INTEREST_ACCRUAL"):
        return ScheduledEventHookArguments(
            effective_datetime=DEFAULT_DATE,
            event_type=event_type,
        )

    def test_accrues_interest_on_positive_balance(self):
        vault  = make_vault(balance=Decimal("10000"), interest_rate=Decimal("0.05"))
        result = contract.scheduled_event_hook(vault, self._make_args())

        assert len(result.posting_instructions_directives) == 1

    def test_interest_amount_is_correct(self):
        """£10,000 × 5% / 365 × 28 = £38.36"""
        vault  = make_vault(balance=Decimal("10000"), interest_rate=Decimal("0.05"))
        result = contract.scheduled_event_hook(vault, self._make_args())

        pis = result.posting_instructions_directives[0].posting_instructions
        credit_posting = next(
            p for p in pis[0].postings
            if p.credit and p.account_address == "ACCRUED_INTEREST"
        )
        assert credit_posting.amount == Decimal("38.36")

    def test_no_postings_on_zero_balance(self):
        vault  = make_vault(balance=Decimal("0"))
        result = contract.scheduled_event_hook(vault, self._make_args())

        assert len(result.posting_instructions_directives) == 0

    def test_ignores_unknown_event_type(self):
        vault  = make_vault()
        result = contract.scheduled_event_hook(vault, self._make_args("UNKNOWN_EVENT"))

        assert len(result.posting_instructions_directives) == 0

    def test_hook_id_stored_in_instruction_details(self):
        """API 4.0: no client_transaction_id on CustomInstruction.
        Hook execution ID is stored in instruction_details instead."""
        vault = make_vault(balance=Decimal("1000"))
        vault.get_hook_execution_id.return_value = "exec-abc-123"

        result = contract.scheduled_event_hook(vault, self._make_args())
        pi     = result.posting_instructions_directives[0].posting_instructions[0]

        assert pi.instruction_details.get("hook_execution_id") == "exec-abc-123"


# ══════════════════════════════════════════════════════════════
# Helper unit tests
# ══════════════════════════════════════════════════════════════
class TestHelpers:

    def test_daily_rate_from_annual(self):
        daily    = contract._calculate_daily_rate(Decimal("0.05"))
        expected = (Decimal("0.05") / Decimal("365")).quantize(Decimal("0.0000000001"))
        assert daily == expected

    def test_interest_calculation_28_days(self):
        daily_rate = contract._calculate_daily_rate(Decimal("0.05"))
        interest   = contract._calculate_interest(Decimal("10000"), daily_rate, days=28)
        assert interest == Decimal("38.36")

    def test_interest_uses_decimal_not_float(self):
        daily_rate = contract._calculate_daily_rate(Decimal("0.05"))
        assert isinstance(daily_rate, Decimal)

    def test_posting_net_effect_debit(self):
        posting = make_posting_instruction(Decimal("100"), credit=False)
        effect  = contract._posting_net_effect([posting])
        assert effect == Decimal("-100")

    def test_posting_net_effect_credit(self):
        posting = make_posting_instruction(Decimal("100"), credit=True)
        effect  = contract._posting_net_effect([posting])
        assert effect == Decimal("100")