# contracts/fixed_term_deposit.py
# Vault Smart Contract — Fixed-Term Deposit
# Contracts Language API 4.0

from contracts_api import (
    ActivationHookArguments,
    ActivationHookResult,
    BalanceCoordinate,
    BalanceDefaultDict,
    BalancesObservationFetcher,
    CustomInstruction,
    DateShape,
    DefinedDateTime,
    DenominationShape,
    DerivedParameterHookArguments,
    DerivedParameterHookResult,
    NumberShape,
    OptionalShape,
    OptionalValue,
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
    UnionItem,
    UnionItemValue,
    UnionShape,
)
from decimal import Decimal, ROUND_HALF_UP

api          = "4.0.0"
version      = "1.0.0"
display_name = "Fixed-Term Deposit"
summary      = "Fixed-term deposit with daily interest accrual and maturity disbursement"
description  = (
    "A liability product where the customer locks a principal amount for a fixed period "
    "in exchange for a guaranteed annual interest rate. Interest accrues daily and is "
    "disbursed automatically on the maturity date together with the principal."
)
tside                   = Tside.LIABILITY
supported_denominations = ["GBP"]

DEFAULT_ADDRESS  = "DEFAULT"
DEFAULT_ASSET    = "COMMERCIAL_BANK_MONEY"
ACCRUED_INTEREST = "ACCRUED_INTEREST"
PENALTY_INCOME   = "PENALTY_INCOME"
DAILY_ACCRUAL    = "DAILY_ACCRUAL"
MATURITY_EVENT   = "MATURITY_EVENT"

parameters = [
    Parameter(
        name="denomination",
        shape=DenominationShape(),
        level=ParameterLevel.INSTANCE,
        display_name="Denomination",
        description="Account denomination.",
        default_value="GBP",
    ),
    Parameter(
        name="annual_interest_rate",
        shape=NumberShape(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            step=Decimal("0.0001"),
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Annual Interest Rate",
        description="AER applied to the deposit (0.05 = 5%).",
        default_value=Decimal("0.05"),
    ),
    Parameter(
        name="maturity_date",
        shape=OptionalShape(shape=DateShape()),
        level=ParameterLevel.INSTANCE,
        display_name="Maturity Date",
        description="The date on which the deposit matures. Must be in the future at activation.",
    ),
    Parameter(
        name="allow_early_closure",
        shape=OptionalShape(
            shape=UnionShape(
                items=[
                    UnionItem(key="true",  display_name="True"),
                    UnionItem(key="false", display_name="False"),
                ]
            )
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Allow Early Closure",
        description="Enables withdrawal before maturity with a penalty applied to accrued interest.",
        default_value=OptionalValue(UnionItemValue("false")),
    ),
    Parameter(
        name="early_closure_penalty_rate",
        shape=NumberShape(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            step=Decimal("0.0001"),
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Early Closure Penalty Rate",
        description="Fraction of accrued interest forfeited on early closure (0.20 = 20%).",
        default_value=Decimal("0.20"),
    ),
    # Derived parameters: declared with derived=True (API 4.0 SDK pattern).
    # Values are computed and returned by derived_parameter_hook.
    Parameter(
        name="accrued_interest",
        shape=NumberShape(),
        level=ParameterLevel.INSTANCE,
        derived=True,
        display_name="Accrued Interest",
        description="Current accrued interest balance.",
    ),
    Parameter(
        name="days_to_maturity",
        shape=NumberShape(),
        level=ParameterLevel.INSTANCE,
        derived=True,
        display_name="Days to Maturity",
        description="Days remaining until the maturity date (floor 0).",
    ),
]

event_types = [
    SmartContractEventType(name=DAILY_ACCRUAL),
    SmartContractEventType(name=MATURITY_EVENT),
]

event_types_groups = []

balance_observation_fetchers = [
    BalancesObservationFetcher(
        fetcher_id="live_balances",
        at=DefinedDateTime.LIVE,
    )
]


# ── Pure helpers ───────────────────────────────────────────────────────────────

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


def _posting_net_effect(posting_instructions, denomination: str) -> Decimal:
    """Sum the COMMITTED net effect on DEFAULT address.
    API 4.0: phase is on BalanceCoordinate (key), not on Balance (value).
    """
    total = Decimal("0")
    for posting in posting_instructions:
        for coord, balance in posting.balances().items():
            if (
                coord.phase == Phase.COMMITTED
                and coord.account_address == DEFAULT_ADDRESS
                and coord.denomination == denomination
            ):
                total += balance.net
    return total


def _get_early_closure_flag(vault) -> bool:
    opt = vault.get_parameter_timeseries(name="allow_early_closure").latest()
    return opt.is_set() and opt.value.key == "true"


# ── Hooks ──────────────────────────────────────────────────────────────────────

def activation_hook(
    vault, hook_arguments: ActivationHookArguments
) -> ActivationHookResult:
    opt_maturity   = vault.get_parameter_timeseries(name="maturity_date").latest()
    if not opt_maturity.is_set():
        raise ValueError("maturity_date is required for a Fixed-Term Deposit.")
    maturity_date  = opt_maturity.value
    effective_date = hook_arguments.effective_datetime.date()

    if maturity_date.date() <= effective_date:
        raise ValueError("maturity_date must be strictly in the future.")

    start_dt = hook_arguments.effective_datetime

    daily_schedule = ScheduledEvent(
        start_datetime=start_dt,
        expression=ScheduleExpression(
            hour="23",
            minute="59",
            second="59",
        ),
    )

    maturity_schedule = ScheduledEvent(
        start_datetime=start_dt,
        expression=ScheduleExpression(
            year=str(maturity_date.year),
            month=str(maturity_date.month),
            day=str(maturity_date.day),
            hour="0",
            minute="0",
            second="0",
        ),
    )

    return ActivationHookResult(
        scheduled_events_return_value={
            DAILY_ACCRUAL:  daily_schedule,
            MATURITY_EVENT: maturity_schedule,
        }
    )


def pre_posting_hook(
    vault, hook_arguments: PrePostingHookArguments
) -> PrePostingHookResult:
    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    balances     = vault.get_balances_observation(fetcher_id="live_balances").balances
    principal    = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)

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

    posting_net = _posting_net_effect(hook_arguments.posting_instructions, denomination)

    if posting_net < Decimal("0"):
        if not _get_early_closure_flag(vault):
            return PrePostingHookResult(
                rejection=Rejection(
                    message="Withdrawals are not permitted before maturity.",
                    reason_code=RejectionReason.AGAINST_TNC,
                )
            )

    if posting_net > Decimal("0") and principal > Decimal("0"):
        return PrePostingHookResult(
            rejection=Rejection(
                message="Only one deposit is accepted at account opening.",
                reason_code=RejectionReason.AGAINST_TNC,
            )
        )

    return PrePostingHookResult()


def post_posting_hook(
    vault, hook_arguments: PostPostingHookArguments
) -> PostPostingHookResult:
    if not _get_early_closure_flag(vault):
        return PostPostingHookResult(posting_instructions_directives=[])

    denomination    = vault.get_parameter_timeseries(name="denomination").latest()
    balances        = vault.get_balances_observation(fetcher_id="live_balances").balances
    principal_after = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)
    accrued         = _get_committed_balance(balances, ACCRUED_INTEREST, denomination)

    if principal_after != Decimal("0") or accrued <= Decimal("0"):
        return PostPostingHookResult(posting_instructions_directives=[])

    penalty_rate = vault.get_parameter_timeseries(name="early_closure_penalty_rate").latest()
    penalty      = (accrued * penalty_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    net_payout   = max(accrued - penalty, Decimal("0"))

    hook_id      = vault.get_hook_execution_id()
    instructions = []

    if net_payout > Decimal("0"):
        instructions.append(CustomInstruction(
            postings=[
                Posting(
                    credit=False,
                    amount=net_payout,
                    denomination=denomination,
                    account_id=vault.account_id,
                    account_address=ACCRUED_INTEREST,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
                Posting(
                    credit=True,
                    amount=net_payout,
                    denomination=denomination,
                    account_id=vault.account_id,
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
            ],
            instruction_details={
                "description": "Early closure interest payout (after penalty)",
                "hook_execution_id": str(hook_id),
            },
        ))

    if penalty > Decimal("0"):
        instructions.append(CustomInstruction(
            postings=[
                Posting(
                    credit=False,
                    amount=penalty,
                    denomination=denomination,
                    account_id=vault.account_id,
                    account_address=ACCRUED_INTEREST,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
                Posting(
                    credit=True,
                    amount=penalty,
                    denomination=denomination,
                    account_id=vault.account_id,
                    account_address=PENALTY_INCOME,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
            ],
            instruction_details={
                "description": "Early closure penalty forfeiture",
                "hook_execution_id": str(hook_id),
            },
        ))

    return PostPostingHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=instructions)
        ]
    )


def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    if hook_arguments.event_type == DAILY_ACCRUAL:
        return _handle_daily_accrual(vault)
    if hook_arguments.event_type == MATURITY_EVENT:
        return _handle_maturity_event(vault)
    return ScheduledEventHookResult(
        posting_instructions_directives=[],
        update_account_event_type_directives=[],
    )


def derived_parameter_hook(
    vault, hook_arguments: DerivedParameterHookArguments
) -> DerivedParameterHookResult:
    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    opt_maturity = vault.get_parameter_timeseries(name="maturity_date").latest()
    balances     = vault.get_balances_observation(fetcher_id="live_balances").balances
    accrued      = _get_committed_balance(balances, ACCRUED_INTEREST, denomination)
    today        = hook_arguments.effective_datetime.date()

    if opt_maturity.is_set():
        days = max((opt_maturity.value.date() - today).days, 0)
    else:
        days = 0

    return DerivedParameterHookResult(
        parameters_return_value={
            "accrued_interest": accrued,
            "days_to_maturity":  days,
        }
    )


# ── Private hook implementations ───────────────────────────────────────────────

def _handle_daily_accrual(vault) -> ScheduledEventHookResult:
    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    annual_rate  = vault.get_parameter_timeseries(name="annual_interest_rate").latest()
    balances     = vault.get_balances_observation(fetcher_id="live_balances").balances
    principal    = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)

    if principal <= Decimal("0"):
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    daily_rate = (annual_rate / Decimal("365")).quantize(
        Decimal("0.0000000001"), rounding=ROUND_HALF_UP
    )
    interest = (principal * daily_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if interest <= Decimal("0"):
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    hook_id = vault.get_hook_execution_id()
    accrual_instruction = CustomInstruction(
        postings=[
            Posting(
                credit=False,
                amount=interest,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=True,
                amount=interest,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=ACCRUED_INTEREST,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={
            "description": "Daily interest accrual",
            "hook_execution_id": str(hook_id),
            "event_type": DAILY_ACCRUAL,
        },
    )

    return ScheduledEventHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[accrual_instruction])
        ],
        update_account_event_type_directives=[],
    )


def _handle_maturity_event(vault) -> ScheduledEventHookResult:
    denomination = vault.get_parameter_timeseries(name="denomination").latest()
    balances     = vault.get_balances_observation(fetcher_id="live_balances").balances
    accrued      = _get_committed_balance(balances, ACCRUED_INTEREST, denomination)

    if accrued <= Decimal("0"):
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    hook_id = vault.get_hook_execution_id()
    disbursement = CustomInstruction(
        postings=[
            Posting(
                credit=False,
                amount=accrued,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=ACCRUED_INTEREST,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=True,
                amount=accrued,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={
            "description": "Maturity disbursement",
            "hook_execution_id": str(hook_id),
            "event_type": MATURITY_EVENT,
        },
    )

    return ScheduledEventHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[disbursement])
        ],
        update_account_event_type_directives=[],
    )
