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

    Attempts to read 'principal' and 'denomination' from hook_arguments and
    returns a CustomInstruction-like structure representing the disbursement.
    The returned structure is a SDK CustomInstruction when available or a
    dict fallback suitable for unit tests.
    """
    principal = _extract_value(hook_arguments, 'principal', 'amount', 'product_principal')
    denom = _extract_value(hook_arguments, 'denomination', 'denom', 'currency', default='GBP')

    if principal is None:
        return None

    try:
        principal = Decimal(principal)
    except Exception:
        return None

    principal_q = _quantize(principal)

    disbursement_posting = {
        'amount': str(principal_q),
        'denomination': denom,
        'narrative': 'Loan principal disbursement',
        'type': 'disbursement',
    }

    details = {
        'description': 'Activation disbursement',
    }

    return _build_custom_instruction([disbursement_posting], details)


def _build_rejection(message: str, reason_code=None):
    """Construct a Rejection object when available, otherwise return a dict."""
    try:
        # contracts_api.Rejection expects message and reason_code in the Vault SDK
        return Rejection(message=message, reason_code=reason_code)
    except Exception:
        return {'message': message, 'reason_code': reason_code}


def _build_preposting_result(rejection_obj=None, instruction=None):
    """Construct PrePostingHookResult or a compatible dict fallback."""
    try:
        if rejection_obj is not None:
            return PrePostingHookResult(rejection=rejection_obj)
        if instruction is not None:
            # Returning an instruction from pre_posting_code is acceptable in some SDKs
            return instruction
        return None
    except Exception:
        # Fallback representation
        return {'rejection': rejection_obj, 'instruction': instruction}


def _build_custom_instruction(postings, details=None):
    """Construct a CustomInstruction or dict fallback."""
    try:
        if details is None:
            details = {}
        return CustomInstruction(postings=postings, instruction_details=details)
    except Exception:
        return {'postings': postings, 'instruction_details': details}


def _calculate_penalty(amount: Decimal, penalty_config):
    """Compute penalty amount given a config {type: 'percent'|'fixed', value: Decimal}.

    Returns a Decimal penalty quantized to 2 decimals.
    """
    if not penalty_config:
        return Decimal('0.00')
    ptype = penalty_config.get('type') if isinstance(penalty_config, dict) else None
    pvalue = Decimal(penalty_config.get('value')) if isinstance(penalty_config, dict) and penalty_config.get('value') is not None else Decimal('0')

    if ptype == 'percent':
        penalty = (amount * (pvalue / Decimal('100')))
    else:
        # default to fixed
        penalty = pvalue

    return _quantize(Decimal(penalty))


def _extract_value(obj, *names, default=None):
    """Safe extractor: try attribute access then dict keys for each name in order."""
    for name in names:
        # attribute
        try:
            val = getattr(obj, name)
            if val is not None:
                return val
        except Exception:
            pass
        # dict-style
        try:
            val = obj[name]
            if val is not None:
                return val
        except Exception:
            pass
    return default


def scheduled_event_hook(hook_arguments):
    """Run scheduled amortization events (monthly).

    This implementation is conservative and runtime-agnostic: it attempts to
    read product parameters (principal, interest_rate, term_months, denomination)
    from common locations inside hook_arguments. If insufficient data is
    available it becomes a no-op (returns None).

    When it can determine the next payment period it builds a CustomInstruction
    with postings for interest and principal for that period and returns it.
    The Vault runtime can accept CustomInstruction or list of postings
    depending on the SDK; a dict fallback is returned when SDK classes are
    unavailable (useful for unit tests that inspect the returned structure).
    """
    # Attempt to read commonly named parameters
    principal = _extract_value(hook_arguments, 'principal', 'amount', 'product_principal')
    annual_rate = _extract_value(hook_arguments, 'interest_rate', 'annual_rate', 'rate')
    term_months = _extract_value(hook_arguments, 'term_months', 'term', 'months')
    denomination = _extract_value(hook_arguments, 'denomination', 'denom', 'currency', default='GBP')

    # If any required parameter is missing, do nothing
    if principal is None or annual_rate is None or term_months is None:
        return None

    # Normalize
    principal = Decimal(principal)
    annual_rate = Decimal(annual_rate)
    term_months = int(term_months)

    schedule = _calculate_schedule(principal, annual_rate, term_months, denomination)

    # Determine which period to execute. Many runtimes provide an explicit
    # period/index; try to extract it. Fallback to 1 (first unpaid period).
    period = _extract_value(hook_arguments, 'period', 'payment_period', 'next_period', default=1)
    try:
        period = int(period)
    except Exception:
        period = 1

    if period < 1 or period > len(schedule):
        # Nothing to do or invalid period
        return None

    entry = schedule[period - 1]

    # Build postings for interest and principal. The exact Posting shape comes
    # from the Vault SDK; construct a best-effort dict or SDK Posting when
    # available. Posting fields here are illustrative: account, amount, denomination, narrative
    interest_posting = {
        'amount': str(entry['interest_due']),
        'denomination': denomination,
        'narrative': f'Interest period {period}',
        'type': 'interest',
    }
    principal_posting = {
        'amount': str(entry['principal_due']),
        'denomination': denomination,
        'narrative': f'Principal repayment period {period}',
        'type': 'principal',
    }

    postings = [interest_posting, principal_posting]

    details = {
        'description': f'Monthly amortization period {period}',
    }

    return _build_custom_instruction(postings, details)


def pre_posting_code(hook_arguments):
    """Validate and process prepayments submitted by clients.

    This function attempts to find a prepayment request in hook_arguments in
    a few common locations. If found it validates denomination and amount
    against the provided balance (if available) and computes/apply the penalty
    according to a penalty configuration. If invalid, returns a
    PrePostingHookResult with a Rejection; otherwise returns a CustomInstruction
    containing postings that apply the penalty and reduce the principal.
    """
    # Try to find a declared 'prepayment' payload
    prepayment = _extract_value(hook_arguments, 'prepayment', 'prepay', 'payload', default=None)

    # If not found, look for postings that indicate a prepayment by convention
    if prepayment is None:
        # Some runtimes pass posting instructions directly
        postings_in = _extract_value(hook_arguments, 'postings', 'posting', 'postings_in', default=None)
        if postings_in:
            # Heuristic: if any posting has a 'type' or 'narrative' mentioning 'prepay'
            for p in postings_in:
                try:
                    narrative = p.get('narrative', '')
                    ptype = p.get('type', '')
                except Exception:
                    narrative = ''
                    ptype = ''
                if 'prepay' in narrative.lower() or 'prepay' in str(ptype).lower():
                    prepayment = p
                    break

    if prepayment is None:
        # No prepayment detected — nothing to validate
        return None

    # Extract amount and denom
    amount = _extract_value(prepayment, 'amount', 'value', 'principal_amount', default=None)
    denom = _extract_value(prepayment, 'denomination', 'denom', 'currency', default=None)

    if amount is None:
        return None

    amount = Decimal(amount)

    # Get current outstanding principal if available
    current_balance = _extract_value(hook_arguments, 'outstanding_principal', 'current_balance', 'balance', default=None)
    if current_balance is not None:
        try:
            current_balance = Decimal(current_balance)
        except Exception:
            current_balance = None

    # Get penalty configuration from parameters or product config
    penalty_cfg = _extract_value(hook_arguments, 'prepayment_penalty', 'penalty', 'prepay_penalty', default=None)

    # Validate denomination if product denomination exists
    product_denom = _extract_value(hook_arguments, 'denomination', 'denom', 'product_denom', default=None)
    if product_denom is not None and denom is not None and str(denom) != str(product_denom):
        rejection = _build_rejection(f'Prepayment in incorrect denomination: {denom} (expected {product_denom})', reason_code=getattr(RejectionReason, 'INCOMPATIBLE_AMOUNT', None))
        return _build_preposting_result(rejection_obj=rejection)

    # Validate amount does not exceed outstanding principal (if known)
    if current_balance is not None and amount > current_balance:
        rejection = _build_rejection('Prepayment amount exceeds outstanding principal', reason_code=getattr(RejectionReason, 'INSUFFICIENT_FUNDS', None))
        return _build_preposting_result(rejection_obj=rejection)

    # Compute penalty
    penalty_amount = _calculate_penalty(amount, penalty_cfg)

    # Build postings: penalty (fee) and principal reduction
    penalty_posting = {
        'amount': str(penalty_amount),
        'denomination': denom or product_denom or 'GBP',
        'narrative': 'Prepayment penalty',
        'type': 'penalty',
    }
    principal_reduction_posting = {
        'amount': str(_quantize(amount)),
        'denomination': denom or product_denom or 'GBP',
        'narrative': 'Prepayment principal reduction',
        'type': 'prepayment_principal',
    }

    instruction = _build_custom_instruction([penalty_posting, principal_reduction_posting], details={'description': 'Apply prepayment and penalty'})

    return _build_preposting_result(instruction=instruction)


def post_posting_code(hook_arguments):
    """Optional: handle post-posting tasks like bookkeeping or schedule updates.

    Currently a no-op placeholder to keep hooks explicit. Implementers can
    extend this to update any remote bookkeeping structures or emit events.
    """
    # No-op by design for now
    return None


# Exported API (hooks) — names expected by the Vault runtime
__all__ = [
    'activation_hook',
    'scheduled_event_hook',
    'pre_posting_code',
    'post_posting_code',
    '_calculate_schedule',
]
