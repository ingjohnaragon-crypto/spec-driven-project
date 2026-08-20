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
