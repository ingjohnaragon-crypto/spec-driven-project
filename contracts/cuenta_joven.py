from contracts_api import (
    ParameterUpdatePermission,
    ActivationHookArguments,
    ActivationHookResult,
    BalanceCoordinate,
    BalanceDefaultDict,
    BalancesObservationFetcher,
    CustomInstruction,
    DefinedDateTime,
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
    ScheduleExpression,
    ScheduledEventHookArguments,
    ScheduledEventHookResult,
    SmartContractEventType,
    Tside,
    fetch_account_data,
    requires,
)
from decimal import Decimal, ROUND_HALF_UP

api = "4.0.0"
version = "1.0.0"
display_name = "Cuenta joven"
summary = "Cuenta joven con límite diario de retiros e interés bonificado"
description = (
    "Cuenta de pasivo con límite configurable de retiros diarios y una tasa de interés "
    "estándar o bonificada según saldo y ahorro mínimos."
)
tside = Tside.LIABILITY
supported_denominations = ["GBP", "USD", "EUR", "COP"]

DEFAULT_ADDRESS = "DEFAULT"
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"
DAILY_WITHDRAWALS = "DAILY_WITHDRAWALS"
DAILY_WITHDRAWALS_OFFSET = "DAILY_WITHDRAWALS_OFFSET"
INTEREST_EXPENSE = "INTEREST_EXPENSE"
DAILY_WITHDRAWAL_RESET = "DAILY_WITHDRAWAL_RESET"
MONTHLY_INTEREST = "MONTHLY_INTEREST"

parameters = [
    Parameter(
        name="denomination",
        shape=DenominationShape(permitted_denominations=supported_denominations),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Denomination",
        description="Account denomination. One currency per account.",
        default_value="GBP",
    ),
    Parameter(
        name="daily_withdrawal_limit",
        shape=NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Daily Withdrawal Limit",
        description="Maximum amount withdrawn during one calendar day.",
        default_value=Decimal("500.00"),
    ),
    Parameter(
        name="standard_interest_rate",
        shape=NumberShape(
            min_value=Decimal("0"), max_value=Decimal("1"), step=Decimal("0.0001")
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Standard Interest Rate",
        description="Annual rate as a fraction, where 0.02 means 2 percent.",
        default_value=Decimal("0.02"),
    ),
    Parameter(
        name="bonus_interest_rate",
        shape=NumberShape(
            min_value=Decimal("0"), max_value=Decimal("1"), step=Decimal("0.0001")
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Bonus Interest Rate",
        description="Annual bonus rate as a fraction, where 0.05 means 5 percent.",
        default_value=Decimal("0.05"),
    ),
    Parameter(
        name="bonus_minimum_balance",
        shape=NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Bonus Minimum Balance",
        description="Minimum balance required for the bonus rate.",
        default_value=Decimal("1000.00"),
    ),
    Parameter(
        name="bonus_minimum_savings",
        shape=NumberShape(min_value=Decimal("0.00"), step=Decimal("0.01")),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Bonus Minimum Savings",
        description="Minimum savings amount required for the bonus rate.",
        default_value=Decimal("500.00"),
    ),
]

event_types = [
    SmartContractEventType(name=DAILY_WITHDRAWAL_RESET),
    SmartContractEventType(name=MONTHLY_INTEREST),
]
event_types_groups = []

# API 4.0: hooks that call get_balances_observation() declare the fetcher here.
data_fetchers = [
    BalancesObservationFetcher(fetcher_id="live_balances", at=DefinedDateTime.LIVE),
]


def _quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_committed_balance(
    balances: BalanceDefaultDict,
    address: str,
    denomination: str,
) -> Decimal:
    key = BalanceCoordinate(
        account_address=address,
        asset=DEFAULT_ASSET,
        denomination=denomination,
        phase=Phase.COMMITTED,
    )
    return balances[key].net


def _posting_net_effect(posting_instructions, address: str, denomination: str) -> Decimal:
    total = Decimal("0")
    for posting in posting_instructions:
        for coordinate, balance in posting.balances().items():
            if (
                coordinate.phase == Phase.COMMITTED
                and coordinate.account_address == address
                and coordinate.denomination == denomination
            ):
                total += balance.net
    return total


def _get_withdrawal_amount(posting_instructions, denomination: str) -> Decimal:
    effect = _posting_net_effect(posting_instructions, DEFAULT_ADDRESS, denomination)
    return abs(effect) if effect < Decimal("0") else Decimal("0")


def _calculate_bonus_eligibility(
    balance: Decimal,
    minimum_balance: Decimal,
    minimum_savings: Decimal,
) -> bool:
    balance_condition = minimum_balance == Decimal("0") or balance >= minimum_balance
    savings_condition = minimum_savings == Decimal("0") or balance >= minimum_savings
    return balance_condition and savings_condition


def _calculate_interest(balance: Decimal, annual_rate: Decimal) -> Decimal:
    if balance <= Decimal("0"):
        return Decimal("0.00")
    return _quantize_money(balance * annual_rate / Decimal("12"))


def _build_internal_transfer(
    amount: Decimal,
    denomination: str,
    debit_address: str,
    credit_address: str,
    description: str,
    hook_id: str,
    event_type: str,
    account_id: str,
) -> CustomInstruction:
    return CustomInstruction(
        postings=[
            Posting(
                credit=False,
                amount=amount,
                denomination=denomination,
                account_id=account_id,
                account_address=debit_address,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=True,
                amount=amount,
                denomination=denomination,
                account_id=account_id,
                account_address=credit_address,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={
            "description": description,
            "hook_execution_id": hook_id,
            "event_type": event_type,
        },
    )


def _build_schedule(effective_datetime):
    return {
        DAILY_WITHDRAWAL_RESET: ScheduledEvent(
            start_datetime=effective_datetime,
            expression=ScheduleExpression(hour="0", minute="0", second="0"),
        ),
        MONTHLY_INTEREST: ScheduledEvent(
            start_datetime=effective_datetime,
            schedule_method=EndOfMonthSchedule(day=28),
        ),
    }


def _get_parameter(vault, name: str):
    return vault.get_parameter_timeseries(name=name).latest()


def _validate_parameters(
    denomination: str,
    daily_limit: Decimal,
    standard_rate: Decimal,
    bonus_rate: Decimal,
    minimum_balance: Decimal,
    minimum_savings: Decimal,
) -> None:
    if denomination not in supported_denominations:
        raise ValueError("Invalid account parameters.")
    if daily_limit < Decimal("0"):
        raise ValueError("Invalid account parameters.")
    if minimum_balance < Decimal("0") or minimum_savings < Decimal("0"):
        raise ValueError("Invalid account parameters.")
    if standard_rate < Decimal("0") or standard_rate > Decimal("1"):
        raise ValueError("Invalid account parameters.")
    if bonus_rate < Decimal("0") or bonus_rate > Decimal("1"):
        raise ValueError("Invalid account parameters.")
    if bonus_rate < standard_rate:
        raise ValueError("Invalid account parameters.")


@requires(parameters=True)
def activation_hook(
    vault, hook_arguments: ActivationHookArguments
) -> ActivationHookResult:
    denomination = _get_parameter(vault, "denomination")
    daily_limit = _get_parameter(vault, "daily_withdrawal_limit")
    standard_rate = _get_parameter(vault, "standard_interest_rate")
    bonus_rate = _get_parameter(vault, "bonus_interest_rate")
    minimum_balance = _get_parameter(vault, "bonus_minimum_balance")
    minimum_savings = _get_parameter(vault, "bonus_minimum_savings")
    _validate_parameters(
        denomination,
        daily_limit,
        standard_rate,
        bonus_rate,
        minimum_balance,
        minimum_savings,
    )
    return ActivationHookResult(
        scheduled_events_return_value=_build_schedule(hook_arguments.effective_datetime)
    )


@requires(parameters=True)
@fetch_account_data(balances=["live_balances"])
def pre_posting_hook(
    vault, hook_arguments: PrePostingHookArguments
) -> PrePostingHookResult:
    denomination = _get_parameter(vault, "denomination")
    daily_limit = _get_parameter(vault, "daily_withdrawal_limit")
    for posting in hook_arguments.posting_instructions:
        if posting.denomination != denomination:
            return PrePostingHookResult(
                rejection=Rejection(
                    message=(
                        f"Posting denomination {posting.denomination} does not match "
                        f"account denomination {denomination}."
                    ),
                    reason_code=RejectionReason.WRONG_DENOMINATION,
                )
            )

    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    current_balance = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)
    accumulated = _get_committed_balance(balances, DAILY_WITHDRAWALS, denomination)
    posting_effect = _posting_net_effect(
        hook_arguments.posting_instructions, DEFAULT_ADDRESS, denomination
    )
    withdrawal = _get_withdrawal_amount(hook_arguments.posting_instructions, denomination)

    if withdrawal > Decimal("0") and current_balance + posting_effect < Decimal("0"):
        return PrePostingHookResult(
            rejection=Rejection(
                message=(
                    f"Insufficient funds: balance {current_balance} {denomination}, "
                    f"attempted {withdrawal} {denomination} debit."
                ),
                reason_code=RejectionReason.INSUFFICIENT_FUNDS,
            )
        )
    if accumulated + withdrawal > daily_limit:
        return PrePostingHookResult(
            rejection=Rejection(
                message=(
                    f"Daily withdrawal limit exceeded: accumulated {accumulated} "
                    f"{denomination}, requested {withdrawal} {denomination}, limit "
                    f"{daily_limit} {denomination}."
                ),
                reason_code=RejectionReason.AGAINST_TNC,
            )
        )
    return PrePostingHookResult()


@requires(parameters=True)
def post_posting_hook(
    vault, hook_arguments: PostPostingHookArguments
) -> PostPostingHookResult:
    denomination = _get_parameter(vault, "denomination")
    withdrawal = _get_withdrawal_amount(hook_arguments.posting_instructions, denomination)
    if withdrawal <= Decimal("0"):
        return PostPostingHookResult(posting_instructions_directives=[])
    instruction = _build_internal_transfer(
        withdrawal,
        denomination,
        DAILY_WITHDRAWALS_OFFSET,
        DAILY_WITHDRAWALS,
        "Daily withdrawal accumulation",
        str(vault.get_hook_execution_id()),
        "WITHDRAWAL_REGISTER",
        vault.account_id,
    )
    return PostPostingHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[instruction])
        ]
    )


@requires(event_type="DAILY_WITHDRAWAL_RESET", parameters=True)
@requires(event_type="MONTHLY_INTEREST", parameters=True)
@fetch_account_data(event_type="DAILY_WITHDRAWAL_RESET", balances=["live_balances"])
@fetch_account_data(event_type="MONTHLY_INTEREST", balances=["live_balances"])
def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    denomination = _get_parameter(vault, "denomination")
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    hook_id = str(vault.get_hook_execution_id())

    if hook_arguments.event_type == DAILY_WITHDRAWAL_RESET:
        accumulated = _get_committed_balance(balances, DAILY_WITHDRAWALS, denomination)
        if accumulated <= Decimal("0"):
            return ScheduledEventHookResult(
                posting_instructions_directives=[],
                update_account_event_type_directives=[],
            )
        instruction = _build_internal_transfer(
            accumulated,
            denomination,
            DAILY_WITHDRAWALS,
            DAILY_WITHDRAWALS_OFFSET,
            "Daily withdrawal accumulation reset",
            hook_id,
            DAILY_WITHDRAWAL_RESET,
            vault.account_id,
        )
        return ScheduledEventHookResult(
            posting_instructions_directives=[
                PostingInstructionsDirective(posting_instructions=[instruction])
            ],
            update_account_event_type_directives=[],
        )

    if hook_arguments.event_type == MONTHLY_INTEREST:
        balance = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)
        standard_rate = _get_parameter(vault, "standard_interest_rate")
        bonus_rate = _get_parameter(vault, "bonus_interest_rate")
        minimum_balance = _get_parameter(vault, "bonus_minimum_balance")
        minimum_savings = _get_parameter(vault, "bonus_minimum_savings")
        eligible = _calculate_bonus_eligibility(
            balance, minimum_balance, minimum_savings
        )
        rate = bonus_rate if eligible else standard_rate
        interest = _calculate_interest(balance, rate)
        if interest <= Decimal("0"):
            return ScheduledEventHookResult(
                posting_instructions_directives=[],
                update_account_event_type_directives=[],
            )
        instruction = _build_internal_transfer(
            interest,
            denomination,
            INTEREST_EXPENSE,
            DEFAULT_ADDRESS,
            "Monthly interest payment",
            hook_id,
            MONTHLY_INTEREST,
            vault.account_id,
        )
        return ScheduledEventHookResult(
            posting_instructions_directives=[
                PostingInstructionsDirective(posting_instructions=[instruction])
            ],
            update_account_event_type_directives=[],
        )

    return ScheduledEventHookResult(
        posting_instructions_directives=[],
        update_account_event_type_directives=[],
    )
