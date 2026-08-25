# contracts/personal_loan.py
# Vault Smart Contract — Personal Loan (amortising, monthly repayment, prepayment penalty)
# Contracts Language API 4.0

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
)
from decimal import Decimal, ROUND_HALF_UP

api = "4.0.0"
version = "1.0.0"
display_name = "Personal Loan"
summary = "Amortising personal loan with monthly repayments and prepayment penalty"
description = (
    "An asset product that disburses a principal at activation, collects monthly "
    "annuity repayments (interest + capital), and allows partial or full prepayment "
    "with a configurable penalty rate. After prepayment the installment is kept and "
    "the remaining term is shortened."
)
tside = Tside.ASSET
supported_denominations = ["GBP", "USD", "EUR", "COP"]

DEFAULT_ADDRESS = "DEFAULT"
DEFAULT_ASSET = "COMMERCIAL_BANK_MONEY"
PENALTY_INCOME = "PENALTY_INCOME"
INTERNAL_CONTRA = "INTERNAL_CONTRA"
MONTHLY_REPAYMENT = "MONTHLY_REPAYMENT"

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
        name="principal",
        shape=NumberShape(
            min_value=Decimal("0.01"),
            step=Decimal("0.01"),
        ),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Principal",
        description="Loan principal disbursed at activation.",
        default_value=Decimal("1000.00"),
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
        description="AER as a fraction (0.12 = 12%).",
        default_value=Decimal("0.12"),
    ),
    Parameter(
        name="term_months",
        shape=NumberShape(
            min_value=Decimal("1"),
            step=Decimal("1"),
        ),
        level=ParameterLevel.INSTANCE,
        update_permission=ParameterUpdatePermission.USER_EDITABLE,
        display_name="Term (months)",
        description="Number of monthly annuity instalments.",
        default_value=Decimal("12"),
    ),
    Parameter(
        name="repayment_day",
        shape=NumberShape(
            min_value=Decimal("1"),
            max_value=Decimal("28"),
            step=Decimal("1"),
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Repayment Day",
        description="Day of month (1-28) for the monthly repayment event.",
        default_value=Decimal("1"),
    ),
    Parameter(
        name="prepayment_penalty_rate",
        shape=NumberShape(
            min_value=Decimal("0"),
            max_value=Decimal("1"),
            step=Decimal("0.0001"),
        ),
        level=ParameterLevel.TEMPLATE,
        display_name="Prepayment Penalty Rate",
        description="Fraction of the prepaid amount charged as penalty (0.02 = 2%).",
        default_value=Decimal("0.02"),
    ),
]

event_types = [
    SmartContractEventType(name=MONTHLY_REPAYMENT),
]

event_types_groups = []

balance_observation_fetchers = [
    BalancesObservationFetcher(
        fetcher_id="live_balances",
        at=DefinedDateTime.LIVE,
    )
]


# ── Pure helpers ───────────────────────────────────────────────────────────────

def _quantize(amount: Decimal, scale: int = 2) -> Decimal:
    exp = Decimal((0, (1,), -scale))
    return Decimal(amount).quantize(exp, rounding=ROUND_HALF_UP)


def _monthly_rate(annual_rate: Decimal) -> Decimal:
    return Decimal(annual_rate) / Decimal("12")


def _build_amortization_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
) -> list:
    """Annuity schedule. annual_rate is a fraction (0.12 = 12%)."""
    if term_months <= 0:
        raise ValueError("term_months must be > 0")

    principal = Decimal(principal)
    annual_rate = Decimal(annual_rate)
    n = int(term_months)
    monthly_rate = _monthly_rate(annual_rate)
    schedule = []

    if monthly_rate == Decimal("0"):
        payment = _quantize(principal / Decimal(n))
        remaining = _quantize(principal)
        for period in range(1, n + 1):
            principal_due = payment if period < n else _quantize(remaining)
            remaining = _quantize(remaining - principal_due)
            schedule.append(
                {
                    "period": period,
                    "payment": _quantize(principal_due),
                    "principal_due": _quantize(principal_due),
                    "interest_due": Decimal("0.00"),
                    "balance": remaining,
                }
            )
        return schedule

    one_plus_r_pow_n = (Decimal("1") + monthly_rate) ** n
    annuity = principal * monthly_rate / (Decimal("1") - (Decimal("1") / one_plus_r_pow_n))
    payment = _quantize(annuity)
    remaining = _quantize(principal)

    for period in range(1, n + 1):
        interest_due = _quantize(remaining * monthly_rate)
        principal_due = _quantize(payment - interest_due)
        if principal_due > remaining:
            principal_due = _quantize(remaining)
            payment = _quantize(interest_due + principal_due)
        remaining = _quantize(remaining - principal_due)
        schedule.append(
            {
                "period": period,
                "payment": payment,
                "principal_due": principal_due,
                "interest_due": interest_due,
                "balance": remaining,
            }
        )

    if schedule and schedule[-1]["balance"] != Decimal("0.00"):
        residual = schedule[-1]["balance"]
        schedule[-1]["principal_due"] = _quantize(schedule[-1]["principal_due"] + residual)
        schedule[-1]["payment"] = _quantize(schedule[-1]["payment"] + residual)
        schedule[-1]["balance"] = Decimal("0.00")

    return schedule


def _installment_from_schedule(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
    schedule = _build_amortization_schedule(principal, annual_rate, term_months)
    return schedule[0]["payment"] if schedule else Decimal("0.00")


def _recompute_term_after_prepayment(
    outstanding: Decimal,
    installment: Decimal,
    annual_rate: Decimal,
) -> int:
    """Keep installment, shorten remaining months (ceil)."""
    outstanding = _quantize(outstanding)
    installment = _quantize(installment)
    if outstanding <= Decimal("0"):
        return 0
    if installment <= Decimal("0"):
        return 1
    monthly_rate = _monthly_rate(Decimal(annual_rate))
    if monthly_rate == Decimal("0"):
        n = int((outstanding / installment).to_integral_value(rounding=ROUND_HALF_UP))
        return max(n, 1)

    # Solve outstanding = installment * (1 - (1+r)^-n) / r  → n
    ratio = Decimal("1") - (outstanding * monthly_rate / installment)
    if ratio <= Decimal("0"):
        return 1
    # n = -log(ratio) / log(1+r) using Decimal exp via float only for log is forbidden —
    # iterate months (term is small).
    remaining = outstanding
    months = 0
    while remaining > Decimal("0") and months < 1200:
        months += 1
        interest = _quantize(remaining * monthly_rate)
        principal_due = _quantize(installment - interest)
        if principal_due <= Decimal("0"):
            principal_due = _quantize(remaining)
        if principal_due > remaining:
            principal_due = remaining
        remaining = _quantize(remaining - principal_due)
    return max(months, 1)


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


def _param(vault, name: str):
    return vault.get_parameter_timeseries(name=name).latest()


# ── Hooks ──────────────────────────────────────────────────────────────────────

def activation_hook(
    vault, hook_arguments: ActivationHookArguments
) -> ActivationHookResult:
    principal = Decimal(_param(vault, "principal"))
    term_months = int(_param(vault, "term_months"))
    denomination = _param(vault, "denomination")
    repayment_day = int(_param(vault, "repayment_day"))

    if principal <= Decimal("0"):
        raise ValueError("principal must be greater than zero.")
    if term_months < 1:
        raise ValueError("term_months must be at least 1.")

    start_dt = hook_arguments.effective_datetime
    monthly_schedule = ScheduledEvent(
        start_datetime=start_dt,
        expression=ScheduleExpression(
            day=str(repayment_day),
            hour="0",
            minute="0",
            second="0",
        ),
    )

    hook_id = vault.get_hook_execution_id()
    principal_q = _quantize(principal)
    disbursement = CustomInstruction(
        postings=[
            Posting(
                credit=False,
                amount=principal_q,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=True,
                amount=principal_q,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=INTERNAL_CONTRA,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={
            "description": "Loan principal disbursement",
            "hook_execution_id": str(hook_id),
        },
    )

    return ActivationHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[disbursement])
        ],
        scheduled_events_return_value={MONTHLY_REPAYMENT: monthly_schedule},
    )


def pre_posting_hook(
    vault, hook_arguments: PrePostingHookArguments
) -> PrePostingHookResult:
    denomination = _param(vault, "denomination")
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    outstanding = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)

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

    # For ASSET loan, repayments / prepayments reduce DEFAULT net (negative effect).
    if posting_net < Decimal("0"):
        repayment = abs(posting_net)
        if repayment > outstanding:
            return PrePostingHookResult(
                rejection=Rejection(
                    message="Prepayment amount exceeds outstanding principal.",
                    reason_code=RejectionReason.AGAINST_TNC,
                )
            )

    return PrePostingHookResult()


def post_posting_hook(
    vault, hook_arguments: PostPostingHookArguments
) -> PostPostingHookResult:
    denomination = _param(vault, "denomination")
    penalty_rate = Decimal(_param(vault, "prepayment_penalty_rate"))
    posting_net = _posting_net_effect(hook_arguments.posting_instructions, denomination)

    if posting_net >= Decimal("0"):
        return PostPostingHookResult(posting_instructions_directives=[])

    prepaid = abs(posting_net)
    penalty = _quantize(prepaid * penalty_rate)
    if penalty <= Decimal("0"):
        return PostPostingHookResult(posting_instructions_directives=[])

    hook_id = vault.get_hook_execution_id()
    penalty_instruction = CustomInstruction(
        postings=[
            Posting(
                credit=False,
                amount=penalty,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
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
            "description": "Prepayment penalty",
            "hook_execution_id": str(hook_id),
        },
    )
    return PostPostingHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[penalty_instruction])
        ]
    )


def scheduled_event_hook(
    vault, hook_arguments: ScheduledEventHookArguments
) -> ScheduledEventHookResult:
    if hook_arguments.event_type != MONTHLY_REPAYMENT:
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )
    return _handle_monthly_repayment(vault)


def _handle_monthly_repayment(vault) -> ScheduledEventHookResult:
    denomination = _param(vault, "denomination")
    annual_rate = Decimal(_param(vault, "annual_interest_rate"))
    original_principal = Decimal(_param(vault, "principal"))
    term_months = int(_param(vault, "term_months"))
    balances = vault.get_balances_observation(fetcher_id="live_balances").balances
    outstanding = _get_committed_balance(balances, DEFAULT_ADDRESS, denomination)

    if outstanding <= Decimal("0"):
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    installment = _installment_from_schedule(original_principal, annual_rate, term_months)
    monthly_rate = _monthly_rate(annual_rate)
    interest_due = _quantize(outstanding * monthly_rate)
    principal_due = _quantize(installment - interest_due)
    if principal_due < Decimal("0"):
        principal_due = Decimal("0.00")
    if principal_due > outstanding:
        principal_due = _quantize(outstanding)
        installment = _quantize(interest_due + principal_due)

    total = _quantize(interest_due + principal_due)
    if total <= Decimal("0"):
        return ScheduledEventHookResult(
            posting_instructions_directives=[],
            update_account_event_type_directives=[],
        )

    hook_id = vault.get_hook_execution_id()
    repayment = CustomInstruction(
        postings=[
            Posting(
                credit=True,
                amount=total,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
            Posting(
                credit=False,
                amount=total,
                denomination=denomination,
                account_id=vault.account_id,
                account_address=INTERNAL_CONTRA,
                asset=DEFAULT_ASSET,
                phase=Phase.COMMITTED,
            ),
        ],
        instruction_details={
            "description": "Monthly loan repayment (interest + capital)",
            "hook_execution_id": str(hook_id),
            "event_type": MONTHLY_REPAYMENT,
            "interest_due": str(interest_due),
            "principal_due": str(principal_due),
        },
    )

    return ScheduledEventHookResult(
        posting_instructions_directives=[
            PostingInstructionsDirective(posting_instructions=[repayment])
        ],
        update_account_event_type_directives=[],
    )
