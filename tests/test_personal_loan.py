import importlib
from decimal import Decimal


def test_personal_loan_module_imports():
    """Basic smoke tests to ensure the contract module and expected hooks exist."""
    module = importlib.import_module('contracts.personal_loan')

    assert hasattr(module, 'activation_hook'), 'activation_hook missing'
    assert hasattr(module, 'scheduled_event_hook'), 'scheduled_event_hook missing'
    assert hasattr(module, 'pre_posting_code'), 'pre_posting_code missing'
    assert callable(module.activation_hook)
    assert callable(module.scheduled_event_hook)
    assert callable(module.pre_posting_code)


def test_helpers_present():
    module = importlib.import_module('contracts.personal_loan')
    assert hasattr(module, '_calculate_schedule')
    assert callable(module._calculate_schedule)


def test_calculate_schedule_annuity():
    """Verify annuity monthly payment and that total principal equals initial principal."""
    module = importlib.import_module('contracts.personal_loan')
    principal = Decimal('1000.00')
    annual_rate = Decimal('12')  # 12% per year
    term = 12

    schedule = module._calculate_schedule(principal, annual_rate, term, denomination='GBP')

    assert len(schedule) == term

    # All payments should be equal (annuity) except for tiny rounding adjustments
    payments = [entry['payment'] for entry in schedule]
    # Compare first payment with every other within 0.01 tolerance
    first_payment = payments[0]
    for p in payments[1:]:
        assert abs(p - first_payment) <= Decimal('0.01')

    # Sum of principal_due must equal the original principal (within rounding)
    total_principal = sum(entry['principal_due'] for entry in schedule)
    assert total_principal == principal.quantize(Decimal('0.01'))

    # First month's interest should equal principal * monthly_rate quantized
    monthly_rate = (annual_rate / Decimal('100')) / Decimal('12')
    expected_first_interest = (principal * monthly_rate).quantize(Decimal('0.01'))
    assert schedule[0]['interest_due'] == expected_first_interest


def test_scheduled_event_hook_returns_postings():
    """Call scheduled_event_hook with dict-like hook_arguments and verify postings."""
    module = importlib.import_module('contracts.personal_loan')

    hook_args = {
        'principal': '1200.00',
        'interest_rate': '12',
        'term_months': 12,
        'denomination': 'GBP',
        'period': 1,
    }

    result = module.scheduled_event_hook(hook_args)
    # result is either SDK CustomInstruction or dict fallback
    assert result is not None
    # If dict fallback, expect keys
    if isinstance(result, dict):
        assert 'postings' in result
        postings = result['postings']
    else:
        # SDK object — try to extract postings attribute
        postings = getattr(result, 'postings', None)

    assert postings is not None
    # Expect two postings: interest and principal
    assert len(postings) == 2

    # Confirm the amounts correspond to the schedule first period
    schedule = module._calculate_schedule(Decimal('1200.00'), Decimal('12'), 12, 'GBP')
    first = schedule[0]
    # postings may be dicts with 'amount' strings
    p_amounts = [Decimal(p['amount']) if isinstance(p, dict) else Decimal(getattr(p, 'amount', '0')) for p in postings]
    assert any(abs(a - first['interest_due']) <= Decimal('0.01') for a in p_amounts)
    assert any(abs(a - first['principal_due']) <= Decimal('0.01') for a in p_amounts)


def test_pre_posting_code_applies_penalty_and_reduction():
    module = importlib.import_module('contracts.personal_loan')

    hook_args = {
        'prepayment': {
            'amount': '200.00',
            'denomination': 'GBP',
        },
        'outstanding_principal': '1000.00',
        'prepayment_penalty': {'type': 'percent', 'value': '1.0'},  # 1%
    }

    result = module.pre_posting_code(hook_args)
    assert result is not None

    # If PrePostingHookResult wrapper returned, it might be the SDK object; support dict fallback
    if isinstance(result, dict) and result.get('rejection'):
        # unexpected rejection
        raise AssertionError(f'Unexpected rejection: {result}')

    instruction = None
    if isinstance(result, dict) and result.get('instruction'):
        instruction = result['instruction']
    elif isinstance(result, dict) and 'postings' in result:
        instruction = result
    else:
        # SDK object likely returned directly
        instruction = result

    assert instruction is not None

    postings = instruction.get('postings') if isinstance(instruction, dict) else getattr(instruction, 'postings', None)
    assert postings is not None
    # Expect penalty and principal reduction postings
    types = [p.get('type') if isinstance(p, dict) else getattr(p, 'type', None) for p in postings]
    assert 'penalty' in types
    assert 'prepayment_principal' in types


def test_pre_posting_code_rejects_denom_mismatch():
    module = importlib.import_module('contracts.personal_loan')

    hook_args = {
        'prepayment': {'amount': '100.00', 'denomination': 'USD'},
        'denomination': 'GBP',
        'outstanding_principal': '1000.00',
        'prepayment_penalty': {'type': 'percent', 'value': '1.0'},
    }

    result = module.pre_posting_code(hook_args)
    assert result is not None
    # Expect a rejection in dict fallback or SDK PrePostingHookResult
    if isinstance(result, dict):
        assert 'rejection' in result or (result.get('instruction') is None)
    else:
        # SDK object: try to detect rejection attribute
        rej = getattr(result, 'rejection', None)
        assert rej is not None


def test_pre_posting_code_rejects_overpay():
    module = importlib.import_module('contracts.personal_loan')

    hook_args = {
        'prepayment': {'amount': '2000.00', 'denomination': 'GBP'},
        'outstanding_principal': '1000.00',
        'prepayment_penalty': {'type': 'percent', 'value': '1.0'},
    }

    result = module.pre_posting_code(hook_args)
    assert result is not None
    if isinstance(result, dict):
        assert 'rejection' in result
    else:
        rej = getattr(result, 'rejection', None)
        assert rej is not None
