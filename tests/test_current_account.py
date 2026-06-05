# tests/test_current_account.py
# Vault Smart Contract API 4.0 — Current Account with Overdraft

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
    ActivationHookArguments,
    RejectionReason,
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import contracts.current_account as contract

UTC = ZoneInfo("UTC")
DEFAULT_DATE = datetime(2024, 1, 28, tzinfo=UTC)
DEFAULT_DENOM = "GBP"
DEFAULT_ADDRESS = "DEFAULT"
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"


def make_balance_dict(amount: Decimal, denomination: str = DEFAULT_DENOM) -> BalanceDefaultDict:
    balances = BalanceDefaultDict()
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    credit = amount if amount >= 0 else Decimal("0")
    debit = Decimal("0") if amount >= 0 else abs(amount)
    balances[key] = Balance(net=amount, credit=credit, debit=debit)
    return balances


def make_vault(
    balance: Decimal = Decimal("1000"),
    overdraft_limit: Decimal = Decimal("0.00"),
    denomination: str = DEFAULT_DENOM,
) -> MagicMock:
    vault = MagicMock()
    vault.account_id = "test_account_001"

    def parameter_timeseries(name: str):
        if name == "overdraft_limit":
            return MagicMock(latest=MagicMock(return_value=overdraft_limit))
        if name == "denomination":
            return MagicMock(latest=MagicMock(return_value=denomination))
        raise AssertionError(f"Unexpected parameter requested: {name}")

    vault.get_parameter_timeseries.side_effect = parameter_timeseries
    obs = MagicMock()
    obs.balances = make_balance_dict(balance, denomination)
    vault.get_balances_observation.return_value = obs
    vault.get_hook_execution_id.return_value = "test-hook-id"
    return vault


def make_posting_instruction(amount: Decimal, credit: bool = False) -> MagicMock:
    pi = MagicMock()
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=DEFAULT_DENOM,
        phase=Phase.COMMITTED,
    )
    net = amount if credit else -amount
    credit_amt = amount if credit else Decimal("0")
    debit_amt = Decimal("0") if credit else amount
    bal_dict = BalanceDefaultDict()
    bal_dict[key] = Balance(net=net, credit=credit_amt, debit=debit_amt)
    pi.balances.return_value = bal_dict
    return pi


class TestActivationHook:

    def test_returns_empty_scheduled_events(self):
        vault = make_vault()
        args = ActivationHookArguments(effective_datetime=DEFAULT_DATE)

        result = contract.activation_hook(vault, args)

        assert result.scheduled_events_return_value == {}


class TestPrePostingHook:

    def _make_args(self, posting) -> PrePostingHookArguments:
        return PrePostingHookArguments(
            effective_datetime=DEFAULT_DATE,
            posting_instructions=[posting],
            client_transactions={},
        )

    def test_allows_withdrawal_with_positive_balance(self):
        vault = make_vault(balance=Decimal("500"), overdraft_limit=Decimal("100.00"))
        posting = make_posting_instruction(Decimal("300"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None

    def test_allows_withdrawal_within_overdraft_limit(self):
        vault = make_vault(balance=Decimal("100"), overdraft_limit=Decimal("200.00"))
        posting = make_posting_instruction(Decimal("250"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None

    def test_rejects_withdrawal_exceeding_overdraft_limit(self):
        vault = make_vault(balance=Decimal("100"), overdraft_limit=Decimal("200.00"))
        posting = make_posting_instruction(Decimal("301"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is not None
        assert result.rejection.reason_code == RejectionReason.INSUFFICIENT_FUNDS

    def test_deposit_reduces_overdraft_usage(self):
        vault = make_vault(balance=Decimal("-100"), overdraft_limit=Decimal("200.00"))
        posting = make_posting_instruction(Decimal("150"), credit=True)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None

    def test_zero_balance_has_zero_overdraft_usage(self):
        usage = contract._calculate_overdraft_usage(Decimal("0"))

        assert usage == Decimal("0.00")

    def test_parameter_retrieval_for_denomination_and_overdraft_limit(self):
        vault = make_vault(balance=Decimal("100"), overdraft_limit=Decimal("50.00"), denomination="GBP")
        posting = make_posting_instruction(Decimal("50"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None
        assert vault.get_parameter_timeseries.call_count == 2
        vault.get_parameter_timeseries.assert_any_call(name="denomination")
        vault.get_parameter_timeseries.assert_any_call(name="overdraft_limit")

    def test_committed_balance_read_from_live_balances(self):
        vault = make_vault(balance=Decimal("250"), overdraft_limit=Decimal("100.00"))
        posting = make_posting_instruction(Decimal("100"), credit=False)

        result = contract.pre_posting_hook(vault, self._make_args(posting))

        assert result.rejection is None
        vault.get_balances_observation.assert_called_once_with(fetcher_id="live_balances")


class TestHelpers:

    def test_available_balance_includes_overdraft_limit(self):
        available = contract._calculate_available_balance(Decimal("100"), Decimal("200.00"))

        assert available == Decimal("300.00")

    def test_overdraft_remaining_is_zero_when_limit_used(self):
        remaining = contract._calculate_overdraft_remaining(Decimal("200.00"), Decimal("200.00"))

        assert remaining == Decimal("0.00")

    def test_overdraft_remaining_never_negative(self):
        remaining = contract._calculate_overdraft_remaining(Decimal("200.00"), Decimal("250.00"))

        assert remaining == Decimal("0.00")
