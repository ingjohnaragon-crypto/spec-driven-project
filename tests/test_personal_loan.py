import importlib


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
