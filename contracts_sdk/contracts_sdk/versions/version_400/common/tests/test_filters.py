from unittest import TestCase
from copy import deepcopy

from ..types import (
    BalancesFilter,
    FlagsFilter,
    ParametersFilter,
    
    CalendarsFilter,
    EventTypesFilter,
)
from .....utils.exceptions import (
    StrongTypingError,
    InvalidSmartContractError,
)
from .....utils.feature_flags import (
    skip_if_not_enabled,
    
    CALENDAR_FETCHERS,
    SCHEDULER_EXECUTION_TIMES,
)
from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)


class TestPublicCommonV400FlagsFilter(TestCase):
    test_flag_definition_ids = ["FLAG_1", "FLAG_2"]

    def test_flags_filter_repr(self):
        flags_filter = FlagsFilter(flag_definition_ids=self.test_flag_definition_ids)
        self.assertTrue(issubclass(FlagsFilter, ContractsLanguageDunderMixin))
        self.assertIn("FlagsFilter", repr(flags_filter))

    def test_flags_filter_flag_definition_ids_attribute(self):
        flags_filter = FlagsFilter(flag_definition_ids=self.test_flag_definition_ids)
        self.assertEqual(self.test_flag_definition_ids, flags_filter.flag_definition_ids)

    def test_flags_filter_equality(self):
        flags_filter_1 = FlagsFilter(flag_definition_ids=self.test_flag_definition_ids)
        flags_filter_2 = FlagsFilter(flag_definition_ids=deepcopy(self.test_flag_definition_ids))
        self.assertEqual(flags_filter_1, flags_filter_2)

    def test_flags_filter_unequal_flag_definition_ids(self):
        flags_filter_1 = FlagsFilter(flag_definition_ids=self.test_flag_definition_ids)
        flags_filter_2 = FlagsFilter(flag_definition_ids=["FLAG_1"])
        self.assertNotEqual(flags_filter_1, flags_filter_2)

    def test_flags_filter_raises_with_empty_list_flag_definition_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            FlagsFilter(flag_definition_ids=[])
        self.assertEqual(
            str(e.exception),
            "'FlagsFilter.flag_definition_ids' must be a non empty list, got []",
        )

    def test_flags_filter_raises_with_none_flag_definition_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            FlagsFilter(flag_definition_ids=None)
        self.assertEqual(
            str(e.exception),
            "'FlagsFilter.flag_definition_ids' must be a non empty list, got None",
        )

    def test_flags_filter_raises_with_no_flag_definition_ids_field(self):
        with self.assertRaises(TypeError) as e:
            FlagsFilter()
        self.assertEqual(
            str(e.exception),
            "FlagsFilter.__init__() missing 1 "
            "required keyword-only argument: 'flag_definition_ids'",
        )

    def test_flags_filter_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            FlagsFilter(flag_definition_ids=123)
        self.assertEqual(
            str(e.exception),
            "Expected list of str objects for 'FlagsFilter.flag_definition_ids', got '123'",
        )

    def test_flags_filter_raises_with_invalid_nested_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            FlagsFilter(flag_definition_ids=["string", 1])
        self.assertEqual(
            str(e.exception),
            "'FlagsFilter.flag_definition_ids[1]' expected str, got '1' of type int",
        )

    def test_flags_filter_raises_with_duplicate_flag_definition_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            FlagsFilter(flag_definition_ids=["FLAG_1", "FLAG_1"])
        self.assertEqual(
            str(e.exception),
            "'FlagsFilter.flag_definition_ids' must not contain any duplicates,"
            " got duplicates: ['FLAG_1']",
        )

    def test_flags_filter_doesnt_raise_with_empty_flag_definition_id(self):
        FlagsFilter(flag_definition_ids=[""])


class TestPublicCommonV400ParametersFilter(TestCase):
    test_parameter_ids = ["PARAMETER_1", "PARAMETER_2"]

    def test_parameters_filter_repr(self):
        parameters_filter = ParametersFilter(parameter_ids=self.test_parameter_ids)
        self.assertTrue(issubclass(ParametersFilter, ContractsLanguageDunderMixin))
        self.assertIn("ParametersFilter", repr(parameters_filter))

    def test_parameters_filter_parameter_ids_attribute(self):
        parameters_filter = ParametersFilter(parameter_ids=self.test_parameter_ids)
        self.assertEqual(self.test_parameter_ids, parameters_filter.parameter_ids)

    def test_parameters_filter_equality(self):
        parameters_filter_1 = ParametersFilter(parameter_ids=self.test_parameter_ids)
        parameters_filter_2 = ParametersFilter(parameter_ids=deepcopy(self.test_parameter_ids))
        self.assertEqual(parameters_filter_1, parameters_filter_2)

    def test_parameters_filter_unequal_parameter_ids(self):
        parameters_filter_1 = ParametersFilter(parameter_ids=self.test_parameter_ids)
        parameters_filter_2 = ParametersFilter(parameter_ids=["PARAMETER_1", "PARAMETER_22"])
        self.assertNotEqual(parameters_filter_1, parameters_filter_2)

    def test_parameters_filter_raises_with_empty_list_parameter_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersFilter(parameter_ids=[])
        self.assertEqual(
            str(e.exception),
            "'ParametersFilter.parameter_ids' must be a non empty list, got []",
        )

    def test_parameters_filter_raises_with_none_parameter_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersFilter(parameter_ids=None)
        self.assertEqual(
            str(e.exception),
            "'ParametersFilter.parameter_ids' must be a non empty list, got None",
        )

    def test_parameters_filter_raises_with_no_parameter_ids_field(self):
        with self.assertRaises(TypeError) as e:
            ParametersFilter()
        self.assertEqual(
            str(e.exception),
            "ParametersFilter.__init__() missing 1 "
            "required keyword-only argument: 'parameter_ids'",
        )

    def test_parameters_filter_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            ParametersFilter(parameter_ids=123)
        self.assertEqual(
            str(e.exception),
            "Expected list of str objects for 'ParametersFilter.parameter_ids', got '123'",
        )

    def test_parameters_filter_raises_with_invalid_nested_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            ParametersFilter(parameter_ids=["string", 1])
        self.assertEqual(
            str(e.exception),
            "'ParametersFilter.parameter_ids[1]' expected str, got '1' of type int",
        )

    def test_parameters_filter_raises_with_duplicate_parameter_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersFilter(parameter_ids=["PARAMETER_1", "PARAMETER_1"])
        self.assertEqual(
            str(e.exception),
            "'ParametersFilter.parameter_ids' must not contain any duplicates, "
            "got duplicates: ['PARAMETER_1']",
        )

    def test_parameters_filter_doesnt_raise_with_empty_parameter_id(self):
        ParametersFilter(parameter_ids=[""])





class TestPublicCommonV400BalancesFilter(TestCase):
    test_addresses = ["CUSTOM_ADDRESS", "DEFAULT_ADDRESS"]

    def test_balances_filter_repr(self):
        balances_filter = BalancesFilter(addresses=self.test_addresses)
        self.assertTrue(issubclass(BalancesFilter, ContractsLanguageDunderMixin))
        self.assertIn("BalancesFilter", repr(balances_filter))

    def test_balances_filter_addresses_attribute(self):
        balances_filter = BalancesFilter(addresses=self.test_addresses)
        self.assertEqual(self.test_addresses, balances_filter.addresses)

    def test_balances_filter_equality(self):
        balances_filter_1 = BalancesFilter(addresses=self.test_addresses)
        balances_filter_2 = BalancesFilter(addresses=deepcopy(self.test_addresses))
        self.assertEqual(balances_filter_1, balances_filter_2)

    def test_balances_filter_unequal_addresses(self):
        balances_filter_1 = BalancesFilter(addresses=self.test_addresses)
        balances_filter_2 = BalancesFilter(addresses=["CUSTOM_ADDRESS", "DEFAULT_ADDRESS42"])
        self.assertNotEqual(balances_filter_1, balances_filter_2)

    def test_balances_filter_raises_with_empty_list_addresses(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            BalancesFilter(addresses=[])
        self.assertEqual(
            str(e.exception), "'BalancesFilter.addresses' must be a non empty list, got []"
        )

    def test_balances_filter_raises_with_none_addresses(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            BalancesFilter(addresses=None)
        self.assertEqual(
            str(e.exception), "'BalancesFilter.addresses' must be a non empty list, got None"
        )

    def test_balances_filter_raises_with_no_addresses_field(self):
        with self.assertRaises(TypeError) as e:
            BalancesFilter()
        self.assertEqual(
            str(e.exception),
            "BalancesFilter.__init__() missing 1 required keyword-only argument: 'addresses'",
        )

    def test_balances_filter_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            BalancesFilter(addresses=123)
        self.assertEqual(
            str(e.exception),
            "Expected list of str objects for 'BalancesFilter.addresses', got '123'",
        )

    def test_balances_filter_raises_with_invalid_nested_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            BalancesFilter(addresses=["string", 1])
        self.assertEqual(
            str(e.exception),
            "'BalancesFilter.addresses[1]' expected str, got '1' of type int",
        )

    def test_balances_filter_raises_with_duplicate_addresses(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            BalancesFilter(addresses=["DEFAULT_ADDRESS", "DEFAULT_ADDRESS"])
        self.assertEqual(
            str(e.exception),
            "'BalancesFilter.addresses' must not contain any duplicates, "
            "got duplicates: ['DEFAULT_ADDRESS']",
        )

    def test_balances_filter_doesnt_raise_with_empty_parameter_id(self):
        BalancesFilter(addresses=[""])


class TestPublicCommonV400CalendarsFilter(TestCase):
    test_calendar_ids = ["CALENDAR_1", "CALENDAR_2"]

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_repr(self):
        calendars_filter = CalendarsFilter(calendar_ids=self.test_calendar_ids)
        self.assertTrue(issubclass(CalendarsFilter, ContractsLanguageDunderMixin))
        self.assertIn("CalendarsFilter", repr(calendars_filter))

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_calendar_ids_attribute(self):
        calendars_filter = CalendarsFilter(calendar_ids=self.test_calendar_ids)
        self.assertEqual(self.test_calendar_ids, calendars_filter.calendar_ids)

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_equality(self):
        calendars_filter_1 = CalendarsFilter(calendar_ids=self.test_calendar_ids)
        calendars_filter_2 = CalendarsFilter(calendar_ids=deepcopy(self.test_calendar_ids))

        self.assertEqual(calendars_filter_1, calendars_filter_2)

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_unequal_calendar_ids(self):
        calendars_filter_1 = CalendarsFilter(calendar_ids=self.test_calendar_ids)
        calendars_filter_2 = CalendarsFilter(calendar_ids=["DIFFERENT_CALENDAR"])

        self.assertNotEqual(calendars_filter_1, calendars_filter_2)

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_empty_list_calendar_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            CalendarsFilter(calendar_ids=[])
        self.assertEqual(
            "'CalendarsFilter.calendar_ids' must be a non empty list, got []",
            str(e.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_none_calendar_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            CalendarsFilter(calendar_ids=None)
        self.assertEqual(
            "'CalendarsFilter.calendar_ids' must be a non empty list, got None",
            str(e.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_no_calendar_ids_field(self):
        with self.assertRaises(TypeError) as e:
            CalendarsFilter()
        self.assertEqual(
            "CalendarsFilter.__init__() missing 1 "
            "required keyword-only argument: 'calendar_ids'",
            str(e.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            CalendarsFilter(calendar_ids=123)
        self.assertEqual(
            "Expected list of str objects for 'CalendarsFilter.calendar_ids', got '123'",
            str(e.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_invalid_nested_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            CalendarsFilter(calendar_ids=["string", 1])
        self.assertEqual(
            "'CalendarsFilter.calendar_ids[1]' expected str, got '1' of type int",
            str(e.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_duplicate_calendar_ids(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            CalendarsFilter(calendar_ids=["CALENDAR_1", "CALENDAR_1"])
        self.assertEqual(
            "'CalendarsFilter.calendar_ids' must not contain any duplicates, "
            "got duplicates: ['CALENDAR_1']",
            str(e.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_filter_raises_with_empty_calendar_ids_item_type(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            CalendarsFilter(calendar_ids=[""])
        self.assertEqual(
            "'CalendarsFilter.calendar_ids[0]' must be a non-empty string",
            str(e.exception),
        )


class TestPublicCommonV400LastScheduledEventDateTimesFilter(TestCase):
    test_event_types = ["EVENT_TYPE_1", "EVENT_TYPE_2"]

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_repr(self):
        lsedt_filter = EventTypesFilter(event_types=self.test_event_types)
        self.assertTrue(issubclass(EventTypesFilter, ContractsLanguageDunderMixin))
        self.assertIn("EventTypesFilter", repr(lsedt_filter))

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_event_types_attribute(self):
        lsedt_filter = EventTypesFilter(event_types=self.test_event_types)
        self.assertEqual(self.test_event_types, lsedt_filter.event_types)

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_equality(self):
        lsedt_filter_1 = EventTypesFilter(event_types=self.test_event_types)
        lsedt_filter_2 = EventTypesFilter(event_types=deepcopy(self.test_event_types))

        self.assertEqual(lsedt_filter_1, lsedt_filter_2)

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_unequal_event_types(self):
        lsedt_filter_1 = EventTypesFilter(event_types=self.test_event_types)
        lsedt_filter_2 = EventTypesFilter(event_types=["DIFFERENT_CALENDAR"])

        self.assertNotEqual(lsedt_filter_1, lsedt_filter_2)

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_empty_list_event_types(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            EventTypesFilter(event_types=[])
        self.assertEqual(
            "'EventTypesFilter.event_types' must be a non empty list, got []",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_none_event_types(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            EventTypesFilter(event_types=None)
        self.assertEqual(
            "'EventTypesFilter.event_types' must be a non empty list, got None",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_no_event_types_field(self):
        with self.assertRaises(TypeError) as e:
            EventTypesFilter()
        self.assertEqual(
            "EventTypesFilter.__init__() missing 1 "
            "required keyword-only argument: 'event_types'",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            EventTypesFilter(event_types=123)
        self.assertEqual(
            "Expected list of str objects for 'EventTypesFilter.event_types', got '123'",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_invalid_nested_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            EventTypesFilter(event_types=["string", 1])
        self.assertEqual(
            "'EventTypesFilter.event_types[1]' expected str, got '1' of type int",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_duplicate_event_types(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            EventTypesFilter(event_types=["CALENDAR_1", "CALENDAR_1"])
        self.assertEqual(
            "'EventTypesFilter.event_types' must not contain any duplicates, "
            "got duplicates: ['CALENDAR_1']",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_lsedt_filter_raises_with_empty_event_types_item_type(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            EventTypesFilter(event_types=[""])
        self.assertEqual(
            "'EventTypesFilter.event_types[0]' must be a non-empty string",
            str(e.exception),
        )
