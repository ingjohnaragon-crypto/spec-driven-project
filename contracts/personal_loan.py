"""Vault Smart Contract (API 4.0) — Personal Loan (skeleton)

This file provides a focused, sandbox-safe skeleton for the personal loan
contract. It intentionally contains minimal implementation: hook signatures,
helpers and clear TODOs so tests and iterative development can proceed.

Follow the project Vault conventions: Decimal for money, no prohibited stdlib
imports, use hook_arguments.effective_datetime for time, and return
PrePostingHookResult(rejection=...) for rejections.
"""

from decimal import Decimal, ROUND_HALF_UP

# Note: contracts_api is provided by the Vault SDK in the runtime/test env.
# Import names here as hints; concrete usage will be implemented in follow-up commits.
try:
    from contracts_api import (
        CustomInstruction,
        PrePostingHookResult,
        Rejection,
        RejectionReason,
        Parameter,
        NumberShape,
        DenominationShape,
        Posting,
        ScheduledEvent,
    )
except Exception:
    # In unit-test environments where the SDK is not available at import time
    # the module-level imports should not break file parsing. Tests will mock
    # SDK objects as needed.
    CustomInstruction = object
    PrePostingHookResult = object
    Rejection = object
    RejectionReason = object
    Parameter = object
    NumberShape = object
    DenominationShape = object
    Posting = object
    ScheduledEvent = object


# Product parameter definitions (examples)
PRODUCT_PARAMETERS = [
    # Parameter(name, shape=NumberShape(...), description="...")
]


# -- Helpers --------------------------------------------------------------

def _quantize(amount: Decimal, scale: int = 2) -> Decimal:
    """Quantize money values to 'scale' decimal places using ROUND_HALF_UP."""
    exp = Decimal((0, (1,), -scale))  # Decimal('0.01') when scale=2
    return amount.quantize(exp, rounding=ROUND_HALF_UP)


def _calculate_schedule(principal: Decimal, annual_rate: Decimal, term_months: int, denomination: str):
    """Pure helper to compute a monthly amortization schedule (annuity).

    Conventions:
    - annual_rate is specified as percent (e.g. Decimal('5') for 5%% per year)
    - term_months is the number of monthly payments (integer)

    Returns a list of dict entries with keys:
      - period: int (1-based)
      - payment: Decimal (total payment for the period)
      - principal_due: Decimal
      - interest_due: Decimal
      - balance: Decimal (remaining principal after payment)

    Rounding: every monetary value is quantized to 2 decimal places using
    ROUND_HALF_UP. The algorithm keeps equal payments for each period where
    possible and adjusts the final principal tranche to clear rounding residuals.
    """
    if term_months <= 0:
        raise ValueError('term_months must be > 0')

    # Normalize inputs to Decimal
    principal = Decimal(principal)
    annual_rate = Decimal(annual_rate)
    n = int(term_months)

    # monthly rate as a decimal fraction (e.g. 0.01 for 1%%)
    monthly_rate = (annual_rate / Decimal('100')) / Decimal('12')

    schedule = []
    # If rate is zero, payment is simply principal/n
    if monthly_rate == Decimal('0'):
        payment = _quantize(principal / Decimal(n))
        remaining = _quantize(principal)
        for period in range(1, n + 1):
            principal_due = payment
            # For the last period, clear any remainder due to rounding
            if period == n:
                principal_due = _quantize(remaining)
            interest_due = _quantize(Decimal('0'))
            remaining = _quantize(remaining - principal_due)
            schedule.append({
                'period': period,
                'payment': _quantize(interest_due + principal_due),
                'principal_due': _quantize(principal_due),
                'interest_due': _quantize(interest_due),
                'balance': remaining,
            })
        return schedule

    # annuity payment formula: A = P * r / (1 - (1+r) ** -n)
    # compute (1+r) ** n with Decimal
    one_plus_r_pow_n = (Decimal('1') + monthly_rate) ** n
    annuity_payment = principal * monthly_rate / (Decimal('1') - (Decimal('1') / one_plus_r_pow_n))
    payment = _quantize(annuity_payment)

    remaining = _quantize(principal)

    for period in range(1, n + 1):
        interest_due = _quantize(remaining * monthly_rate)
        principal_due = _quantize(payment - interest_due)

        # Ensure we do not overpay principal in the final period due to rounding
        if principal_due > remaining:
            principal_due = _quantize(remaining)
            payment = _quantize(interest_due + principal_due)

        remaining = _quantize(remaining - principal_due)

        schedule.append({
            'period': period,
            'payment': payment,
            'principal_due': principal_due,
            'interest_due': interest_due,
            'balance': remaining,
        })

    # If any tiny residual remains (due to quantize), adjust the last entry
    if schedule and schedule[-1]['balance'] != Decimal('0.00'):
        residual = schedule[-1]['balance']
        schedule[-1]['principal_due'] = _quantize(schedule[-1]['principal_due'] + residual)
        schedule[-1]['payment'] = _quantize(schedule[-1]['payment'] + residual)
        schedule[-1]['balance'] = Decimal('0.00')

    return schedule


# -- Hooks (skeletons) ---------------------------------------------------

def activation_hook(hook_arguments):
    """Handle product activation: create initial postings to disburse principal.

    Expected to return a CustomInstruction or list of postings/instructions
    according to the Vault API conventions.
    """
    # TODO: Read parameters, build CustomInstruction to disburse principal
    # Example (pseudocode):
    # instruction = CustomInstruction(postings=[...], instruction_details={...})
    # return instruction
    return None


def scheduled_event_hook(hook_arguments):
    """Run scheduled amortization events (monthly)."""
    # TODO: Compute current schedule entry and return postings to apply interest+principal
    return None


def pre_posting_code(hook_arguments):
    """Validate and process prepayments submitted by clients.

    Should return a PrePostingHookResult with rejection when invalid, or None/empty
    to allow posting to continue. When applying penalties, construct the
    appropriate postings or CustomInstruction.
    """
    # TODO: Validate denomination, amount, calculate penalty, generate postings
    # Example (pseudocode):
    # if invalid:
    #     return PrePostingHookResult(rejection=Rejection(message="...", reason_code=RejectionReason.INCOMPATIBLE_AMOUNT))
    return None


def post_posting_code(hook_arguments):
    """Optional: handle post-posting tasks like bookkeeping or schedule updates."""
    # TODO: implement if needed
    return None


# Exported API (hooks) — names expected by the Vault runtime
__all__ = [
    'activation_hook',
    'scheduled_event_hook',
    'pre_posting_code',
    'post_posting_code',
    '_calculate_schedule',
]
