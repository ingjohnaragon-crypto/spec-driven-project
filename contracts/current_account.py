from contracts_api import (
    ActivationHookArguments,
    ActivationHookResult,
    BalanceCoordinate,
    BalanceDefaultDict,
    DenominationShape,
    NumberShape,
    Parameter,
    ParameterLevel,
    Phase,
    PostPostingHookArguments,
    PostPostingHookResult,
    PrePostingHookArguments,
    PrePostingHookResult,
    Rejection,
    RejectionReason,
    ScheduledEventHookArguments,
    ScheduledEventHookResult,
    Tside,
)
from decimal import Decimal

api = "4.0.0"
version = "1.0.0"
display_name = "Current Account with Overdraft"
summary = "Current account product with authorized overdraft limit"
description = (
    "A current account product that supports a configurable overdraft limit "
    "and rejects debit postings that exceed the approved overdraft capacity."
)
tside = Tside.LIABILITY
supported_denominations = ["GBP"]

DEFAULT_ADDRESS = "DEFAULT"
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"

parameters = [
    Parameter(
        name="denomination",
        shape=DenominationShape(),
        level=ParameterLevel.INSTANCE,
        display_name="Denomination",
        description="Account currency denomination.",
        default_value="GBP",
    ),
    Parameter(
        name="overdraft_limit",
        shape=NumberShape(
            min_value=Decimal("0.00"),
            step=Decimal("0.01"),
        ),
        level=ParameterLevel.INSTANCE,
        display_name="Overdraft Limit",
        description="Maximum permitted overdraft for the account.",
        default_value=Decimal("0.00"),
    ),
]

event_types = []
event_types_groups = []


def _get_committed_balance(
    balances: BalanceDefaultDict,
    denomination: str,
) -> Decimal:
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    return balances[key].net


def _posting_net_effect(posting_instructions) -> Decimal:
    total = Decimal("0")
    for posting in posting_instructions:
        for coord, balance in posting.balances().items():
            if coord.phase == Phase.COMMITTED:
                total += balance.net
    return total


def _calculate_overdraft_usage(current_balance: Decimal) -> Decimal:
    return max(Decimal("0.00"), -current_balance)


def _calculate_overdraft_remaining(
    overdraft_limit: Decimal,
    overdraft_used: Decimal,
) -> Decimal:
    remaining = overdraft_limit - overdraft_used
    return remaining if remaining >= Decimal("0.00") else Decimal("0.00")


def _calculate_available_balance(
    current_balance: Decimal,
    overdraft_limit: Decimal,
) -> Decimal:
    return current_balance + overdraft_limit


def activation_hook(
    vault, hook_arguments: ActivationHookArguments
) -> ActivationHookResult:
    return ActivationHookResult(scheduled_events_return_value={})


def pre_posting_hook(
    vault, hook_arguments: PrePostingHookArguments
) -> PrePostingHookResult:
    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    overdraft_limit = vault.get_parameter_timeseries(name="overdraft_limit").latest()
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    current_balance = _get_committed_balance(balances, denomination)
    posting_effect = _posting_net_effect(hook_arguments.posting_instructions)
    available_balance = _calculate_available_balance(current_balance, overdraft_limit)
    resulting_balance = current_balance + posting_effect
    overdraft_used = _calculate_overdraft_usage(resulting_balance)
    overdraft_remaining = _calculate_overdraft_remaining(overdraft_limit, overdraft_used)

    if overdraft_used > overdraft_limit:
        return PrePostingHookResult(
            rejection=Rejection(
                message=(
                    f"Insufficient funds: available balance {available_balance} "
                    f"{denomination}, requested net effect {posting_effect}, "
                    f"overdraft remaining {overdraft_remaining}."
                ),
                reason_code=RejectionReason.INSUFFICIENT_FUNDS,
            )
        )

    return PrePostingHookResult()


def post_posting_hook(
    vault, hook_arguments: PostPostingHookArguments
) -> PostPostingHookResult:
    return PostPostingHookResult(posting_instructions_directives=[])


def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    return ScheduledEventHookResult(
        posting_instructions_directives=[],
        update_account_event_type_directives=[],
    )
