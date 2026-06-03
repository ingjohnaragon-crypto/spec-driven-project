from unittest import TestCase
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from ..types import (
    AccountConstraint,
    DateTimeConstraint,
    DateTimePrecision,
    DecimalConstraint,
    EnumerationConstraint,
    ExpectedParameter,
    StringConstraint,
    
)

from .....utils.exceptions import (
    StrongTypingError,
    InvalidSmartContractError,
)


from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)


class TestPublicCommonV400Constraints(TestCase):
    # DateTimeConstraint

    def test_date_time_constraint_repr(self):
        constraint = DateTimeConstraint(precision=DateTimePrecision.DAY)
        expected = "DateTimeConstraint(precision=DateTimePrecision.DAY, earliest=None, latest=None)"
        self.assertEqual(expected, repr(constraint))

    def test_date_time_constraint_equality(self):
        constraint = DateTimeConstraint(precision=DateTimePrecision.DAY)
        other_constraint = DateTimeConstraint(precision=DateTimePrecision.DAY)
        self.assertEqual(constraint, other_constraint)

    def test_date_time_constraint_default_precision(self):
        constraint = DateTimeConstraint()
        expected = DateTimePrecision.MINUTE
        self.assertEqual(expected, constraint.precision)

    def test_date_time_constraint_unequal_precision(self):
        constraint = DateTimeConstraint(precision=DateTimePrecision.DAY)
        other_constraint = DateTimeConstraint(precision=DateTimePrecision.MINUTE)

        self.assertNotEqual(constraint, other_constraint)

    def test_date_time_constraint_requires_precision_argument(self):
        with self.assertRaises(StrongTypingError) as ex:
            DateTimeConstraint(precision="")
        self.assertEqual(
            "'precision' expected DateTimePrecision value, got '' of type str", str(ex.exception)
        )

    def test_date_time_constraint_invalid_precision(self):
        with self.assertRaises(StrongTypingError) as ex:
            DateTimeConstraint(precision=27)
        expected = "'precision' expected DateTimePrecision value, got '27' of type int"
        self.assertEqual(expected, str(ex.exception))

    def test_date_time_constraint_stores_valid_arguments(self):
        earliest_datetime = datetime.fromtimestamp(1).replace(tzinfo=ZoneInfo("UTC"))
        latest_datetime = datetime.fromtimestamp(2).replace(tzinfo=ZoneInfo("UTC"))
        constraint = DateTimeConstraint(
            precision=DateTimePrecision.MINUTE,
            earliest=earliest_datetime,
            latest=latest_datetime,
        )
        self.assertEqual(DateTimePrecision.MINUTE, constraint.precision)
        self.assertEqual(earliest_datetime, constraint.earliest)
        self.assertEqual(latest_datetime, constraint.latest)

    def test_date_time_constraint_raises_with_naive_earliest_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateTimeConstraint(
                precision=DateTimePrecision.MINUTE,
                earliest=datetime.fromtimestamp(1),
            )
        expected = "'earliest' of DateTimeConstraint is not timezone aware."
        self.assertEqual(expected, str(ex.exception))

    def test_date_time_constraint_raises_with_naive_latest_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateTimeConstraint(
                precision=DateTimePrecision.MINUTE,
                latest=datetime.fromtimestamp(1),
            )
        expected = "'latest' of DateTimeConstraint is not timezone aware."
        self.assertEqual(expected, str(ex.exception))

    def test_date_time_constraint_raises_with_non_utc_earliest_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateTimeConstraint(
                precision=DateTimePrecision.MINUTE,
                earliest=datetime.fromtimestamp(1).replace(tzinfo=ZoneInfo("US/Pacific")),
            )
        expected = "'earliest' of DateTimeConstraint must have timezone UTC, currently US/Pacific."
        self.assertEqual(expected, str(ex.exception))

    def test_date_time_constraint_raises_with_non_utc_latest_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateTimeConstraint(
                precision=DateTimePrecision.MINUTE,
                latest=datetime.fromtimestamp(1).replace(tzinfo=ZoneInfo("US/Pacific")),
            )
        expected = "'latest' of DateTimeConstraint must have timezone UTC, currently US/Pacific."
        self.assertEqual(expected, str(ex.exception))

    def test_date_time_constraint_rejects_earliest_after_latest(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            DateTimeConstraint(
                precision=DateTimePrecision.MINUTE,
                earliest=datetime.fromtimestamp(10, timezone.utc).replace(tzinfo=ZoneInfo("UTC")),
                latest=datetime.fromtimestamp(1, timezone.utc).replace(tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "DateTimeConstraint earliest must be no later than latest "
            "(received 1970-01-01 00:00:10+00:00 > 1970-01-01 00:00:01+00:00)",
            str(e.exception),
        )

    def test_date_time_constraint_raises_with_invalid_date(self):
        with self.assertRaises(StrongTypingError) as ex:
            DateTimeConstraint(precision=DateTimePrecision.MINUTE, earliest="today")
        self.assertEqual("'earliest' expected datetime, got 'today' of type str", str(ex.exception))

    # DecimalConstraint

    def test_decimal_constraint_repr(self):
        constraint = DecimalConstraint(
            min_value=Decimal("1.2"),
            max_value=Decimal("123.4"),
        )
        expected = "DecimalConstraint(min_value=Decimal('1.2'), max_value=Decimal('123.4'))"
        self.assertEqual(expected, repr(constraint))

    def test_decimal_constraint_equality(self):
        constraint = DecimalConstraint(
            min_value=Decimal("1.2"),
            max_value=Decimal("123.4"),
        )
        other_constraint = DecimalConstraint(
            min_value=Decimal("1.2"),
            max_value=Decimal("123.4"),
        )
        self.assertEqual(constraint, other_constraint)

    def test_decimal_constraint_unequal_min_value(self):
        constraint = DecimalConstraint(
            min_value=Decimal("1.2"),
            max_value=Decimal("123.4"),
        )
        other_constraint = DecimalConstraint(
            min_value=Decimal("4.2"),
            max_value=Decimal("123.4"),
        )
        self.assertNotEqual(constraint, other_constraint)

    def test_decimal_constraint_stores_valid_arguments(self):
        constraint = DecimalConstraint(
            min_value=Decimal("1.2"),
            max_value=Decimal("123.4"),
        )
        self.assertEqual(Decimal("1.2"), constraint.min_value)
        self.assertEqual(Decimal("123.4"), constraint.max_value)

    def test_decimal_constraint_rejects_min_greater_than_max(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            DecimalConstraint(min_value=Decimal("10"), max_value=Decimal("9"))
        expected = (
            "DecimalConstraint 'min_value' must be less than or equal to 'max_value' "
            "(received 10 > 9)"
        )
        self.assertEqual(expected, str(e.exception))

    # EnumerationConstraint

    def test_enumeration_constraint_repr(self):
        constraint = EnumerationConstraint(permitted_values=["value-1", "value-2"])
        expected = "EnumerationConstraint(permitted_values=['value-1', 'value-2'])"
        self.assertEqual(expected, repr(constraint))

    def test_enumeration_constraint_equality(self):
        constraint = EnumerationConstraint(permitted_values=["value-1", "value-2"])
        other_constraint = EnumerationConstraint(permitted_values=["value-1", "value-2"])

        self.assertEqual(constraint, other_constraint)

    def test_enumeration_constraint_unequal_permitted_values(self):
        constraint = EnumerationConstraint(permitted_values=["value-1", "value-2"])
        other_constraint = EnumerationConstraint(permitted_values=["value-1", "value-3"])

        self.assertNotEqual(constraint, other_constraint)

    def test_enumeration_constraint_requires_permitted_values(self):
        with self.assertRaises(TypeError) as e:
            EnumerationConstraint()
        self.assertEqual(
            "EnumerationConstraint.__init__() missing 1 required "
            "keyword-only argument: 'permitted_values'",
            str(e.exception),
        )

    def test_enumeration_constraint_stores_valid_argument(self):
        constraint = EnumerationConstraint(permitted_values=["value-1", "value-2"])
        self.assertEqual(["value-1", "value-2"], constraint.permitted_values)

    def test_enumeration_constraint_from_proto_requires_list(self):
        with self.assertRaises(StrongTypingError) as e:
            EnumerationConstraint(permitted_values="not a list")
        self.assertEqual(
            "'permitted_values' expected list, got 'not a list' of type str", str(e.exception)
        )

    # AccountConstraint

    def test_account_constraint_repr(self):
        constraint = AccountConstraint()
        expected = "AccountConstraint()"
        self.assertEqual(expected, repr(constraint))

    def test_account_constraint_equality(self):
        constraint = AccountConstraint()
        other_constraint = AccountConstraint()

        self.assertEqual(constraint, other_constraint)

    # StringConstraint

    def test_string_constraint_repr(self):
        constraint = StringConstraint(min_length=1, max_length=10)
        expected = "StringConstraint(min_length=1, max_length=10)"
        self.assertEqual(expected, repr(constraint))

    def test_string_constraint_equality(self):
        constraint = StringConstraint(min_length=1, max_length=10)
        other_constraint = StringConstraint(min_length=1, max_length=10)

        self.assertEqual(constraint, other_constraint)

    def test_string_constraint_unequal_min_length(self):
        constraint = StringConstraint(min_length=1, max_length=10)
        other_constraint = StringConstraint(min_length=4, max_length=10)

        self.assertNotEqual(constraint, other_constraint)

    def test_string_constraint_accepts_no_arguments(self):
        constraint = StringConstraint()
        self.assertEqual(0, constraint.min_length)
        self.assertEqual(0, constraint.max_length)

    def test_string_constraint_accepts_none(self):
        constraint = StringConstraint(min_length=None, max_length=None)
        self.assertEqual(0, constraint.min_length)
        self.assertEqual(0, constraint.max_length)

    def test_string_constraint_stores_valid_arguments(self):
        constraint = StringConstraint(min_length=1, max_length=10)
        self.assertEqual(1, constraint.min_length)
        self.assertEqual(10, constraint.max_length)

    def test_string_constraint_stores_raises_invalid_argument(self):
        with self.assertRaises(StrongTypingError) as ex:
            StringConstraint(min_length=1, max_length="not a number")
        self.assertEqual("Expected int, got 'not a number' of type str", str(ex.exception))

    def test_string_constraint_rejects_negative_min_length(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            StringConstraint(min_length=-1, max_length=10)
        self.assertEqual(
            "StringConstraint min_length must be non-negative (received -1)", str(e.exception)
        )

    def test_string_constraint_rejects_negative_max_length(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            StringConstraint(min_length=1, max_length=-10)
        self.assertEqual(
            "StringConstraint max_length must be non-negative (received -10)", str(e.exception)
        )

    def test_string_constraint_rejects_empty_interval(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            StringConstraint(min_length=11, max_length=10)
        self.assertEqual(
            "StringConstraint min_length must be less than or equal to max_length "
            "(received 11 > 10)",
            str(e.exception),
        )


class TestPublicCommonV400ExpectedParameters(TestCase):
    def test_expected_parameter_repr(self):
        self.assertTrue(
            issubclass(ExpectedParameter, ContractsLanguageDunderMixin),
        )
        self.assertIn("ExpectedParameter", repr(ExpectedParameter))

    def test_expected_parameter_with_string_constraint(self):
        constraint = StringConstraint()
        expected_parameter = ExpectedParameter(
            id="parameter-id",
            constraint=constraint,
        )
        self.assertEqual("parameter-id", expected_parameter.id)
        self.assertEqual(constraint, expected_parameter.constraint)
        self.assertFalse(expected_parameter.optional)

    def test_expected_parameter_equality(self):
        constraint = StringConstraint(min_length=1, max_length=10)
        expected_parameter = ExpectedParameter(
            id="parameter-id",
            constraint=constraint,
            triggers_post_parameter_change_hook=True,
            triggers_pre_parameter_change_hook=False,
        )
        other_constraint = StringConstraint(min_length=1, max_length=10)
        other_expected_parameter = ExpectedParameter(
            id="parameter-id",
            constraint=other_constraint,
            triggers_post_parameter_change_hook=True,
            triggers_pre_parameter_change_hook=False,
        )
        self.assertEqual(expected_parameter, other_expected_parameter)

    def test_expected_parameter_unequal_constraint(self):
        constraint = StringConstraint(min_length=1, max_length=10)
        expected_parameter = ExpectedParameter(
            id="parameter-id",
            constraint=constraint,
        )
        other_constraint = StringConstraint(min_length=1, max_length=42)
        other_expected_parameter = ExpectedParameter(
            id="parameter-id",
            constraint=other_constraint,
        )
        self.assertNotEqual(expected_parameter, other_expected_parameter)

    def test_expected_parameter_with_account_constraint(self):
        constraint = AccountConstraint()
        expected_parameter = ExpectedParameter(
            id="parameter-id",
            constraint=constraint,
        )
        self.assertEqual(expected_parameter.id, "parameter-id")
        self.assertEqual(expected_parameter.constraint, constraint)

    def test_expected_parameter_raises_with_empty_id(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ExpectedParameter(id="", constraint=StringConstraint())
        self.assertEqual("ExpectedParameter 'id' must be populated", str(e.exception))

    def test_expected_parameter_with_no_constraint(self):
        expected_parameter = ExpectedParameter(id="parameter-id")
        self.assertEqual("parameter-id", expected_parameter.id)
        self.assertEqual(None, expected_parameter.constraint)

    def test_expected_parameter_raises_with_invalid_constraint(self):
        with self.assertRaises(StrongTypingError) as e:
            ExpectedParameter(id="parameter-id", constraint="not a constraint")
        expected = (
            "Expected Optional[Union[AccountConstraint, DateTimeConstraint, DecimalConstraint, "
            "EnumerationConstraint, StringConstraint]], got 'not a constraint' "
            "of type str"
        )
        self.assertEqual(expected, str(e.exception))

    def test_expected_parameter_with_optional_flag(self):
        expected_parameter = ExpectedParameter(
            id="parameter-id",
            optional=True,
        )
        self.assertEqual("parameter-id", expected_parameter.id)
        self.assertTrue(expected_parameter.optional)

    def test_expected_parameter_raises_with_invalid_optional_flag(self):
        with self.assertRaises(StrongTypingError) as ex:
            ExpectedParameter(id="parameter-id", optional="yes")
        self.assertEqual(
            "Expected Optional[bool] if populated, got 'yes' of type str", str(ex.exception)
        )

    def test_expected_parameter_pre_param_hook_execution_arguments_defaults_correctly(self):
        expected_parameter = ExpectedParameter(id="parameter-id")
        self.assertEqual("parameter-id", expected_parameter.id)
        self.assertIsNone(expected_parameter.triggers_pre_parameter_change_hook)

    def test_expected_parameter_raises_with_invalid_triggers_pre_parameter_change_hook_flag(self):
        with self.assertRaises(StrongTypingError) as ex:
            ExpectedParameter(id="parameter-id", triggers_pre_parameter_change_hook="yes")
        self.assertEqual(
            "Expected Optional[bool] if populated, got 'yes' of type str", str(ex.exception)
        )

    def test_expected_parameter_post_param_hook_execution_arguments_defaults_correctly(self):
        expected_parameter = ExpectedParameter(id="parameter-id")
        self.assertEqual("parameter-id", expected_parameter.id)
        self.assertIsNone(expected_parameter.triggers_post_parameter_change_hook)

    def test_expected_parameter_raises_with_invalid_triggers_post_parameter_change_hook_flag(self):
        with self.assertRaises(StrongTypingError) as ex:
            ExpectedParameter(
                id="parameter-id",
                triggers_pre_parameter_change_hook=True,
                triggers_post_parameter_change_hook="yes",
            )
        self.assertEqual(
            "Expected Optional[bool] if populated, got 'yes' of type str", str(ex.exception)
        )

    def test_expected_parameter_raises_when_post_parameter_change_hook_arg_defined_only(self):
        with self.assertRaises(ValueError) as ex:
            ExpectedParameter(id="parameter-id", triggers_post_parameter_change_hook=True)
        self.assertEqual(
            "Parameter with id=parameter-id: triggers_pre_parameter_change_hook must be explicitly "
            "defined if triggers_post_parameter_change_hook is explicitly defined.",
            str(ex.exception),
        )



