# tests/test_current_account.py
# Unit tests for current_account.py — Vault Smart Contract API 4.0
# Run: py -m pytest tests/test_current_account.py -v --cov=contracts/current_account.py

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
    PostPostingHookArguments,
    ScheduledEventHookArguments,
    ActivationHookArguments,
    RejectionReason,
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import contracts.current_account as contract

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
               overdraft_limit: Decimal = Decimal("500"),
               denomination: str = DEFAULT_DENOM) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "test_current_account_001"

    def param_side_effect(name):
        values = {
            "denomination": denomination,
            "overdraft_limit": overdraft_limit,
        }
        return MagicMock(latest=MagicMock(return_value=values[name]))

    vault.get_parameter_timeseries.side_effect = param_side_effect
    obs = MagicMock()
    obs.balances = make_balance_dict(balance, denomination)
    vault.get_balances_observation.return_value = obs
    vault.get_hook_execution_id.return_value = "test-hook-id-001"
    return vault


def make_posting_instruction(amount: Decimal,
                              credit: bool = False) -> MagicMock:
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

    def test_returns_result(self):
        vault = make_vault()
        args  = ActivationHookArguments(effective_datetime=DEFAULT_DATE)
        result = contract.activation_hook(vault, args)
        assert result is not None


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
        vault   = make_vault(balance=Decimal("500"), overdraft_limit=Decimal("0"))
        posting = make_posting_instruction(Decimal("100"), credit=True)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is None

    def test_allows_withdrawal_within_balance(self):
        vault   = make_vault(balance=Decimal("500"), overdraft_limit=Decimal("0"))
        posting = make_posting_instruction(Decimal("400"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is None

    def test_allows_withdrawal_using_overdraft(self):
        """Balance 100 + overdraft 500 = 600 available. Withdraw 500 → ok."""
        vault   = make_vault(balance=Decimal("100"), overdraft_limit=Decimal("500"))
        posting = make_posting_instruction(Decimal("500"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is None

    def test_allows_full_overdraft(self):
        """Balance 0 + overdraft 500 = 500 available. Withdraw 500 → ok."""
        vault   = make_vault(balance=Decimal("0"), overdraft_limit=Decimal("500"))
        posting = make_posting_instruction(Decimal("500"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is None

    def test_rejects_beyond_overdraft_limit(self):
        """Balance 100 + overdraft 500 = 600. Withdraw 700 → rejected."""
        vault   = make_vault(balance=Decimal("100"), overdraft_limit=Decimal("500"))
        posting = make_posting_instruction(Decimal("700"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.INSUFFICIENT_FUNDS

    def test_rejects_one_cent_beyond_overdraft(self):
        vault   = make_vault(balance=Decimal("0"), overdraft_limit=Decimal("500"))
        posting = make_posting_instruction(Decimal("500.01"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is not None

    def test_rejects_with_no_overdraft_and_no_balance(self):
        vault   = make_vault(balance=Decimal("0"), overdraft_limit=Decimal("0"))
        posting = make_posting_instruction(Decimal("1"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is not None

    def test_allows_exact_balance_no_overdraft(self):
        vault   = make_vault(balance=Decimal("200"), overdraft_limit=Decimal("0"))
        posting = make_posting_instruction(Decimal("200"), credit=False)
        result  = contract.pre_posting_hook(vault, self._make_args(posting))
        assert result.rejection is None


# ══════════════════════════════════════════════════════════════
# post_posting_hook
# ══════════════════════════════════════════════════════════════
class TestPostPostingHook:

    def test_returns_empty_directives(self):
        vault   = make_vault()
        posting = make_posting_instruction(Decimal("100"), credit=True)
        args    = PostPostingHookArguments(
            effective_datetime=DEFAULT_DATE,
            posting_instructions=[posting],
            client_transactions={},
        )
        result = contract.post_posting_hook(vault, args)
        assert result.posting_instructions_directives == []


# ══════════════════════════════════════════════════════════════
# scheduled_event_hook
# ══════════════════════════════════════════════════════════════
class TestScheduledEventHook:

    def test_returns_empty_directives(self):
        vault  = make_vault()
        args   = ScheduledEventHookArguments(
            effective_datetime=DEFAULT_DATE,
            event_type="ANY_EVENT",
        )
        result = contract.scheduled_event_hook(vault, args)
        assert result.posting_instructions_directives == []


# ══════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════
class TestHelpers:

    def test_get_committed_balance(self):
        balances = make_balance_dict(Decimal("750"))
        result   = contract._get_committed_balance(balances, "GBP")
        assert result == Decimal("750")

    def test_get_committed_balance_negative(self):
        balances = make_balance_dict(Decimal("-200"))
        result   = contract._get_committed_balance(balances, "GBP")
        assert result == Decimal("-200")

    def test_posting_net_effect_debit(self):
        posting = make_posting_instruction(Decimal("300"), credit=False)
        result  = contract._posting_net_effect([posting])
        assert result == Decimal("-300")

    def test_posting_net_effect_credit(self):
        posting = make_posting_instruction(Decimal("300"), credit=True)
        result  = contract._posting_net_effect([posting])
        assert result == Decimal("300")

    def test_calculate_available_balance_with_overdraft(self):
        result = contract._calculate_available_balance(Decimal("100"), Decimal("500"))
        assert result == Decimal("600")

    def test_calculate_available_balance_no_overdraft(self):
        result = contract._calculate_available_balance(Decimal("100"), Decimal("0"))
        assert result == Decimal("100")

    def test_calculate_available_balance_negative_balance(self):
        result = contract._calculate_available_balance(Decimal("-100"), Decimal("500"))
        assert result == Decimal("400")

    def test_calculate_overdraft_usage_no_overdraft(self):
        result = contract._calculate_overdraft_usage(Decimal("100"))
        assert result == Decimal("0")

    def test_calculate_overdraft_usage_in_overdraft(self):
        result = contract._calculate_overdraft_usage(Decimal("-200"))
        assert result == Decimal("200")