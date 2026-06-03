# contracts/savings_product.py
# Vault Smart Contract — Basic Savings Account
# Contracts Language API 4.0

from contracts_api import (
    ActivationHookArguments,
    ActivationHookResult,
    BalanceDefaultDict,
    CustomInstruction,
    DenominationShape,
    EndOfMonthSchedule,
    NumberShape,
    Parameter,
    ParameterLevel,
    Phase,
    Posting,
    PostingInstructionsDirective,
    PostPostingHookArguments,
    PostPostingHookResult,
    PrePostingHookArguments,
    PrePostingHookResult,
    Rejection,
    RejectionReason,
    ScheduledEvent,
    ScheduledEventHookArguments,
    ScheduledEventHookResult,
    SmartContractEventType,
    Tside,
)
from decimal import Decimal, ROUND_HALF_UP

api          = "4.0.0"
version      = "1.0.0"
display_name = "Basic Savings Account"
summary      = "Savings account with monthly interest accrual"
description  = (
    "A simple savings account that accrues interest monthly. "
    "Overdrafts are rejected. Interest is calculated on the "
    "committed balance at the end of each month."
)

tside                    = Tside.LIABILITY
supported_denominations  = ["GBP"]

DEFAULT_ADDRESS  = "DEFAULT"
DEFAULT_ASSET    = "COMMERCIAL_BANK_MONEY"
ACCRUED_INTEREST = "ACCRUED_INTEREST"
DAYS_IN_YEAR     = Decimal("365")
INTEREST_ACCRUAL = "INTEREST_ACCRUAL"

parameters = [
    Parameter(
        name="interest_rate",
        shape=NumberShape(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            step=Decimal("0.0001"),
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Annual Interest Rate",
        description="Annual interest rate applied to the account balance.",
        default_value=Decimal("0.05"),
    ),
    Parameter(
        name="denomination",
        shape=DenominationShape(),
        level=ParameterLevel.INSTANCE,
        display_name="Denomination",
        description="Account denomination.",
        default_value="GBP",
    ),
]

event_types = [
    SmartContractEventType(
        name=INTEREST_ACCRUAL,
        scheduler_tag_ids=["SAVINGS_INTEREST_ACCRUAL_AST"],
    ),
]

event_types_groups = []

# ── Pure helpers ──────────────────────────────────────────────

def _get_committed_balance(
    balances: BalanceDefaultDict,
    denomination: str,
) -> Decimal:
    """Read the net committed balance for the default address."""
    from contracts_api import BalanceCoordinate
    key = BalanceCoordinate(
        account_address=DEFAULT_ADDRESS,
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    return balances[key].net


def _calculate_daily_rate(annual_rate: Decimal) -> Decimal:
    return (annual_rate / DAYS_IN_YEAR).quantize(
        Decimal("0.0000000001"), rounding=ROUND_HALF_UP
    )


def _calculate_interest(balance: Decimal, daily_rate: Decimal, days: int) -> Decimal:
    return (balance * daily_rate * Decimal(str(days))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _posting_net_effect(posting_instructions) -> Decimal:
    """
    Sum the net COMMITTED effect of all postings in a batch.
    In API 4.0 posting.balances() returns {BalanceCoordinate: Balance}.
    Phase is on the key (BalanceCoordinate), not on the Balance value.
    """
    total = Decimal("0")
    for posting in posting_instructions:
        for coord, balance in posting.balances().items():
            if coord.phase == Phase.COMMITTED:
                total += balance.net
    return total


# ── Hooks ─────────────────────────────────────────────────────

def activation_hook(
    vault, hook_arguments: ActivationHookArguments
) -> ActivationHookResult:
    scheduled_events = {
        INTEREST_ACCRUAL: ScheduledEvent(
            start_datetime=hook_arguments.effective_datetime,
            schedule_method=EndOfMonthSchedule(day=28),
        ),
    }
    return ActivationHookResult(scheduled_events_return_value=scheduled_events)


def pre_posting_hook(
    vault, hook_arguments: PrePostingHookArguments
) -> PrePostingHookResult:
    denomination    = vault.get_parameter_timeseries(name="denomination").latest()
    balances        = vault.get_balances_observation(fetcher_id="live_balances").balances
    current_balance = _get_committed_balance(balances, denomination)
    posting_effect  = _posting_net_effect(hook_arguments.posting_instructions)

    if current_balance + posting_effect < Decimal("0"):
        return PrePostingHookResult(
            rejection=Rejection(
                message=(
                    f"Insufficient funds: balance {current_balance} {denomination}, "
                    f"attempted {abs(posting_effect)} {denomination} debit."
                ),
                reason_code=RejectionReason.INSUFFICIENT_FUNDS,
            )
        )
    return PrePostingHookResult()


def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    if hook_arguments.event_type != INTEREST_ACCRUAL:
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    annual_rate  = vault.get_parameter_timeseries(name="interest_rate").latest()
    balances     = vault.get_balances_observation(fetcher_id="live_balances").balances
    balance      = _get_committed_balance(balances, denomination)
    daily_rate   = _calculate_daily_rate(annual_rate)
    interest     = _calculate_interest(balance, daily_rate, days=28)

    if interest <= Decimal("0"):
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    # API 4.0: CustomInstruction does NOT have client_transaction_id
    # Use instruction_details to carry the hook execution ID
    hook_id = vault.get_hook_execution_id()
    custom_instruction = CustomInstruction(
        postings=[
            Posting(
                credit=True,
                amount=interest,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=ACCRUED_INTEREST,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=False,
                amount=interest,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={
            "description": "Monthly interest accrual",
            "hook_execution_id": str(hook_id),
            "event_type": INTEREST_ACCRUAL,
        },
    )

    return ScheduledEventHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[custom_instruction])
        ],
        update_account_event_type_directives=[],
    )


def post_posting_hook(
    vault, hook_arguments: PostPostingHookArguments
) -> PostPostingHookResult:
    return PostPostingHookResult(posting_instructions_directives=[])