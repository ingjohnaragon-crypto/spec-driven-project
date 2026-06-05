from collections import defaultdict, namedtuple
from unittest import TestCase
from copy import deepcopy
from datetime import datetime, timezone
from contextlib import redirect_stderr
from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from ..types import (
    AccountIdShape,
    AdjustmentStrategy,
    AccountNotificationDirective,
    ActivationHookResult,
    CustomInstruction,
    DateShape,
    DateTimeView,
    DeactivationHookResult,
    DEFAULT_ADDRESS,
    DEFAULT_ASSET,
    DefinedDateTime,
    DenominationShape,
    DerivedParameterHookResult,
    EndOfMonthSchedule,
    fetch_account_data,
    FlagsObservation,
    HookName,
    Logger,
    Next,
    NumberShape,
    OptionalShape,
    OptionalValue,
    Override,
    Parameter,
    ParameterLevel,
    ParametersObservation,
    Phase,
    PlanNotificationDirective,
    Posting,
    PostingInstructionsDirective,
    PostingInstructionEnrichment,
    PostingInstructionRejectionReason,
    PostingInstructionType,
    PostParameterChangeHookResult,
    PreParameterChangeHookResult,
    PostParameterChangeAdjustmentHookResult,
    PostPostingAdjustmentHookResult,
    PostPostingHookResult,
    PrePostingHookResult,
    Previous,
    Rejection,
    RejectionReason,
    RelativeDateTime,
    requires,
    ScheduleExpression,
    ScheduledEvent,
    ScheduledEventAdjustmentHookResult,
    ScheduledEventHookResult,
    ScheduleFailover,
    ScheduleSkip,
    Shift,
    SmartContractDescriptor,
    StringShape,
    SupervisedHooks,
    SupervisionExecutionMode,
    SupervisorActivationHookResult,
    SupervisorConversionHookResult,
    SupervisorPostPostingHookResult,
    SupervisorPrePostingHookResult,
    SupervisorScheduledEventHookResult,
    Timeline,
    Tside,
    UnionItem,
    UnionItemValue,
    UnionShape,
    UpdateAccountEventTypeDirective,
    UpdatePlanEventTypeDirective,
    ParameterUpdatePermission,
    ConversionHookResult,
    AttributeHookResult,
    
)

from ..types import hook_results
from ..types.hook_results import (
    validate_account_directives,
    validate_supervisee_directives,
    
)

from .....utils import symbols
from .....utils.exceptions import (
    StrongTypingError,
    InvalidSmartContractError,
)
from .....utils.feature_flags import (
    is_fflag_enabled,
    skip_if_not_enabled,
    ACCOUNT_ATTRIBUTE_HOOK,
    ADJUSTMENTS,
    BOOKING_BALANCES,
    ENRICH_POSTING_INSTRUCTIONS,
    EXPECTED_PID_REJECTIONS,
    
)
from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)


class PublicCommonV400TypesTestCase(TestCase):
    test_account_id = "test_test_account_id"
    test_posting_instructions = [
        CustomInstruction(
            postings=[
                Posting(
                    amount=Decimal(1),
                    credit=True,
                    account_id="1",
                    denomination="GBP",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
                Posting(
                    amount=Decimal(1),
                    credit=False,
                    account_id="2",
                    denomination="GBP",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
            ],
        )
    ]
    test_account_notification_directives = [
        AccountNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key1": "value1"},
        )
    ]
    test_scheduled_events_return_value = {
        "event_1": ScheduledEvent(
            start_datetime=datetime(1970, 1, 1, second=1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(1970, 1, 1, second=2, tzinfo=ZoneInfo("UTC")),
            expression=ScheduleExpression(
                year="2000",
                month="1",
                day="1",
                hour="0",
                minute="0",
                second="0",
            ),
            skip=ScheduleSkip(
                end=datetime(1970, 1, 1, second=4, tzinfo=ZoneInfo("UTC")),
            ),
        ),
        "event_2": ScheduledEvent(
            start_datetime=datetime(1970, 1, 1, second=5, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(1970, 1, 1, second=6, tzinfo=ZoneInfo("UTC")),
            expression=ScheduleExpression(
                day_of_week="mon",
            ),
        ),
    }
    test_posting_instructions_directives = [
        PostingInstructionsDirective(
            client_batch_id="international-payment",
            value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            posting_instructions=test_posting_instructions,
        )
    ]
    test_posting_instructions_directive_with_rejection_reasons = PostingInstructionsDirective(
        client_batch_id="international-payment",
        value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
        posting_instructions=test_posting_instructions,
        non_blocking_rejection_reasons={
            PostingInstructionRejectionReason.INSUFFICIENT_FUNDS,
            PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID,
        },
    )
    test_scheduled_events_return_value = {
        "event_1": ScheduledEvent(
            start_datetime=datetime(1970, 1, 1, second=1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(1970, 1, 1, second=2, tzinfo=ZoneInfo("UTC")),
            expression=ScheduleExpression(
                year="2000",
                month="1",
                day="1",
                hour="0",
                minute="0",
                second="0",
            ),
            skip=ScheduleSkip(
                end=datetime(1970, 1, 1, second=3, tzinfo=ZoneInfo("UTC")),
            ),
        ),
        "event_2": ScheduledEvent(
            start_datetime=datetime(1970, 1, 1, second=5, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(1970, 1, 1, second=6, tzinfo=ZoneInfo("UTC")),
            expression=ScheduleExpression(
                day_of_week="mon",
            ),
        ),
    }
    test_update_account_event_type_directives = [
        UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
        )
    ]
    test_plan_notification_directives = [
        PlanNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key1": "value1"},
        )
    ]
    test_update_plan_event_type_directives = [
        UpdatePlanEventTypeDirective(
            event_type="event_type",
            skip=True,
        )
    ]
    test_supervisee_account_notification_directives = {
        test_account_id: [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
    }
    test_supervisee_posting_instructions_directives = {
        test_account_id: test_posting_instructions_directives
    }
    test_supervisee_update_account_event_type_directives = {
        test_account_id: [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
    }

    

    # Parameters

    def test_parameter(self):
        parameter = Parameter(
            name="day_of_month",
            description="Which day would you like interest to be paid?",
            display_name="Day of month to pay interest",
            level=ParameterLevel.GLOBAL,
            default_value=27,
            derived=False,
            shape=NumberShape(min_value=1, max_value=28, step=1),
        )
        self.assertEqual(parameter.default_value, 27)

    def test_parameter_init_validation(self):
        with self.assertRaises(TypeError) as ex:
            Parameter()
        self.assertEqual(
            str(ex.exception),
            "Parameter.__init__() missing 3 required keyword-only arguments: 'name', 'shape', and "
            "'level'",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name=None, shape=None, level=None)
        self.assertEqual(str(ex.exception), "Parameter attribute 'name' expected str, got None")

        with self.assertRaises(InvalidSmartContractError) as ex:
            Parameter(name="", shape=StringShape(), level=1)
        self.assertEqual(str(ex.exception), "Parameter attribute 'name' must be a non-empty string")

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name="name", shape=None, level=None)
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'shape' expected Union[AccountIdShape, DateShape, "
            "DenominationShape, NumberShape, OptionalShape, StringShape, UnionShape],"
            " got None",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name="name", shape=Decimal, level=None)
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'shape' expected Union[AccountIdShape, DateShape, "
            "DenominationShape, NumberShape, OptionalShape, StringShape, UnionShape], got "
            "'<class 'decimal.Decimal'>'",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name="name", shape=StringShape, level=None)
        self.assertEqual(
            str(ex.exception),
            "Parameter init arg 'shape' for parameter 'name' must be an instance of the "
            "StringShape class",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name="name", shape=StringShape(), level=None)
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'level' expected ParameterLevel, got None",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name="name", shape=StringShape(), level=1.0)
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'level' expected ParameterLevel, got '1.0' of type float",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(name="name", shape=StringShape(), level=ParameterLevel.INSTANCE, derived=1)
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'derived' expected bool if populated, got '1' of type int",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="name",
                shape=StringShape(),
                level=ParameterLevel.INSTANCE,
                derived=True,
                display_name=True,
            )
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'display_name' expected str if populated, got 'True' of type bool",
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="name",
                shape=StringShape(),
                level=ParameterLevel.INSTANCE,
                derived=True,
                display_name="display_name",
                description=StringShape(),
            )
        self.assertEqual(
            str(ex.exception),
            (
                "Parameter attribute 'description' expected str if populated, "
                + "got 'StringShape()' of type StringShape"
            ),
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="name",
                shape=StringShape(),
                level=ParameterLevel.INSTANCE,
                derived=True,
                display_name="display_name",
                description="description",
                default_value=StringShape(),
            )
        expected = (
            "Parameter attribute 'default_value' expected Union[Decimal, str, "
            + "datetime, OptionalValue, UnionItemValue, int] if populated, "
            + "got 'StringShape()' of type StringShape"
        )
        self.assertEqual(expected, str(ex.exception))

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="name",
                shape=OptionalShape(shape=StringShape()),
                level=ParameterLevel.INSTANCE,
                derived=False,
                display_name="display_name",
                description="description",
                default_value=OptionalValue(Decimal(1)),
                update_permission=True,
            )
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'update_permission' expected ParameterUpdatePermission if "
            "populated, got 'True' of type bool",
        )

    def test_parameter_cannot_use_optional_default_value(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            Parameter(
                name="overdraft_limit",
                level=ParameterLevel.TEMPLATE,
                description="Overdraft limit",
                shape=StringShape(),
                default_value=OptionalValue(1),
            )
        self.assertEqual(
            "Non optional shapes must have a non optional default value: overdraft_limit",
            str(ex.exception),
        )

    def test_parameter_invalid_default_value_raises_error(self):
        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="overdraft_limit",
                level=ParameterLevel.TEMPLATE,
                description="Overdraft limit",
                shape=StringShape(),
                default_value=500,
            )
        self.assertEqual(
            "Expected str, got '500' of type int",
            str(ex.exception),
        )

    def test_parameter_invalid_optional_default_value_raises_error(self):
        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="overdraft_limit",
                level=ParameterLevel.TEMPLATE,
                description="Overdraft limit",
                shape=OptionalShape(shape=StringShape()),
                default_value=500,
            )
        self.assertEqual(
            "Expected OptionalValue, got '500' of type int",
            str(ex.exception),
        )

        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="overdraft_limit",
                level=ParameterLevel.TEMPLATE,
                description="Overdraft limit",
                shape=OptionalShape(shape=StringShape()),
                default_value=OptionalValue(500),
            )
        self.assertEqual(
            "Expected str, got '500' of type int",
            str(ex.exception),
        )

    def test_optional_value_raises_with_invalid_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            OptionalValue(value=True)
        self.assertEqual(
            "'OptionalValue.value' expected Union[Decimal, str, datetime, UnionItemValue, int] "
            + "if populated, got 'True' of type bool",
            str(ex.exception),
        )

    def test_optional_value_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            OptionalValue(datetime(2022, 1, 1))
        self.assertEqual(
            "'value' of OptionalValue is not timezone aware.",
            str(ex.exception),
        )

    def test_optional_value_raises_with_non_utc_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            OptionalValue(datetime(2022, 1, 1, tzinfo=ZoneInfo("US/Pacific")))
        self.assertEqual(
            "'value' of OptionalValue must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_optional_value_raises_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            OptionalValue(datetime.fromtimestamp(1, timezone.utc))
        self.assertEqual(
            "'value' of OptionalValue must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_parameter_global_level(self):
        parameter = Parameter(
            name="day_of_month",
            description="Which day would you like interest to be paid?",
            display_name="Day of month to pay interest",
            level=ParameterLevel.GLOBAL,
            default_value=27,
            shape=NumberShape(min_value=1, max_value=28, step=1),
        )
        self.assertEqual(parameter.default_value, 27)

    def test_parameter_default_value_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            Parameter(
                name="day_of_month",
                description="Which day would you like interest to be paid?",
                display_name="Day of month to pay interest",
                level=ParameterLevel.GLOBAL,
                default_value=datetime(2022, 1, 1),
                shape=DateShape(
                    min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
                ),
            )
        self.assertEqual(
            "'default_value' of Parameter is not timezone aware.",
            str(ex.exception),
        )

    def test_parameter_default_value_raises_with_non_utc_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            Parameter(
                name="day_of_month",
                description="Which day would you like interest to be paid?",
                display_name="Day of month to pay interest",
                level=ParameterLevel.GLOBAL,
                default_value=datetime(2022, 1, 1, tzinfo=ZoneInfo("US/Pacific")),
                shape=DateShape(
                    min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
                ),
            )
        self.assertEqual(
            "'default_value' of Parameter must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_parameter_default_value_raises_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            Parameter(
                name="day_of_month",
                description="Which day would you like interest to be paid?",
                display_name="Day of month to pay interest",
                level=ParameterLevel.GLOBAL,
                default_value=datetime.fromtimestamp(1, timezone.utc),
                shape=DateShape(
                    min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
                ),
            )
        self.assertEqual(
            "'default_value' of Parameter must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_parameter_template_level(self):
        parameter = Parameter(
            name="overdraft_fee",
            description="Overdraft fee",
            display_name="Fee charged for balances over the overdraft limit",
            level=ParameterLevel.TEMPLATE,
            default_value=Decimal(15),
            shape=NumberShape(min_value=0, max_value=100, step=Decimal("0.01")),
        )
        self.assertEqual(parameter.default_value, Decimal(15))

    def test_parameter_instance_level(self):
        parameter = Parameter(
            name="minimum_interest_rate",
            description="Minimum interest rate",
            display_name="Minimum interest rate paid on positive balances",
            level=ParameterLevel.INSTANCE,
            update_permission=ParameterUpdatePermission.FIXED,
            derived=False,
            default_value=Decimal(1.0),
            shape=NumberShape(min_value=0, max_value=100, step=Decimal("0.01")),
        )
        self.assertEqual(parameter.default_value, Decimal(1.0))

    def test_parameter_string_shape(self):
        parameter = Parameter(
            name="string_parameter",
            description="template level string parameter",
            display_name="Test Parameter",
            level=ParameterLevel.TEMPLATE,
            shape=StringShape(),
        )
        self.assertTrue(isinstance(parameter.shape, StringShape))

    def test_parameter_account_id_shape(self):
        parameter = Parameter(
            name="account_id",
            description="template level account id parameter",
            display_name="Test Parameter",
            level=ParameterLevel.TEMPLATE,
            shape=AccountIdShape(),
        )
        self.assertTrue(isinstance(parameter.shape, AccountIdShape))

    def test_parameter_denomination_shape(self):
        parameter = Parameter(
            name="denomination",
            description="template level denomination parameter",
            display_name="Test Parameter",
            level=ParameterLevel.TEMPLATE,
            shape=DenominationShape(),
        )
        self.assertTrue(isinstance(parameter.shape, DenominationShape))

    def test_parameter_date_shape(self):
        date_shape = DateShape(
            min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
            max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
        )
        parameter = Parameter(
            name="bonus_date",
            description="Date account bonus will be paid",
            display_name="Bonus date",
            level=ParameterLevel.TEMPLATE,
            shape=date_shape,
        )
        self.assertEqual(parameter.shape, date_shape)

    def test_parameter_date_shape_min_date_raise_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime(2020, 1, 1),
                max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "'min_date' of DateShape is not timezone aware.",
            str(ex.exception),
        )

    def test_parameter_date_shape_min_date_raise_with_non_utc_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("US/Pacific")),
                max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "'min_date' of DateShape must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_parameter_date_shape_min_date_raise_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime.fromtimestamp(1, timezone.utc),
                max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "'min_date' of DateShape must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_parameter_date_shape_max_date_raise_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                max_date=datetime(2020, 3, 31),
            )
        self.assertEqual(
            "'max_date' of DateShape is not timezone aware.",
            str(ex.exception),
        )

    def test_parameter_date_shape_max_date_raise_with_non_utc_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                max_date=datetime(2020, 3, 31, tzinfo=ZoneInfo("US/Pacific")),
            )
        self.assertEqual(
            "'max_date' of DateShape must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_parameter_date_shape_max_date_raise_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                max_date=datetime.fromtimestamp(1, timezone.utc),
            )
        self.assertEqual(
            "'max_date' of DateShape must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_parameter_not_using_shape_instance(self):
        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="day_of_month",
                description="Which day would you like interest to be paid?",
                display_name="Day of month to pay interest",
                level=ParameterLevel.GLOBAL,
                default_value=27,
                derived=False,
                shape=NumberShape,
            )
        self.assertEqual(
            str(ex.exception),
            "Parameter init arg 'shape' for parameter 'day_of_month' must be an instance of the "
            "NumberShape class",
        )

    def test_parameter_invalid_shape(self):
        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="day_of_month",
                description="Which day would you like interest to be paid?",
                display_name="Day of month to pay interest",
                level=ParameterLevel.GLOBAL,
                default_value=27,
                derived=False,
                shape=Decimal,
            )
        self.assertEqual(
            str(ex.exception),
            "Parameter attribute 'shape' expected Union[AccountIdShape, DateShape, "
            "DenominationShape, NumberShape, OptionalShape, StringShape, UnionShape], got "
            "'<class 'decimal.Decimal'>'",
        )

    def test_derived_parameters_cannot_have_default_values(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            Parameter(
                name="overdraft_limit",
                level=ParameterLevel.INSTANCE,
                description="Overdraft limit",
                shape=StringShape(),
                default_value="1",
                derived=True,
            )
        self.assertEqual(
            "Derived Parameters cannot have a default value or update permissions: "
            "overdraft_limit",
            str(ex.exception),
        )

    def test_parameter_default_value_multiple_optional_value(self):
        with self.assertRaises(StrongTypingError) as ex:
            Parameter(
                name="day_of_month",
                description="Which day would you like interest to be paid?",
                display_name="Day of month to pay interest",
                level=ParameterLevel.GLOBAL,
                derived=False,
                shape=OptionalShape(shape=NumberShape()),
                default_value=OptionalValue(OptionalValue(1)),
            )
        expected = (
            "'OptionalValue.value' expected Union[Decimal, str, datetime, UnionItemValue, int] "
            + "if populated, got 'OptionalValue(value=1)' of type OptionalValue"
        )
        self.assertEqual(expected, str(ex.exception))

    # Shapes

    # NumberShape

    def test_number_shape_init(self):
        with self.assertRaises(StrongTypingError) as ex:
            NumberShape(min_value="")
        self.assertEqual(
            str(ex.exception),
            "'min_value' expected Union[Decimal, int] if populated, got '' " "of type str",
        )

        with self.assertRaises(StrongTypingError) as ex:
            NumberShape(min_value=1, max_value="")
        self.assertEqual(
            str(ex.exception),
            "'max_value' expected Union[Decimal, int] if populated, got '' of type str",
        )

        with self.assertRaises(StrongTypingError) as ex:
            NumberShape(min_value=1, max_value=2, step="")
        self.assertEqual(
            str(ex.exception),
            "'step' expected Union[Decimal, int] if populated, got '' of type str",
        )

        with self.assertRaises(InvalidSmartContractError) as ex:
            NumberShape(min_value=2, max_value=1)
        self.assertEqual(str(ex.exception), "NumberShape min_value must be less than max_value")

        valid_number_shape = NumberShape(min_value=1, max_value=2, step=Decimal(0.01))
        self.assertEqual(valid_number_shape.min_value, 1)
        self.assertEqual(valid_number_shape.max_value, 2)
        self.assertEqual(valid_number_shape.step, Decimal(0.01))

    def test_number_shape_repr(self):
        shape = NumberShape(min_value=1, max_value=5, step=1)
        expected = "NumberShape(min_value=1, max_value=5, step=1)"
        self.assertEqual(expected, repr(shape))

    def test_number_shape_equality(self):
        shape = NumberShape(min_value=1, max_value=2)
        other_shape = NumberShape(min_value=1, max_value=2)

        self.assertEqual(shape, other_shape)

    def test_number_shape_unequal_max_value(self):
        shape = NumberShape(min_value=1, max_value=2)
        other_shape = NumberShape(min_value=1, max_value=42)

        self.assertNotEqual(shape, other_shape)

    # StringShape

    def test_string_shape_repr(self):
        shape = StringShape()
        expected = "StringShape()"
        self.assertEqual(expected, repr(shape))

    def test_string_shape_equality(self):
        shape = StringShape()
        other_shape = StringShape()

        self.assertEqual(shape, other_shape)

    # DateShape

    def test_date_shape_init(self):
        with self.assertRaises(StrongTypingError) as ex:
            DateShape(min_date="")
        self.assertEqual(
            str(ex.exception), "'min_date' expected datetime if populated, got '' of type str"
        )

        with self.assertRaises(StrongTypingError) as ex:
            DateShape(min_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")), max_date="")
        self.assertEqual(
            str(ex.exception), "'max_date' expected datetime if populated, got '' of type str"
        )

        with self.assertRaises(InvalidSmartContractError) as ex:
            DateShape(
                min_date=datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC")),
                max_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(str(ex.exception), "DateShape min_date must be less than max_date")

        valid_date_shape_1 = DateShape()
        valid_date_shape_2 = DateShape(min_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")))
        valid_date_shape_3 = DateShape(max_date=datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC")))

        self.assertEqual(valid_date_shape_1.min_date, None)
        self.assertEqual(valid_date_shape_1.max_date, None)
        self.assertEqual(valid_date_shape_2.min_date, datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(valid_date_shape_2.max_date, None)
        self.assertEqual(valid_date_shape_3.min_date, None)
        self.assertEqual(valid_date_shape_3.max_date, datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC")))

    def test_date_shape_repr(self):
        shape = DateShape(min_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")))
        expected = (
            "DateShape(min_date=datetime.datetime(1999, 1, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), max_date=None)"
        )
        self.assertEqual(expected, repr(shape))

    def test_date_shape_equality(self):
        shape = DateShape(min_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")))
        other_shape = DateShape(min_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")))

        self.assertEqual(shape, other_shape)

    def test_date_shape_unequal_min_date(self):
        shape = DateShape(min_date=datetime(1999, 1, 1, tzinfo=ZoneInfo("UTC")))
        other_shape = DateShape(min_date=datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC")))

        self.assertNotEqual(shape, other_shape)

    # AccountIdShape

    def test_account_id_shape_repr(self):
        shape = AccountIdShape()
        expected = "AccountIdShape()"
        self.assertEqual(expected, repr(shape))

    def test_account_id_shape_equality(self):
        shape = AccountIdShape()
        other_shape = AccountIdShape()

        self.assertEqual(shape, other_shape)

    # DenominationShape

    def test_denomination_shape_repr(self):
        shape = DenominationShape(permitted_denominations=["GBP"])
        expected = "DenominationShape(permitted_denominations=['GBP'])"
        self.assertEqual(expected, repr(shape))

    def test_denomination_shape_equality(self):
        shape = DenominationShape(permitted_denominations=["GBP"])
        other_shape = DenominationShape(permitted_denominations=["GBP"])

        self.assertEqual(shape, other_shape)

    def test_denomination_shape_unequal_max_value(self):
        shape = DenominationShape(permitted_denominations=["GBP"])
        other_shape = DenominationShape(permitted_denominations=["USD"])

        self.assertNotEqual(shape, other_shape)

    # UnionShape

    def test_union_shape_init(self):
        with self.assertRaises(TypeError) as ex:
            UnionShape()
        self.assertEqual(
            str(ex.exception),
            "UnionShape.__init__() missing 1 required keyword-only argument: 'items'",
        )

        with self.assertRaises(StrongTypingError) as ex:
            UnionShape(items=1)
        self.assertEqual(
            str(ex.exception),
            "UnionShape __init__ Expected list of UnionItem objects for " "'items', got '1'",
        )

        with self.assertRaises(InvalidSmartContractError) as ex:
            UnionShape(items=[])
        self.assertEqual(str(ex.exception), "'items' must be a non empty list, got []")

        with self.assertRaises(StrongTypingError) as ex:
            UnionShape(items=[1, 2, 3])
        self.assertEqual(
            str(ex.exception), "UnionShape __init__ Expected UnionItem, got '1' of type int"
        )

        with self.assertRaises(InvalidSmartContractError) as ex:
            UnionShape(
                items=[
                    UnionItem(key="key_1", display_name="display_name_1"),
                    UnionItem(key="key_1", display_name="display_name_2"),
                ]
            )
        self.assertEqual(str(ex.exception), "Parameter contains duplicate UnionItem key_1")

        union_item = UnionItem(key="key", display_name="display_name")
        valid_union_shape = UnionShape(items=[union_item])
        self.assertEqual(valid_union_shape.items[0], union_item)

    def test_union_shape_repr(self):
        union_item = UnionItem(key="key", display_name="display_name")
        shape = UnionShape(items=[union_item])
        expected = "UnionShape(items=[UnionItem(key='key', display_name='display_name')])"
        self.assertEqual(expected, repr(shape))

    def test_union_shape_equality(self):
        union_item = UnionItem(key="key", display_name="display_name")
        shape = UnionShape(items=[union_item])

        other_union_item = UnionItem(key="key", display_name="display_name")
        other_shape = UnionShape(items=[other_union_item])

        self.assertEqual(shape, other_shape)

    def test_union_shape_unequal_items(self):
        union_item = UnionItem(key="key", display_name="display_name")
        shape = UnionShape(items=[union_item])

        other_union_item = UnionItem(key="key", display_name="display_eman")
        other_shape = UnionShape(items=[other_union_item])

        self.assertNotEqual(shape, other_shape)

    # UnionItem

    def test_union_item_init(self):
        with self.assertRaises(StrongTypingError) as ex:
            UnionItem(key=None, display_name=None)
        self.assertEqual(str(ex.exception), "UnionItem init arg 'key' must be populated")

        with self.assertRaises(StrongTypingError) as ex:
            UnionItem(key="", display_name=None)
        self.assertEqual(str(ex.exception), "UnionItem init arg 'key' must be populated")

        with self.assertRaises(StrongTypingError) as ex:
            UnionItem(key="KEY", display_name=None)
        self.assertEqual(str(ex.exception), "UnionItem init arg 'display_name' must be populated")

        with self.assertRaises(StrongTypingError) as ex:
            UnionItem(key="KEY", display_name="")
        self.assertEqual(str(ex.exception), "UnionItem init arg 'display_name' must be populated")

        valid_union_item = UnionItem(key="KEY", display_name="display_name")
        self.assertEqual(valid_union_item.key, "KEY")
        self.assertEqual(valid_union_item.display_name, "display_name")

    def test_union_item_repr(self):
        item = UnionItem(key="KEY", display_name="display_name")
        expected = "UnionItem(key='KEY', display_name='display_name')"
        self.assertEqual(expected, repr(item))

    def test_union_item_equality(self):
        item = UnionItem(key="bob", display_name="ken")
        other_item = UnionItem(key="bob", display_name="ken")
        self.assertEqual(item, other_item)

    def test_union_item_unequal_key(self):
        item = UnionItem(key="bob", display_name="ken")
        other_item = UnionItem(key="alice", display_name="ken")
        self.assertNotEqual(item, other_item)

    # UnionItemValue

    def test_union_item_value_repr(self):
        value = UnionItemValue(key="KEY")
        expected = "UnionItemValue(key='KEY')"
        self.assertEqual(expected, repr(value))

    def test_union_item_value_equality(self):
        value = UnionItemValue(key="bob")
        other_value = UnionItemValue(key="bob")
        self.assertEqual(value, other_value)

    def test_union_item_value_unequal_key(self):
        value = UnionItemValue(key="bob")
        other_value = UnionItemValue(key="alice")
        self.assertNotEqual(value, other_value)

    # OptionalShape

    def test_optional_shape_init(self):
        with self.assertRaises(TypeError) as ex:
            OptionalShape()
        self.assertEqual(
            str(ex.exception),
            "OptionalShape.__init__() missing 1 required keyword-only argument: 'shape'",
        )

        with self.assertRaises(TypeError) as ex:
            OptionalShape(1)
        self.assertEqual(
            str(ex.exception),
            "OptionalShape.__init__() takes 1 positional argument but 2 were given",
        )

        with self.assertRaises(StrongTypingError) as ex:
            OptionalShape(shape=1)
        self.assertEqual(
            str(ex.exception),
            "'shape' expected Union[AccountIdShape, DateShape, DenominationShape, NumberShape, "
            "StringShape, UnionShape], got '1' of type int",
        )

        with self.assertRaises(StrongTypingError) as ex:
            OptionalShape(shape=StringShape)
        self.assertEqual(
            str(ex.exception),
            "OptionalShape init arg 'shape' must be an instance of StringShape class",
        )

        shape = StringShape()
        valid_optional_shape = OptionalShape(shape=shape)
        self.assertEqual(valid_optional_shape.shape, shape)

    def test_optional_shape_repr(self):
        optional_value = OptionalShape(
            shape=NumberShape(min_value=1, max_value=2, step=Decimal("0.01"))
        )
        expected = (
            "OptionalShape(shape=NumberShape(min_value=1, max_value=2, step=Decimal('0.01')))"
        )
        self.assertEqual(expected, repr(optional_value))

    def test_optional_shape_equality(self):
        optional_value = OptionalShape(
            shape=NumberShape(min_value=1, max_value=2, step=Decimal(0.01))
        )
        other_optional_value = OptionalShape(
            shape=NumberShape(min_value=1, max_value=2, step=Decimal(0.01))
        )

        self.assertEqual(optional_value, other_optional_value)

    def test_optional_shape_unequal_shape(self):
        optional_value = OptionalShape(
            shape=NumberShape(min_value=1, max_value=2, step=Decimal(0.01))
        )
        other_optional_value = OptionalShape(
            shape=NumberShape(min_value=1, max_value=42, step=Decimal(0.01))
        )

        self.assertNotEqual(optional_value, other_optional_value)

    # OptionalValue

    def test_optional_value_init(self):
        with self.assertRaises(StrongTypingError) as ex:
            OptionalValue(AccountIdShape())
        expected = (
            "'OptionalValue.value' expected Union[Decimal, str, datetime, UnionItemValue, int] "
            + "if populated, got 'AccountIdShape()' of type AccountIdShape"
        )
        self.assertEqual(str(ex.exception), expected)

        with self.assertRaises(StrongTypingError) as ex:
            OptionalValue([])
        self.assertEqual(
            str(ex.exception),
            "'OptionalValue.value' expected Union[Decimal, str, datetime, UnionItemValue, int] "
            + "if populated, got '[]' of type list",
        )

        self.assertEqual(OptionalValue("").value, "")

        valid_optional_value = OptionalValue(1)
        self.assertEqual(valid_optional_value.value, 1)
        self.assertEqual(valid_optional_value.is_set(), True)
        valid_optional_value.value = None
        self.assertEqual(valid_optional_value.is_set(), False)

    def test_optional_value_repr(self):
        value = OptionalValue(45)
        expected = "OptionalValue(value=45)"
        self.assertEqual(expected, repr(value))

    def test_optional_value_equality(self):
        optional_value = OptionalValue(1)
        other_optional_value = OptionalValue(1)
        self.assertEqual(optional_value, other_optional_value)

    def test_optional_value_unequal_value(self):
        optional_value = OptionalValue(1)
        other_optional_value = OptionalValue(42)
        self.assertNotEqual(optional_value, other_optional_value)

    # Enums

    def test_posting_instruction_type_enum(self):
        self.assertEqual(PostingInstructionType.AUTHORISATION.value, "Authorisation")
        self.assertEqual(
            PostingInstructionType.AUTHORISATION_ADJUSTMENT.value,
            "AuthorisationAdjustment",
        )
        self.assertEqual(PostingInstructionType.CUSTOM_INSTRUCTION.value, "CustomInstruction")
        self.assertEqual(PostingInstructionType.HARD_SETTLEMENT.value, "HardSettlement")
        self.assertEqual(PostingInstructionType.RELEASE.value, "Release")
        self.assertEqual(PostingInstructionType.SETTLEMENT.value, "Settlement")
        self.assertEqual(PostingInstructionType.TRANSFER.value, "Transfer")

    def test_phase_enum(self):
        self.assertEqual(Phase.PENDING_IN.value, "pending_in")
        self.assertEqual(Phase.PENDING_OUT.value, "pending_out")
        self.assertEqual(Phase.COMMITTED.value, "committed")

    def test_tside_enum(self):
        self.assertEqual(Tside.ASSET.value, 1)
        self.assertEqual(Tside.LIABILITY.value, 2)

    def test_level_enum(self):
        self.assertEqual(ParameterLevel.GLOBAL.value, 1)
        self.assertEqual(ParameterLevel.TEMPLATE.value, 2)
        self.assertEqual(ParameterLevel.INSTANCE.value, 3)

    def test_rejection_reason_enum(self):
        self.assertEqual(RejectionReason.UNKNOWN_REASON.value, 0)
        self.assertEqual(RejectionReason.INSUFFICIENT_FUNDS.value, 1)
        self.assertEqual(RejectionReason.WRONG_DENOMINATION.value, 2)
        self.assertEqual(RejectionReason.AGAINST_TNC.value, 3)
        self.assertEqual(RejectionReason.CLIENT_CUSTOM_REASON.value, 4)

    def test_update_permission_enum(self):
        self.assertEqual(ParameterUpdatePermission.PERMISSION_UNKNOWN.value, 0)
        self.assertEqual(ParameterUpdatePermission.FIXED.value, 1)
        self.assertEqual(ParameterUpdatePermission.OPS_EDITABLE.value, 2)
        self.assertEqual(ParameterUpdatePermission.USER_EDITABLE.value, 3)
        self.assertEqual(ParameterUpdatePermission.USER_EDITABLE_WITH_OPS_PERMISSION.value, 4)

    def test_supervision_execution_mode_enum(self):
        self.assertEqual(SupervisionExecutionMode.OVERRIDE.value, 1)
        self.assertEqual(SupervisionExecutionMode.INVOKED.value, 2)

    def test_timeline_enum(self):
        self.assertEqual(Timeline.PRESENT.value, 1)
        self.assertEqual(Timeline.FUTURE.value, 2)

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_adjustment_strategy_enum(self):
        self.assertEqual(AdjustmentStrategy.SCHEDULE_TRIGGERED.value, 1)

    @skip_if_not_enabled(BOOKING_BALANCES)
    def test_fetcher_datetimeview_enum(self):
        self.assertEqual(DateTimeView.VALUE_DATETIME.value, 2)
        self.assertEqual(DateTimeView.BOOKING_DATETIME.value, 3)

    def test_hoook_name_enum(self):
        self.assertEqual(HookName.UNKNOWN_HOOK.value, 0)
        self.assertEqual(HookName.ACTIVATION_HOOK.value, 1)
        self.assertEqual(HookName.SCHEDULED_EVENT_HOOK.value, 2)
        self.assertEqual(HookName.DEACTIVATION_HOOK.value, 3)
        self.assertEqual(HookName.CONVERSION_HOOK.value, 4)
        self.assertEqual(HookName.POST_PARAMETER_CHANGE_HOOK.value, 5)
        self.assertEqual(HookName.PRE_PARAMETER_CHANGE_HOOK.value, 6)
        self.assertEqual(HookName.PRE_POSTING_HOOK.value, 7)
        self.assertEqual(HookName.POST_POSTING_HOOK.value, 8)
        self.assertEqual(HookName.DERIVED_PARAMETERS_HOOK.value, 9)
        self.assertEqual(HookName.ATTRIBUTE_HOOK.value, 10)
        self.assertEqual(HookName.SCHEDULED_EVENT_ADJUSTMENT_HOOK.value, 11)
        self.assertEqual(HookName.POST_POSTING_ADJUSTMENT_HOOK.value, 12)
        self.assertEqual(HookName.POST_PARAMETER_CHANGE_ADJUSTMENT_HOOK.value, 13)

    # SupervisorActivationHookResult

    def test_supervisor_activation_hook_result(self):
        supervisor_activation_hook_result = SupervisorActivationHookResult(
            scheduled_events_return_value=self.test_scheduled_events_return_value
        )
        self.assertEqual(
            self.test_scheduled_events_return_value,
            supervisor_activation_hook_result.scheduled_events_return_value,
        )
        self.assertIsNone(supervisor_activation_hook_result.rejection)

    def test_supervisor_activation_hook_result_repr(self):
        supervisor_activation_hook_result = SupervisorActivationHookResult(
            scheduled_events_return_value=self.test_scheduled_events_return_value
        )
        expected = (
            "SupervisorActivationHookResult(scheduled_events_return_value={'event_1': "
            + "ScheduledEvent(start_datetime=datetime.datetime(1970, 1, 1, 0, 0, 1, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), "
            + "end_datetime=datetime.datetime(1970, 1, 1, 0, 0, 2, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), expression=ScheduleExpression(second='0', "
            + "minute='0', hour='0', day='1', month='1', day_of_week=None, year='2000'), "
            + "schedule_method=None, skip=ScheduleSkip(end=datetime.datetime(1970, 1, 1, 0, 0, 3, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')))), 'event_2': "
            + "ScheduledEvent(start_datetime=datetime.datetime(1970, 1, 1, 0, 0, 5, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), "
            + "end_datetime=datetime.datetime(1970, 1, 1, 0, 0, 6, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), expression="
            + "ScheduleExpression(second=None, minute=None, hour=None, day=None, "
            + "month=None, day_of_week='mon', year=None), schedule_method=None, skip=False)}, "
            + "rejection=None)"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(supervisor_activation_hook_result))

    def test_supervisor_activation_hook_result_equality(self):
        supervisor_activation_hook_result = SupervisorActivationHookResult(
            scheduled_events_return_value=self.test_scheduled_events_return_value
        )
        other_scheduled_events_return_value = {
            "event_1": ScheduledEvent(
                start_datetime=datetime(1970, 1, 1, second=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(1970, 1, 1, second=2, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(
                    year="2000",
                    month="1",
                    day="1",
                    hour="0",
                    minute="0",
                    second="0",
                ),
                skip=ScheduleSkip(
                    end=datetime(1970, 1, 1, second=3, tzinfo=ZoneInfo("UTC")),
                ),
            ),
            "event_2": ScheduledEvent(
                start_datetime=datetime(1970, 1, 1, second=5, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(1970, 1, 1, second=6, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(
                    day_of_week="mon",
                ),
            ),
        }
        other_supervisor_activation_hook_result = SupervisorActivationHookResult(
            scheduled_events_return_value=other_scheduled_events_return_value
        )

        self.assertEqual(
            supervisor_activation_hook_result,
            other_supervisor_activation_hook_result,
        )

    def test_supervisor_activation_hook_result_unequal_scheduled_events_return_value(self):
        supervisor_activation_hook_result = SupervisorActivationHookResult(
            scheduled_events_return_value=self.test_scheduled_events_return_value
        )
        other_scheduled_events_return_value = {
            "event_1": ScheduledEvent(
                start_datetime=datetime(1970, 1, 1, second=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(1970, 1, 1, second=2, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(
                    year="2000",
                    month="1",
                    day="1",
                    hour="0",
                    minute="0",
                    second="0",
                ),
                skip=ScheduleSkip(
                    end=datetime(1970, 1, 1, second=5, tzinfo=ZoneInfo("UTC")),
                ),
            ),
            "event_2": ScheduledEvent(
                start_datetime=datetime(1970, 1, 1, second=5, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(1970, 1, 1, second=6, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(
                    day_of_week="mon",
                ),
            ),
        }
        other_supervisor_activation_hook_result = SupervisorActivationHookResult(
            scheduled_events_return_value=other_scheduled_events_return_value
        )

        self.assertNotEqual(
            supervisor_activation_hook_result,
            other_supervisor_activation_hook_result,
        )

    

    def test_supervisor_activation_hook_result_no_events(self):
        supervisor_activation_hook_result = SupervisorActivationHookResult()
        self.assertEqual({}, supervisor_activation_hook_result.scheduled_events_return_value)
        

    # SupervisorConversionHookResult

    def test_supervisor_conversion_hook_result(self):
        supervisor_conversion_hook_result = SupervisorConversionHookResult(
            scheduled_events_return_value=self.test_scheduled_events_return_value
        )
        self.assertEqual(
            self.test_scheduled_events_return_value,
            supervisor_conversion_hook_result.scheduled_events_return_value,
        )
        

    def test_supervisor_conversion_hook_result_no_events(self):
        supervisor_conversion_hook_result = SupervisorConversionHookResult()
        self.assertEqual({}, supervisor_conversion_hook_result.scheduled_events_return_value)
        

    

    # FlagsObservation

    def test_flags_observation(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        flags = {"flag_def_1": True, "flag_def_2": False}
        flags_observation = FlagsObservation(
            flags=deepcopy(flags), value_datetime=deepcopy(value_datetime)
        )
        self.assertEqual(value_datetime, flags_observation.value_datetime)
        self.assertEqual(flags, flags_observation.flags)

    def test_flags_observation_no_value_datetime(self):
        flags = {"flag_def_1": True, "flag_def_2": False}
        flags_observation = FlagsObservation(flags=deepcopy(flags))
        self.assertIsNone(flags_observation.value_datetime)
        self.assertEqual(flags, flags_observation.flags)

    def test_flags_observation_equality(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        flags = {"flag_def_1": True, "flag_def_2": False}
        flags_observation_1 = FlagsObservation(flags=flags, value_datetime=value_datetime)
        flags_observation_2 = FlagsObservation(
            flags=deepcopy(flags), value_datetime=deepcopy(value_datetime)
        )
        self.assertEqual(flags_observation_1, flags_observation_2)

    def test_flags_observation_equality_different_from_proto(self):
        """Should be equal if all public attributes are equal by value."""
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        flags = {"flag_def_1": True, "flag_def_2": False}
        flags_observation_1 = FlagsObservation(flags=flags, value_datetime=value_datetime)
        flags_observation_2 = FlagsObservation(
            flags=deepcopy(flags), value_datetime=deepcopy(value_datetime), _from_proto=True
        )
        self.assertEqual(flags_observation_1, flags_observation_2)

    def test_flags_observation_unequal_flags(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        flags_1 = {"flag_def_1": True, "flag_def_2": False}
        flags_2 = {"flag_def_1": False, "flag_def_2": False}
        flags_observation_1 = FlagsObservation(flags=flags_1, value_datetime=value_datetime)
        flags_observation_2 = FlagsObservation(flags=flags_2, value_datetime=value_datetime)
        self.assertNotEqual(flags_observation_1, flags_observation_2)

    def test_flags_observation_unequal_datetime(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        christmas_day = datetime(year=2022, month=12, day=25, tzinfo=ZoneInfo("UTC"))
        flags = {"flag_def_1": True, "flag_def_2": False}
        flags_observation_1 = FlagsObservation(flags=flags, value_datetime=value_datetime)
        flags_observation_2 = FlagsObservation(flags=flags, value_datetime=christmas_day)
        self.assertNotEqual(flags_observation_1, flags_observation_2)

    def test_flags_observation_repr(self):
        christmas_day = datetime(year=2022, month=12, day=25, tzinfo=ZoneInfo("UTC"))
        flags = {"flag_def_1": True, "flag_def_2": False}
        flags_observation = FlagsObservation(flags=flags, value_datetime=christmas_day)
        expected_repr = (
            "FlagsObservation(flags={'flag_def_1': True, 'flag_def_2': False}, "
            "value_datetime=datetime.datetime(2022, 12, 25, 0, 0, "
            "tzinfo=zoneinfo.ZoneInfo(key='UTC')))"
        )
        self.assertEqual(expected_repr, repr(flags_observation))

    def test_flags_observation_repr_empty_flags(self):
        flags_observation = FlagsObservation(flags=defaultdict(lambda: False), value_datetime=None)
        expected_repr = "FlagsObservation(flags={}, value_datetime=None)"
        self.assertEqual(expected_repr, repr(flags_observation))

    def test_flags_observation_raises_error_with_wrong_flags_type(self):
        with self.assertRaises(StrongTypingError) as e:
            christmas_day = datetime(year=2022, month=12, day=25, tzinfo=ZoneInfo("UTC"))
            FlagsObservation(flags=1, value_datetime=christmas_day)
        self.assertEqual(
            "'FlagsObservation.flags' expected dict[str, bool], got '1' of type int",
            str(e.exception),
        )

    def test_flags_observation_raises_error_with_wrong_value_datetime_type(self):
        with self.assertRaises(StrongTypingError) as e:
            flags = {"flag_def_1": True, "flag_def_2": False}
            FlagsObservation(flags=flags, value_datetime=1)
        self.assertEqual(
            "'FlagsObservation.value_datetime' expected datetime if populated, got '1' of type int",
            str(e.exception),
        )

    def test_flags_observation_raises_error_with_value_datetime_not_timezone_aware(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            naive_datetime = datetime(year=2020, month=2, day=20)
            flags = {"flag_def_1": True, "flag_def_2": False}
            FlagsObservation(flags=flags, value_datetime=naive_datetime)
        self.assertEqual(
            "'value_datetime' of FlagsObservation is not timezone aware.", str(e.exception)
        )

    def test_flags_observation_raises_with_non_utc_timezone(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("US/Pacific"))
        flags = {"flag_def_1": True, "flag_def_2": False}
        with self.assertRaises(InvalidSmartContractError) as e:
            FlagsObservation(flags=flags, value_datetime=value_datetime)
        self.assertEqual(
            str(e.exception),
            "'value_datetime' of FlagsObservation must have timezone UTC, currently " "US/Pacific.",
        )

    def test_flags_observation_raises_with_non_zoneinfo_timezone(self):
        value_datetime = datetime.fromtimestamp(1, timezone.utc)
        flags = {"flag_def_1": True, "flag_def_2": False}
        with self.assertRaises(InvalidSmartContractError) as e:
            FlagsObservation(flags=flags, value_datetime=value_datetime)
        self.assertEqual(
            "'value_datetime' of FlagsObservation must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    def test_flags_observation_no_value_datetime_and_empty_balances(self):
        flags = {}
        flags_observation = FlagsObservation(flags=flags)
        self.assertIsNone(flags_observation.value_datetime)
        self.assertEqual({}, flags_observation.flags)

    # Shift, Override, Next, Previous

    def test_time_operations_equality(self):
        shift = Shift(years=3, months=1, days=12, hours=4, minutes=5, seconds=6)
        override = Override(year=2000, month=1, day=12)
        next = Next(month=1, day=12, hour=4, minute=5, second=6)
        previous = Previous(month=1, day=12, hour=6, minute=7, second=25)
        relative_date_time = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Next(month=1, day=12, hour=4, minute=5, second=6),
        )

        other_shift = Shift(years=3, months=1, days=12, hours=4, minutes=5, seconds=6)
        other_override = Override(year=2000, month=1, day=12)
        other_next = Next(month=1, day=12, hour=4, minute=5, second=6)
        other_previous = Previous(month=1, day=12, hour=6, minute=7, second=25)
        other_relative_date_time = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Next(month=1, day=12, hour=4, minute=5, second=6),
        )

        self.assertEqual(shift, other_shift)
        self.assertEqual(override, other_override)
        self.assertEqual(next, other_next)
        self.assertEqual(previous, other_previous)
        self.assertEqual(relative_date_time, other_relative_date_time)

    def test_time_operations_unequal_month(self):
        shift = Shift(years=3, months=1, days=12, hours=4, minutes=5, seconds=6)
        override = Override(year=2000, month=1, day=12)
        next = Next(month=1, day=12, hour=4, minute=5, second=6)
        previous = Previous(month=1, day=12, hour=6, minute=7, second=25)
        relative_date_time = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Next(month=1, day=12, hour=4, minute=5, second=6),
        )

        other_shift = Shift(years=3, months=2, days=12, hours=4, minutes=5, seconds=6)
        other_override = Override(year=2000, month=2, day=12)
        other_next = Next(month=2, day=12, hour=4, minute=5, second=6)
        other_previous = Previous(month=2, day=12, hour=6, minute=7, second=25)
        other_relative_date_time = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Next(month=2, day=12, hour=4, minute=5, second=6),
        )

        self.assertNotEqual(shift, other_shift)
        self.assertNotEqual(override, other_override)
        self.assertNotEqual(next, other_next)
        self.assertNotEqual(previous, other_previous)
        self.assertNotEqual(relative_date_time, other_relative_date_time)

    def test_shift_with_positive_values(self):
        shift = Shift(years=3, months=1, days=12, hours=4, minutes=5, seconds=6)
        self.assertEqual(3, shift.years)
        self.assertEqual(1, shift.months)
        self.assertEqual(12, shift.days)
        self.assertEqual(4, shift.hours)
        self.assertEqual(5, shift.minutes)
        self.assertEqual(6, shift.seconds)

    def test_shift_with_negative_values(self):
        shift = Shift(years=-4, months=-3, days=-2, hours=-10, minutes=-25, seconds=-45)
        self.assertEqual(-4, shift.years)
        self.assertEqual(-3, shift.months)
        self.assertEqual(-2, shift.days)
        self.assertEqual(-10, shift.hours)
        self.assertEqual(-25, shift.minutes)
        self.assertEqual(-45, shift.seconds)

    def test_shift_with_only_time_attribute_values(self):
        shift = Shift(hours=7, minutes=8, seconds=25)
        self.assertEqual(7, shift.hours)
        self.assertEqual(8, shift.minutes)
        self.assertEqual(25, shift.seconds)

    def test_shift_with_optional_values_not_provided(self):
        shift_missing_months = Shift(years=4, days=2, hours=-10, minutes=-25, seconds=-45)
        shift_missing_days = Shift(years=4, months=3, hours=-10, minutes=-25, seconds=-45)
        shift_missing_years = Shift(months=3, days=2, hours=-10, minutes=-25, seconds=-45)
        shift_missing_hours = Shift(years=4, months=3, days=2, minutes=25, seconds=45)
        shift_missing_minutes = Shift(years=2, days=2, months=3, hours=10, seconds=45)
        shift_missing_seconds = Shift(years=2, days=2, months=3, hours=10, minutes=25)

        # Confirm that values are populated with zero if left empty.
        self.assertEqual(None, shift_missing_years.years)
        self.assertEqual(None, shift_missing_months.months)
        self.assertEqual(None, shift_missing_days.days)
        self.assertEqual(None, shift_missing_hours.hours)
        self.assertEqual(None, shift_missing_minutes.minutes)
        self.assertEqual(None, shift_missing_seconds.seconds)

    def test_shift_repr(self):
        shift = Shift(years=2, months=3, days=-2, hours=-10, minutes=25, seconds=-45)
        expected = "Shift(years=2, months=3, days=-2, hours=-10, minutes=25, seconds=-45)"
        self.assertEqual(expected, repr(shift))

    def test_shift_raises_if_no_values_provided(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Shift()

        self.assertEqual(
            str(e.exception), "Shift object needs to be populated with at least one attribute."
        )

    def test_shift_raises_if_invalid_year_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Shift(years="1")
        self.assertEqual(
            str(e.exception), "'Shift.years' expected int if populated, got '1' of type str"
        )

    def test_shift_raises_if_invalid_month_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Shift(months="1")
        self.assertEqual(
            str(e.exception), "'Shift.months' expected int if populated, got '1' of type str"
        )

    def test_shift_raises_if_invalid_day_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Shift(days="1")
        self.assertEqual(
            str(e.exception), "'Shift.days' expected int if populated, got '1' of type str"
        )

    def test_shift_raises_if_invalid_hour_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Shift(hours="1")
        self.assertEqual(
            str(e.exception), "'Shift.hours' expected int if populated, got '1' of type str"
        )

    def test_shift_raises_if_invalid_minute_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Shift(minutes="1")
        self.assertEqual(
            str(e.exception), "'Shift.minutes' expected int if populated, got '1' of type str"
        )

    def test_shift_raises_if_invalid_second_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Shift(seconds="1")
        self.assertEqual(
            str(e.exception), "'Shift.seconds' expected int if populated, got '1' of type str"
        )

    def test_defined_date_time_enum(self):
        self.assertEqual(DefinedDateTime.LIVE.value, -1)
        self.assertEqual(DefinedDateTime.INTERVAL_START.value, 2)
        self.assertEqual(DefinedDateTime.EFFECTIVE_DATETIME.value, 3)
        with self.assertRaises(AttributeError):
            DefinedDateTime.EFFECTIVE_TIME

    def test_failover_enum(self):
        self.assertEqual(ScheduleFailover.FIRST_VALID_DAY_BEFORE.value, 1)
        self.assertEqual(ScheduleFailover.FIRST_VALID_DAY_AFTER.value, 2)

    def test_override_repr(self):
        override = Override(year=2000, month=1, day=12, hour=4, minute=5, second=6)
        expected = "Override(year=2000, month=1, day=12, hour=4, minute=5, second=6)"
        self.assertEqual(expected, repr(override))

    def test_override_with_valid_values(self):
        override = Override(year=2000, month=1, day=12, hour=4, minute=5, second=6)
        self.assertEqual(2000, override.year)
        self.assertEqual(1, override.month)
        self.assertEqual(12, override.day)
        self.assertEqual(4, override.hour)
        self.assertEqual(5, override.minute)
        self.assertEqual(6, override.second)

    def test_override_with_time_attributes_not_populated(self):
        override = Override(year=2000, month=1, day=12)
        self.assertEqual(2000, override.year)
        self.assertEqual(1, override.month)
        self.assertEqual(12, override.day)
        self.assertEqual(None, override.hour)
        self.assertEqual(None, override.minute)
        self.assertEqual(None, override.second)

    def test_override_with_optional_date_attribute_not_populated(self):
        override = Override(year=2000, day=12)
        self.assertEqual(2000, override.year)
        self.assertEqual(None, override.month)
        self.assertEqual(12, override.day)
        self.assertEqual(None, override.hour)
        self.assertEqual(None, override.minute)
        self.assertEqual(None, override.second)

    def test_override_raises_if_no_values_provided(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Override()

        self.assertEqual(
            str(e.exception), "Override object needs to be populated with at least one attribute."
        )

    def test_override_raises_if_invalid_year_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(year="1")
        self.assertEqual(
            str(e.exception),
            "'Override.year' expected int if populated, got '1' of type str",
        )

    def test_override_raises_if_invalid_month_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(month="1")
        self.assertEqual(
            str(e.exception),
            "'Override.month' expected int if populated, got '1' of type str",
        )

    def test_override_raises_if_invalid_day_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(day="1")
        self.assertEqual(
            str(e.exception),
            "'Override.day' expected int if populated, got '1' of type str",
        )

    def test_override_raises_if_invalid_hour_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(hour="1")
        self.assertEqual(
            str(e.exception),
            "'Override.hour' expected int if populated, got '1' of type str",
        )

    def test_override_raises_if_invalid_minute_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(minute="1")
        self.assertEqual(
            str(e.exception),
            "'Override.minute' expected int if populated, got '1' of type str",
        )

    def test_override_raises_if_invalid_second_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(second="1")
        self.assertEqual(
            str(e.exception),
            "'Override.second' expected int if populated, got '1' of type str",
        )

    def test_override_raises_if_invalid_year_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(year=True)
        self.assertEqual(
            str(e.exception),
            "'Override.year' expected int if populated, got 'True' of type bool",
        )

    def test_override_raises_if_invalid_month_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(month=True)
        self.assertEqual(
            str(e.exception),
            "'Override.month' expected int if populated, got 'True' of type bool",
        )

    def test_override_raises_if_invalid_day_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(day=True)
        self.assertEqual(
            str(e.exception),
            "'Override.day' expected int if populated, got 'True' of type bool",
        )

    def test_override_raises_if_invalid_hour_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(hour=True)
        self.assertEqual(
            str(e.exception),
            "'Override.hour' expected int if populated, got 'True' of type bool",
        )

    def test_override_raises_if_invalid_minute_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(minute=True)
        self.assertEqual(
            str(e.exception),
            "'Override.minute' expected int if populated, got 'True' of type bool",
        )

    def test_override_raises_if_invalid_second_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Override(second=True)
        self.assertEqual(
            str(e.exception),
            "'Override.second' expected int if populated, got 'True' of type bool",
        )

    def test_override_raises_if_values_out_of_range(self):
        with self.assertRaises(InvalidSmartContractError) as ex1:
            Override(month=13)
        with self.assertRaises(InvalidSmartContractError) as ex2:
            Override(day=32)
        with self.assertRaises(InvalidSmartContractError) as ex3:
            Override(hour=24)
        with self.assertRaises(InvalidSmartContractError) as ex4:
            Override(minute=60)
        with self.assertRaises(InvalidSmartContractError) as ex5:
            Override(second=60)
        with self.assertRaises(InvalidSmartContractError) as ex6:
            Override(year=-1)
        with self.assertRaises(InvalidSmartContractError) as ex7:
            Override(month=0)
        with self.assertRaises(InvalidSmartContractError) as ex8:
            Override(day=0)
        with self.assertRaises(InvalidSmartContractError) as ex9:
            Override(hour=-1)
        with self.assertRaises(InvalidSmartContractError) as ex10:
            Override(minute=-1)
        with self.assertRaises(InvalidSmartContractError) as ex11:
            Override(second=-1)

        for ex in [ex1, ex2, ex3, ex4, ex5, ex6, ex7, ex8, ex9, ex10, ex11]:
            self.assertEqual(str(ex.exception), "Values of Override object are out of range.")

    def test_next_with_all_values_not_provided(self):
        with self.assertRaises(TypeError) as e:
            Next()
        self.assertEqual(
            str(e.exception),
            "Next.__init__() missing 1 required keyword-only argument: 'day'",
        )

    def test_next_raises_if_invalid_month_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(month="1", day=1)
        self.assertEqual(
            str(e.exception), "'Next.month' expected int if populated, got '1' of type str"
        )

    def test_next_raises_if_invalid_day_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(day="1")
        self.assertEqual(str(e.exception), "'Next.day' expected int, got '1' of type str")

    def test_next_raises_if_invalid_hour_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(hour="1", day=1)
        self.assertEqual(
            str(e.exception), "'Next.hour' expected int if populated, got '1' of type str"
        )

    def test_next_raises_if_invalid_minute_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(minute="1", day=1)
        self.assertEqual(
            str(e.exception), "'Next.minute' expected int if populated, got '1' of type str"
        )

    def test_next_raises_if_invalid_second_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(second="1", day=1)
        self.assertEqual(
            str(e.exception), "'Next.second' expected int if populated, got '1' of type str"
        )

    def test_next_raises_if_invalid_month_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(month=True, day=1)
        self.assertEqual(
            str(e.exception), "'Next.month' expected int if populated, got 'True' of type bool"
        )

    def test_next_raises_if_invalid_day_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(day=True)
        self.assertEqual(str(e.exception), "'Next.day' expected int, got 'True' of type bool")

    def test_next_raises_if_invalid_hour_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(hour=True, day=1)
        self.assertEqual(
            str(e.exception), "'Next.hour' expected int if populated, got 'True' of type bool"
        )

    def test_next_raises_if_invalid_minute_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(minute=True, day=1)
        self.assertEqual(
            str(e.exception), "'Next.minute' expected int if populated, got 'True' of type bool"
        )

    def test_next_raises_if_invalid_second_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Next(second=True, day=1)
        self.assertEqual(
            str(e.exception), "'Next.second' expected int if populated, got 'True' of type bool"
        )

    def test_previous_with_all_values_not_provided(self):
        with self.assertRaises(TypeError) as e:
            Previous()
        self.assertEqual(
            str(e.exception),
            "Previous.__init__() missing 1 required keyword-only argument: 'day'",
        )

    def test_previous_raises_if_invalid_month_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(month="1", day=1)
        self.assertEqual(
            str(e.exception), "'Previous.month' expected int if populated, got '1' of type str"
        )

    def test_previous_raises_if_invalid_day_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(day="1")
        self.assertEqual(str(e.exception), "'Previous.day' expected int, got '1' of type str")

    def test_previous_raises_if_invalid_hour_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(hour="1", day=1)
        self.assertEqual(
            str(e.exception), "'Previous.hour' expected int if populated, got '1' of type str"
        )

    def test_previous_raises_if_invalid_minute_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(minute="1", day=1)
        self.assertEqual(
            str(e.exception), "'Previous.minute' expected int if populated, got '1' of type str"
        )

    def test_previous_raises_if_invalid_second_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(second="1", day=1)
        self.assertEqual(
            str(e.exception), "'Previous.second' expected int if populated, got '1' of type str"
        )

    def test_previous_raises_if_invalid_month_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(month=True, day=1)
        self.assertEqual(
            str(e.exception), "'Previous.month' expected int if populated, got 'True' of type bool"
        )

    def test_previous_raises_if_invalid_day_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(day=True)
        self.assertEqual(str(e.exception), "'Previous.day' expected int, got 'True' of type bool")

    def test_previous_raises_if_invalid_hour_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(hour=True, day=1)
        self.assertEqual(
            str(e.exception), "'Previous.hour' expected int if populated, got 'True' of type bool"
        )

    def test_previous_raises_if_invalid_minute_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(minute=True, day=1)
        self.assertEqual(
            str(e.exception),
            "'Previous.minute' expected int if populated, got 'True' of type " "bool",
        )

    def test_previous_raises_if_invalid_second_types_provided_bool(self):
        with self.assertRaises(StrongTypingError) as e:
            Previous(second=True, day=1)
        self.assertEqual(
            str(e.exception),
            "'Previous.second' expected int if populated, got 'True' of type " "bool",
        )

    def test_next_repr(self):
        next_native_type = Next(month=1, day=12, hour=4, minute=5, second=6)
        expected = "Next(month=1, day=12, hour=4, minute=5, second=6)"
        self.assertEqual(expected, repr(next_native_type))

    def test_next_with_all_values_populated(self):
        next_native_type = Next(month=1, day=12, hour=4, minute=5, second=6)
        self.assertEqual(1, next_native_type.month)
        self.assertEqual(12, next_native_type.day)
        self.assertEqual(4, next_native_type.hour)
        self.assertEqual(5, next_native_type.minute)
        self.assertEqual(6, next_native_type.second)

    def test_previous_repr(self):
        previous = Previous(month=5, day=17, hour=3, minute=45, second=12)
        expected = "Previous(month=5, day=17, hour=3, minute=45, second=12)"
        self.assertEqual(expected, repr(previous))

    def test_previous_with_all_values_populated(self):
        previous_native_type = Previous(month=5, day=17, hour=3, minute=45, second=12)
        self.assertEqual(5, previous_native_type.month)
        self.assertEqual(17, previous_native_type.day)
        self.assertEqual(3, previous_native_type.hour)
        self.assertEqual(45, previous_native_type.minute)
        self.assertEqual(12, previous_native_type.second)

    def test_next_raises_if_values_out_of_range(self):
        with self.assertRaises(InvalidSmartContractError) as ex1:
            Next(month=13, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex2:
            Next(day=32)
        with self.assertRaises(InvalidSmartContractError) as ex3:
            Next(hour=24, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex4:
            Next(minute=60, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex5:
            Next(second=60, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex6:
            Next(month=0, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex7:
            Next(day=0)

        for ex in [ex1, ex2, ex3, ex4, ex5, ex6, ex7]:
            self.assertEqual(str(ex.exception), "Values of Next object are out of range.")

    def test_previous_raises_if_values_out_of_range(self):
        with self.assertRaises(InvalidSmartContractError) as ex1:
            Previous(month=13, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex2:
            Previous(day=32)
        with self.assertRaises(InvalidSmartContractError) as ex3:
            Previous(hour=24, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex4:
            Previous(minute=60, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex5:
            Previous(second=60, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex6:
            Previous(month=0, day=2)
        with self.assertRaises(InvalidSmartContractError) as ex7:
            Previous(day=0)

        for ex in [ex1, ex2, ex3, ex4, ex5, ex6, ex7]:
            self.assertEqual(str(ex.exception), "Values of Previous object are out of range.")

    def test_relative_date_time_with_next(self):
        relative_date_time_native_object = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Next(month=1, day=12, hour=4, minute=5, second=6),
        )

        self.assertEqual(4, relative_date_time_native_object.shift.years)
        self.assertEqual(1, relative_date_time_native_object.shift.months)
        self.assertEqual(2, relative_date_time_native_object.shift.days)
        self.assertEqual(-10, relative_date_time_native_object.shift.hours)
        self.assertEqual(25, relative_date_time_native_object.shift.minutes)
        self.assertEqual(-45, relative_date_time_native_object.shift.seconds)

        self.assertEqual(1, relative_date_time_native_object.find.month)
        self.assertEqual(12, relative_date_time_native_object.find.day)
        self.assertEqual(4, relative_date_time_native_object.find.hour)
        self.assertEqual(5, relative_date_time_native_object.find.minute)
        self.assertEqual(6, relative_date_time_native_object.find.second)

        self.assertEqual(
            DefinedDateTime.EFFECTIVE_DATETIME, relative_date_time_native_object.origin
        )

    def test_relative_date_time_with_previous(self):
        relative_date_time_native_object = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Previous(month=1, day=12, hour=6, minute=7, second=25),
        )

        self.assertEqual(4, relative_date_time_native_object.shift.years)
        self.assertEqual(1, relative_date_time_native_object.shift.months)
        self.assertEqual(2, relative_date_time_native_object.shift.days)
        self.assertEqual(-10, relative_date_time_native_object.shift.hours)
        self.assertEqual(25, relative_date_time_native_object.shift.minutes)
        self.assertEqual(-45, relative_date_time_native_object.shift.seconds)

        self.assertEqual(1, relative_date_time_native_object.find.month)
        self.assertEqual(12, relative_date_time_native_object.find.day)
        self.assertEqual(6, relative_date_time_native_object.find.hour)
        self.assertEqual(7, relative_date_time_native_object.find.minute)
        self.assertEqual(25, relative_date_time_native_object.find.second)

        self.assertEqual(
            DefinedDateTime.EFFECTIVE_DATETIME, relative_date_time_native_object.origin
        )

    def test_relative_date_time_raises_if_invalid_shift_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            RelativeDateTime(shift="1", origin=DefinedDateTime.EFFECTIVE_DATETIME)
        self.assertEqual(
            str(e.exception),
            "'RelativeDateTime.shift' expected Shift if populated, got '1' of type str",
        )

    def test_relative_date_time_raises_if_invalid_find_types_provided(self):
        with self.assertRaises(StrongTypingError) as e:
            RelativeDateTime(find="1", origin=DefinedDateTime.EFFECTIVE_DATETIME)
        self.assertEqual(
            str(e.exception),
            "'RelativeDateTime.find' expected Union[Next, Previous, Override] if populated, got "
            "'1' of type str",
        )

    def test_relative_date_time_with_shift_and_find_not_populated(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            RelativeDateTime(origin=DefinedDateTime.EFFECTIVE_DATETIME)

        self.assertEqual(
            str(ex.exception),
            "RelativeDateTime Object requires either shift or find attributes to be populated",
        )

    def test_relative_date_time_repr(self):
        relative_date_time_native_object = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Override(year=2, month=1, day=12, hour=2, minute=9, second=53),
        )
        expected = (
            "RelativeDateTime(origin=DefinedDateTime.EFFECTIVE_DATETIME, "
            + "shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45), "
            + "find=Override(year=2, month=1, day=12, hour=2, minute=9, second=53))"
        )
        self.assertEqual(expected, repr(relative_date_time_native_object))

    def test_relative_date_time_with_override(self):
        relative_date_time_native_object = RelativeDateTime(
            origin=DefinedDateTime.EFFECTIVE_DATETIME,
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Override(year=2, month=1, day=12, hour=2, minute=9, second=53),
        )

        self.assertEqual(4, relative_date_time_native_object.shift.years)
        self.assertEqual(1, relative_date_time_native_object.shift.months)
        self.assertEqual(2, relative_date_time_native_object.shift.days)
        self.assertEqual(-10, relative_date_time_native_object.shift.hours)
        self.assertEqual(25, relative_date_time_native_object.shift.minutes)
        self.assertEqual(-45, relative_date_time_native_object.shift.seconds)

        self.assertEqual(2, relative_date_time_native_object.find.year)
        self.assertEqual(1, relative_date_time_native_object.find.month)
        self.assertEqual(12, relative_date_time_native_object.find.day)
        self.assertEqual(2, relative_date_time_native_object.find.hour)
        self.assertEqual(9, relative_date_time_native_object.find.minute)
        self.assertEqual(53, relative_date_time_native_object.find.second)

        self.assertEqual(
            DefinedDateTime.EFFECTIVE_DATETIME, relative_date_time_native_object.origin
        )

    def test_relative_date_time_with_origin_interval_start(self):
        relative_date_time_native_object = RelativeDateTime(
            shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
            find=Override(year=2, month=1, day=12, hour=2, minute=9, second=53),
            origin=DefinedDateTime.INTERVAL_START,
        )

        self.assertEqual(4, relative_date_time_native_object.shift.years)
        self.assertEqual(1, relative_date_time_native_object.shift.months)
        self.assertEqual(2, relative_date_time_native_object.shift.days)
        self.assertEqual(-10, relative_date_time_native_object.shift.hours)
        self.assertEqual(25, relative_date_time_native_object.shift.minutes)
        self.assertEqual(-45, relative_date_time_native_object.shift.seconds)

        self.assertEqual(2, relative_date_time_native_object.find.year)
        self.assertEqual(1, relative_date_time_native_object.find.month)
        self.assertEqual(12, relative_date_time_native_object.find.day)
        self.assertEqual(2, relative_date_time_native_object.find.hour)
        self.assertEqual(9, relative_date_time_native_object.find.minute)
        self.assertEqual(53, relative_date_time_native_object.find.second)

        self.assertEqual(DefinedDateTime.INTERVAL_START, relative_date_time_native_object.origin)

    def test_relative_date_time_with_origin_using_illegal_live_value(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            RelativeDateTime(
                shift=Shift(years=4, months=1, days=2, hours=-10, minutes=25, seconds=-45),
                find=Override(year=2, month=1, day=12, hour=2, minute=9, second=53),
                origin=DefinedDateTime.LIVE,
            )
        self.assertEqual(
            str(ex.exception),
            "RelativeDateTime origin attribute does not support 'DefinedDateTime.LIVE'",
        )

    # ParametersObservation

    def test_parameters_observation(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        parameters_observation = ParametersObservation(
            parameters=parameters,
            value_datetime=value_datetime,
        )
        self.assertEqual(parameters, parameters_observation.parameters)
        self.assertEqual(value_datetime, parameters_observation.value_datetime)

    def test_parameters_observation_repr(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        parameters_observation = ParametersObservation(
            parameters=parameters,
            value_datetime=value_datetime,
        )
        expected = (
            "ParametersObservation(parameters={'parameter_1': 'string_value', "
            + "'parameter_2': Decimal('3.14159')}, value_datetime="
            + "datetime.datetime(2020, 1, 1, 0, 0, tzinfo=zoneinfo.ZoneInfo(key='UTC')))"
        )
        self.assertEqual(expected, repr(parameters_observation))

    def test_parameters_observation_equality(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        parameters_observation = ParametersObservation(
            parameters=parameters,
            value_datetime=value_datetime,
        )
        other_parameters_observation = ParametersObservation(
            parameters=parameters,
            value_datetime=value_datetime,
        )
        self.assertEqual(parameters_observation, other_parameters_observation)

    def test_parameters_observation_unequal_parameters(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        parameters_observation = ParametersObservation(
            parameters=parameters,
            value_datetime=value_datetime,
        )
        other_parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.1"),
        }
        other_parameters_observation = ParametersObservation(
            parameters=other_parameters,
            value_datetime=value_datetime,
        )
        self.assertNotEqual(parameters_observation, other_parameters_observation)

    def test_parameters_observation_empty_parameters(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {}
        parameters_observation = ParametersObservation(
            parameters=parameters,
            value_datetime=value_datetime,
        )
        self.assertEqual(parameters, parameters_observation.parameters)
        self.assertEqual(value_datetime, parameters_observation.value_datetime)

    def test_parameters_observation_raises_with_naive_value_datetime(self):
        value_datetime = datetime(year=2020, month=1, day=1)
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersObservation(
                parameters=parameters,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            str(e.exception),
            "'value_datetime' of ParametersObservation is not timezone aware.",
        )

    def test_parameters_observation_raises_with_non_utc_timezone(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Pacific"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersObservation(
                parameters=parameters,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            str(e.exception),
            "'value_datetime' of ParametersObservation must have timezone UTC, currently US/Pacific.",
        )

    def test_parameters_observation_raises_with_non_zoneinfo_timezone(self):
        value_datetime = datetime.fromtimestamp(1, timezone.utc)
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": Decimal("3.14159"),
        }
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersObservation(
                parameters=parameters,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            "'value_datetime' of ParametersObservation must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    def test_parameters_observation_raises_with_naive_datetime_parameters(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": datetime(2022, 1, 1),
        }
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersObservation(
                parameters=parameters,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            str(e.exception),
            "'parameters[\"parameter_2\"]' of ParametersObservation is not timezone aware.",
        )

    def test_parameters_observation_raises_with_non_utc_timezone_datetime_parameters(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": datetime(2022, 1, 1, tzinfo=ZoneInfo("US/Pacific")),
        }
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersObservation(
                parameters=parameters,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            str(e.exception),
            "'parameters[\"parameter_2\"]' of ParametersObservation must have timezone UTC, currently US/Pacific.",
        )

    def test_parameters_observation_raises_with_non_zoneinfo_timezone_datetime_parameters(self):
        value_datetime = datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        parameters = {
            "parameter_1": "string_value",
            "parameter_2": datetime.fromtimestamp(1, timezone.utc),
        }
        with self.assertRaises(InvalidSmartContractError) as e:
            ParametersObservation(
                parameters=parameters,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            "'parameters[\"parameter_2\"]' of ParametersObservation must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    # EndOfMonthSchedule

    def test_end_of_month_schedule_type_default_values(self):
        end_of_month_schedule = EndOfMonthSchedule(day=1)
        self.assertEqual(0, end_of_month_schedule.hour)
        self.assertEqual(0, end_of_month_schedule.minute)
        self.assertEqual(0, end_of_month_schedule.second)
        self.assertEqual(ScheduleFailover.FIRST_VALID_DAY_BEFORE, end_of_month_schedule.failover)

    def test_end_of_month_schedule_repr(self):
        end_of_month_schedule = EndOfMonthSchedule(day=1)
        expected = (
            "EndOfMonthSchedule(day=1, hour=0, minute=0, second=0, "
            + "failover=ScheduleFailover.FIRST_VALID_DAY_BEFORE)"
        )
        self.assertEqual(expected, repr(end_of_month_schedule))

    def test_end_of_month_schedule_equality(self):
        end_of_month_schedule = EndOfMonthSchedule(day=1)
        other_end_of_month_schedule = EndOfMonthSchedule(day=1)
        self.assertEqual(end_of_month_schedule, other_end_of_month_schedule)

    def test_end_of_month_schedule_unequal_day(self):
        end_of_month_schedule = EndOfMonthSchedule(day=1)
        other_end_of_month_schedule = EndOfMonthSchedule(day=24)
        self.assertNotEqual(end_of_month_schedule, other_end_of_month_schedule)

    def test_end_of_month_schedule_type_can_set_values(self):
        end_of_month_schedule = EndOfMonthSchedule(
            day=15, hour=10, minute=20, second=5, failover=ScheduleFailover.FIRST_VALID_DAY_BEFORE
        )
        self.assertEqual(15, end_of_month_schedule.day)
        self.assertEqual(10, end_of_month_schedule.hour)
        self.assertEqual(20, end_of_month_schedule.minute)
        self.assertEqual(5, end_of_month_schedule.second)
        self.assertEqual(ScheduleFailover.FIRST_VALID_DAY_BEFORE, end_of_month_schedule.failover)

    def test_end_of_month_schedule_type_can_set_decimal_values(self):
        end_of_month_schedule = EndOfMonthSchedule(
            day=Decimal(15),
            hour=Decimal(10),
            minute=Decimal(20),
            second=Decimal(5),
            failover=ScheduleFailover.FIRST_VALID_DAY_BEFORE,
        )
        self.assertEqual(15, end_of_month_schedule.day)
        self.assertEqual(10, end_of_month_schedule.hour)
        self.assertEqual(20, end_of_month_schedule.minute)
        self.assertEqual(5, end_of_month_schedule.second)
        self.assertEqual(ScheduleFailover.FIRST_VALID_DAY_BEFORE, end_of_month_schedule.failover)

    def test_end_of_month_schedule_raise_if_values_out_of_range(self):
        values = [
            {"day": 0},
            {"day": 32},
            {"day": 1, "hour": -1},
            {"day": 1, "hour": 25},
            {"day": 1, "minute": -1},
            {"day": 1, "minute": 61},
            {"day": 1, "second": -1},
            {"day": 1, "second": 61},
        ]

        error_parts = [
            ("day", 1, 31),
            ("day", 1, 31),
            ("hour", 0, 23),
            ("hour", 0, 23),
            ("minute", 0, 59),
            ("minute", 0, 59),
            ("second", 0, 59),
            ("second", 0, 59),
        ]

        for i, value in enumerate(values):
            time_component, low, high = error_parts[i]
            with self.assertRaises(InvalidSmartContractError) as e:
                EndOfMonthSchedule(**value)
            self.assertEqual(
                str(e.exception),
                f"Argument {time_component} of EndOfMonthSchedule"
                f" object is out of range({low}-{high}).",
            )

    def test_end_of_month_schedule_raises_if_decimal_values_out_of_range(self):
        values = [
            {"day": Decimal(0)},
            {"day": Decimal(32)},
            {"day": Decimal(1), "hour": Decimal(-1)},
            {"day": Decimal(1), "hour": Decimal(25)},
            {"day": Decimal(1), "minute": Decimal(-1)},
            {"day": Decimal(1), "minute": Decimal(61)},
            {"day": Decimal(1), "second": Decimal(-1)},
            {"day": Decimal(1), "second": Decimal(61)},
        ]

        error_parts = [
            ("day", 1, 31),
            ("day", 1, 31),
            ("hour", 0, 23),
            ("hour", 0, 23),
            ("minute", 0, 59),
            ("minute", 0, 59),
            ("second", 0, 59),
            ("second", 0, 59),
        ]

        for i, value in enumerate(values):
            time_component, low, high = error_parts[i]
            with self.assertRaises(InvalidSmartContractError) as e:
                EndOfMonthSchedule(**value)
            self.assertEqual(
                str(e.exception),
                f"Argument {time_component} of EndOfMonthSchedule"
                f" object is out of range({low}-{high}).",
            )

    def test_end_of_month_schedule_raises_if_decimal_values_not_integer(self):
        values = [
            {"day": Decimal(0.1)},
            {"day": Decimal(1.5)},
            {"day": Decimal(-1.5)},
            {"day": Decimal(1), "hour": Decimal(1.5)},
            {"day": Decimal(1), "minute": Decimal(1.5)},
            {"day": Decimal(1), "second": Decimal(1.5)},
        ]

        error_parts = [
            ("day", 1, 31),
            ("day", 1, 31),
            ("day", 1, 31),
            ("hour", 0, 23),
            ("minute", 0, 59),
            ("second", 0, 59),
        ]

        for i, value in enumerate(values):
            time_component, low, high = error_parts[i]
            with self.assertRaises(InvalidSmartContractError) as e:
                EndOfMonthSchedule(**value)
            self.assertEqual(
                str(e.exception),
                f"Argument {time_component} of EndOfMonthSchedule"
                f" object is not an integer value in range({low}-{high}).",
            )

    def test_end_of_month_schedule_invalid_argument_raises(self):
        Test = namedtuple(
            "Test",
            ["method_kwargs", "invalid_field_name", "expected_type", "got_value", "got_type"],
        )

        test_cases = [
            Test(
                method_kwargs={"day": "1"},
                invalid_field_name="day",
                expected_type="int",
                got_value="1",
                got_type="str",
            ),
            Test(
                method_kwargs={"day": 1, "hour": "1"},
                invalid_field_name="hour",
                expected_type="int",
                got_value="1",
                got_type="str",
            ),
            Test(
                method_kwargs={"day": "1", "hour": 1},
                invalid_field_name="day",
                expected_type="int",
                got_value="1",
                got_type="str",
            ),
            Test(
                method_kwargs={"day": 1, "minute": (1,)},
                invalid_field_name="minute",
                expected_type="int",
                got_value="(1,)",
                got_type="tuple",
            ),
            Test(
                method_kwargs={"day": [1], "minute": 1},
                invalid_field_name="day",
                expected_type="int",
                got_value="[1]",
                got_type="list",
            ),
            Test(
                method_kwargs={"day": {1: 1}, "second": 1},
                invalid_field_name="day",
                expected_type="int",
                got_value="{1: 1}",
                got_type="dict",
            ),
            Test(
                method_kwargs={"day": 1.0, "second": 1.0},
                invalid_field_name="day",
                expected_type="int",
                got_value="1.0",
                got_type="float",
            ),
            Test(
                method_kwargs={"day": 1, "failover": 2},
                invalid_field_name="failover",
                expected_type="ScheduleFailover",
                got_value="2",
                got_type="int",
            ),
        ]

        for test_case in test_cases:
            with self.assertRaises(StrongTypingError) as e:
                EndOfMonthSchedule(**test_case.method_kwargs)
            self.assertEqual(
                str(e.exception),
                f"'EndOfMonthSchedule.{test_case.invalid_field_name}' expected {test_case.expected_type}, "
                f"got '{test_case.got_value}' of type {test_case.got_type}",
            )

    # SupervisedHooks

    def test_supervised_hooks(self):
        supervised_hooks = SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.OVERRIDE)
        self.assertEqual(supervised_hooks.pre_posting_hook, SupervisionExecutionMode.OVERRIDE)

    def test_supervised_hooks_argument_required(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            SupervisedHooks()

        self.assertEqual(
            str(e.exception),
            "At least one hook supervision must be specified.",
        )

    def test_supervised_hooks_repr(self):
        supervised_hooks = SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.OVERRIDE)
        expected = "SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.OVERRIDE)"
        self.assertEqual(expected, repr(supervised_hooks))

    def test_supervised_hooks_equality(self):
        supervised_hooks = SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.OVERRIDE)
        other_supervised_hooks = SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.OVERRIDE)
        self.assertEqual(supervised_hooks, other_supervised_hooks)

    def test_supervised_hooks_unequal_pre_posting_hook(self):
        supervised_hooks = SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.OVERRIDE)
        other_supervised_hooks = SupervisedHooks(pre_posting_hook=SupervisionExecutionMode.INVOKED)
        self.assertNotEqual(supervised_hooks, other_supervised_hooks)

    # Rejection

    def test_rejection(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        self.assertEqual("Rejection", rejection.message)
        self.assertEqual(RejectionReason.INSUFFICIENT_FUNDS, rejection.reason_code)

    def test_rejection_repr(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        expected = "Rejection(message='Rejection', reason_code=RejectionReason.INSUFFICIENT_FUNDS)"
        self.assertEqual(expected, repr(rejection))

    def test_rejection_equality(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS
        )
        self.assertEqual(rejection, other_rejection)

    def test_rejection_unequal_reason_code(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.WRONG_DENOMINATION
        )
        self.assertNotEqual(rejection, other_rejection)

    def test_rejection_with_no_reason_code(self):
        rejection = Rejection(message="Rejection")
        self.assertEqual("Rejection", rejection.message)
        self.assertEqual(None, rejection.reason_code)

    def test_rejection_raises_with_no_message(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            Rejection(message="", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        self.assertEqual("Rejection 'message' must be populated", str(ex.exception))

    def test_rejection_from_proto_skips_validation(self):
        rejection = Rejection(message=True, _from_proto=True)
        self.assertEqual(True, rejection.message)
        self.assertEqual(None, rejection.reason_code)

    # Hook Results

    def test_derived_parameter_result_repr(self):
        result = DerivedParameterHookResult(
            parameters_return_value={
                "interest_account": "1",
                "repayment_date": datetime(2019, 12, 12, 13, 20),
                "denomination": "GBP",
                "monthly_repayment": Decimal("500.00"),
                "customer_name": "Paul",
                "tier": UnionItemValue(key="GOLD"),
                "interest_payment_day": OptionalValue(),
                "overdraft_limit": OptionalValue(Decimal("1000.00")),
                "overdraft_fee": OptionalValue(None),
            }
        )
        expected = (
            "DerivedParameterHookResult(parameters_return_value={'interest_account': '1', "
            + "'repayment_date': datetime.datetime(2019, 12, 12, 13, 20), 'denomination': 'GBP', "
            + "'monthly_repayment': Decimal('500.00'), 'customer_name': 'Paul', 'tier': "
            + "UnionItemValue(key='GOLD'), 'interest_payment_day': OptionalValue(value=None), "
            + "'overdraft_limit': OptionalValue(value=Decimal('1000.00')), "
            + "'overdraft_fee': OptionalValue(value=None)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(result))

    def test_derived_parameter_result(self):
        derived_parameters_result = DerivedParameterHookResult(
            parameters_return_value={
                "interest_account": "1",
                "repayment_date": datetime(2019, 12, 12, 13, 20),
                "denomination": "GBP",
                "monthly_repayment": Decimal("500.00"),
                "customer_name": "Paul",
                "tier": UnionItemValue(key="GOLD"),
                "interest_payment_day": OptionalValue(),
                "overdraft_limit": OptionalValue(Decimal("1000.00")),
                "overdraft_fee": OptionalValue(None),
            }
        )
        self.assertEqual(9, len(derived_parameters_result.parameters_return_value))

    def test_derived_parameter_result_equality(self):
        derived_parameters_result = DerivedParameterHookResult(
            parameters_return_value={
                "interest_account": "1",
                "repayment_date": datetime(2019, 12, 12, 13, 20),
                "denomination": "GBP",
            }
        )
        other_derived_parameters_result = DerivedParameterHookResult(
            parameters_return_value={
                "interest_account": "1",
                "repayment_date": datetime(2019, 12, 12, 13, 20),
                "denomination": "GBP",
            }
        )
        self.assertEqual(derived_parameters_result, other_derived_parameters_result)

    def test_derived_parameter_result_unequal_parameters_return_value(self):
        derived_parameters_result = DerivedParameterHookResult(
            parameters_return_value={
                "interest_account": "1",
                "repayment_date": datetime(2019, 12, 12, 13, 20),
                "denomination": "GBP",
            }
        )
        other_derived_parameters_result = DerivedParameterHookResult(
            parameters_return_value={
                "interest_account": "1",
                "repayment_date": datetime(2042, 12, 12, 13, 20),
                "denomination": "GBP",
            }
        )
        self.assertNotEqual(derived_parameters_result, other_derived_parameters_result)

    def test_derived_parameter_result_raises_with_invalid_return_value(self):
        with self.assertRaises(StrongTypingError) as ex:
            DerivedParameterHookResult(parameters_return_value=None)
        self.assertEqual(
            "'parameters_return_value' expected dict, got None",
            str(ex.exception),
        )

    def test_deactivation_hook_result_without_directives_and_rejection(self):
        deactivation_hook_result = DeactivationHookResult()
        self.assertEqual([], deactivation_hook_result.account_notification_directives)
        self.assertEqual([], deactivation_hook_result.posting_instructions_directives)
        self.assertIsNone(deactivation_hook_result.rejection)

    def test_deactivation_hook_result_with_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        deactivation_hook_result = DeactivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        self.assertEqual(
            account_notification_directives,
            deactivation_hook_result.account_notification_directives,
        )
        self.assertEqual(
            posting_instructions_directives,
            deactivation_hook_result.posting_instructions_directives,
        )
        self.assertEqual(
            update_account_event_type_directives,
            deactivation_hook_result.update_account_event_type_directives,
        )

    def test_deactivation_hook_result_with_rejection(self):
        rejection = Rejection(
            message="Cannot close account until loan repaid",
            reason_code=RejectionReason.AGAINST_TNC,
        )
        deactivation_hook_result = DeactivationHookResult(rejection=rejection)
        self.assertEqual(rejection, deactivation_hook_result.rejection)

    def test_deactivation_hook_result_with_rejection_and_directives_errors(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        rejection = Rejection(
            message="Cannot close account until loan repaid",
            reason_code=RejectionReason.AGAINST_TNC,
        )
        with self.assertRaises(InvalidSmartContractError) as ex:
            DeactivationHookResult(
                account_notification_directives=account_notification_directives,
                posting_instructions_directives=posting_instructions_directives,
                update_account_event_type_directives=update_account_event_type_directives,
                rejection=rejection,
            )
        self.assertEqual(
            str(ex.exception),
            "DeactivationHookResult allows the population of directives or rejection, but not both",
        )

    def test_deactivation_hook_result_repr(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        deactivation_hook_result = DeactivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        expected = (
            f"DeactivationHookResult(account_notification_directives={repr(account_notification_directives)}, "
            f"posting_instructions_directives={repr(posting_instructions_directives)}, "
            f"update_account_event_type_directives={repr(update_account_event_type_directives)}, "
            f"rejection={repr(deactivation_hook_result.rejection)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(deactivation_hook_result))

    def test_deactivation_hook_result_equality(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        deactivation_hook_result = DeactivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_deactivation_hook_result = DeactivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )

        self.assertEqual(deactivation_hook_result, other_deactivation_hook_result)

    def test_deactivation_hook_result_unequal_update_account_event_type_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        other_update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2032, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        deactivation_hook_result = DeactivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_deactivation_hook_result = DeactivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=other_update_account_event_type_directives,
        )

        self.assertNotEqual(deactivation_hook_result, other_deactivation_hook_result)

    @patch.object(hook_results, "validate_account_directives")
    def test_deactivation_hook_result_validates_account_directives(
        self, mock_validate_account_directives: Mock
    ):
        DeactivationHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            update_account_event_type_directives=self.test_update_account_event_type_directives,
        )
        mock_validate_account_directives.assert_called_once_with(
            account_directives=self.test_account_notification_directives,
            posting_directives=self.test_posting_instructions_directives,
            update_events=self.test_update_account_event_type_directives,
        )

    def test_post_parameter_change_hook_result_without_directives(self):
        post_parameter_change_hook_result = PostParameterChangeHookResult()
        self.assertEqual([], post_parameter_change_hook_result.account_notification_directives)
        self.assertEqual([], post_parameter_change_hook_result.posting_instructions_directives)
        self.assertEqual([], post_parameter_change_hook_result.update_account_event_type_directives)

    def test_post_parameter_change_hook_result_with_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_parameter_change_hook_result = PostParameterChangeHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        self.assertEqual(
            account_notification_directives,
            post_parameter_change_hook_result.account_notification_directives,
        )
        self.assertEqual(
            posting_instructions_directives,
            post_parameter_change_hook_result.posting_instructions_directives,
        )
        self.assertEqual(
            update_account_event_type_directives,
            post_parameter_change_hook_result.update_account_event_type_directives,
        )

    @patch.object(hook_results, "validate_account_directives")
    def test_post_parameter_change_hook_result_validates_account_directives(
        self, mock_validate_account_directives: Mock
    ):
        PostParameterChangeHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            update_account_event_type_directives=self.test_update_account_event_type_directives,
        )
        mock_validate_account_directives.assert_called_once_with(
            account_directives=self.test_account_notification_directives,
            posting_directives=self.test_posting_instructions_directives,
            update_events=self.test_update_account_event_type_directives,
        )

    def test_post_parameter_change_hook_result_repr(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_parameter_change_hook_result = PostParameterChangeHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        expected = (
            f"PostParameterChangeHookResult(account_notification_directives={repr(account_notification_directives)}, "
            f"posting_instructions_directives={repr(posting_instructions_directives)}, "
            f"update_account_event_type_directives={repr(update_account_event_type_directives)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(post_parameter_change_hook_result))

    def test_post_parameter_change_hook_result_equality(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_parameter_change_hook_result = PostParameterChangeHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_post_parameter_change_hook_result = PostParameterChangeHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )

        self.assertEqual(post_parameter_change_hook_result, other_post_parameter_change_hook_result)

    def test_post_parameter_change_hook_result_unequal_update_account_event_type_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        other_update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2042, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_parameter_change_hook_result = PostParameterChangeHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_post_parameter_change_hook_result = PostParameterChangeHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=other_update_account_event_type_directives,
        )

        self.assertNotEqual(
            post_parameter_change_hook_result, other_post_parameter_change_hook_result
        )

    def test_post_posting_hook_result_without_directives(self):
        post_posting_hook_result = PostPostingHookResult()
        self.assertEqual([], post_posting_hook_result.account_notification_directives)
        self.assertEqual([], post_posting_hook_result.posting_instructions_directives)
        self.assertEqual([], post_posting_hook_result.update_account_event_type_directives)

    def test_post_posting_hook_result_with_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_posting_hook_result = PostPostingHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        self.assertEqual(
            account_notification_directives,
            post_posting_hook_result.account_notification_directives,
        )
        self.assertEqual(
            posting_instructions_directives,
            post_posting_hook_result.posting_instructions_directives,
        )
        self.assertEqual(
            update_account_event_type_directives,
            post_posting_hook_result.update_account_event_type_directives,
        )

    @patch.object(hook_results, "validate_account_directives")
    def test_post_posting_hook_result_validates_account_directives(
        self, mock_validate_account_directives: Mock
    ):
        PostPostingHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            update_account_event_type_directives=self.test_update_account_event_type_directives,
        )
        mock_validate_account_directives.assert_called_once_with(
            account_directives=self.test_account_notification_directives,
            posting_directives=self.test_posting_instructions_directives,
            update_events=self.test_update_account_event_type_directives,
        )

    def test_post_posting_hook_result_repr(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_posting_hook_result = PostPostingHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        expected = (
            f"PostPostingHookResult(account_notification_directives={repr(account_notification_directives)}, "
            f"posting_instructions_directives={repr(posting_instructions_directives)}, "
            f"update_account_event_type_directives={repr(update_account_event_type_directives)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(post_posting_hook_result))

    def test_post_posting_hook_result_equality(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_posting_hook_result = PostPostingHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_post_posting_hook_result = PostPostingHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )

        self.assertEqual(
            post_posting_hook_result,
            other_post_posting_hook_result,
        )

    def test_post_posting_hook_result_unequal_update_account_event_type_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        other_update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2042, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        post_posting_hook_result = PostPostingHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_post_posting_hook_result = PostPostingHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=other_update_account_event_type_directives,
        )

        self.assertNotEqual(
            post_posting_hook_result,
            other_post_posting_hook_result,
        )

    def test_post_posting_hook_result_from_proto_skips_validation(self):
        post_posting_hook_result = PostPostingHookResult(
            update_account_event_type_directives=True, _from_proto=True
        )
        self.assertEqual(True, post_posting_hook_result.update_account_event_type_directives)

    def test_pre_parameter_change_hook_result(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_parameter_change_hook_result = PreParameterChangeHookResult(rejection=rejection)
        self.assertEqual(rejection, pre_parameter_change_hook_result.rejection)

    def test_pre_parameter_change_hook_result_repr(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_parameter_change_hook_result = PreParameterChangeHookResult(rejection=rejection)
        expected = (
            "PreParameterChangeHookResult(rejection=Rejection(message='Rejection', "
            + "reason_code=RejectionReason.INSUFFICIENT_FUNDS))"
        )
        self.assertEqual(expected, repr(pre_parameter_change_hook_result))

    def test_pre_parameter_change_hook_result_equality(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_parameter_change_hook_result = PreParameterChangeHookResult(rejection=rejection)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS
        )
        other_pre_parameter_change_hook_result = PreParameterChangeHookResult(
            rejection=other_rejection
        )

        self.assertEqual(pre_parameter_change_hook_result, other_pre_parameter_change_hook_result)

    def test_pre_parameter_change_hook_result_unequal_rejection(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_parameter_change_hook_result = PreParameterChangeHookResult(rejection=rejection)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.WRONG_DENOMINATION
        )
        other_pre_parameter_change_hook_result = PreParameterChangeHookResult(
            rejection=other_rejection
        )

        self.assertNotEqual(
            pre_parameter_change_hook_result, other_pre_parameter_change_hook_result
        )

    def test_pre_parameter_change_hook_result_with_no_rejection(self):
        pre_parameter_change_hook_result = PreParameterChangeHookResult()
        self.assertEqual(None, pre_parameter_change_hook_result.rejection)

    def test_pre_parameter_change_hook_result_raises_with_invalid_rejection_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            PreParameterChangeHookResult(rejection=True)
        self.assertEqual(
            "'rejection' expected Rejection, got 'True' of type bool", str(ex.exception)
        )

    def test_pre_posting_hook_result(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_posting_hook_result = PrePostingHookResult(rejection=rejection)
        self.assertEqual(rejection, pre_posting_hook_result.rejection)

    def test_pre_posting_hook_result_repr(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_posting_hook_result = PrePostingHookResult(rejection=rejection)
        expected = (
            "PrePostingHookResult(rejection=Rejection(message='Rejection', "
            + "reason_code=RejectionReason.INSUFFICIENT_FUNDS))"
        )
        if is_fflag_enabled(ENRICH_POSTING_INSTRUCTIONS):
            expected = (
                "PrePostingHookResult(rejection=Rejection(message='Rejection', "
                + "reason_code=RejectionReason.INSUFFICIENT_FUNDS), "
                + "enrichment_details=None)"
            )
        self.assertEqual(expected, repr(pre_posting_hook_result))

    def test_pre_posting_hook_result_equality(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_posting_hook_result = PrePostingHookResult(rejection=rejection)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS
        )
        other_pre_posting_hook_result = PrePostingHookResult(rejection=other_rejection)

        self.assertEqual(pre_posting_hook_result, other_pre_posting_hook_result)

    def test_pre_posting_hook_result_unequal_rejection(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        pre_posting_hook_result = PrePostingHookResult(rejection=rejection)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.WRONG_DENOMINATION
        )
        other_pre_posting_hook_result = PrePostingHookResult(rejection=other_rejection)

        self.assertNotEqual(pre_posting_hook_result, other_pre_posting_hook_result)

    def test_pre_posting_hook_result_with_no_rejection(self):
        pre_posting_hook_result = PrePostingHookResult()
        self.assertEqual(None, pre_posting_hook_result.rejection)

    def test_pre_posting_hook_skips_validation(self):
        pre_posting_hook_result = PrePostingHookResult(rejection=True, _from_proto=True)
        self.assertEqual(True, pre_posting_hook_result.rejection)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_with_no_rejection(self):
        enrichment_details = {
            "pi_id_1": PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
            "pi_id_2": PostingInstructionEnrichment(details={"3": "c", "4": "d"}),
        }
        pre_posting_hook_result = PrePostingHookResult(enrichment_details=enrichment_details)
        self.assertEqual(None, pre_posting_hook_result.rejection)
        self.assertEqual(enrichment_details, pre_posting_hook_result.enrichment_details)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_with_rejection(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        enrichment_details = {
            "pi_id_1": PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
            "pi_id_2": PostingInstructionEnrichment(details={"3": "c", "4": "d"}),
        }
        pre_posting_hook_result = PrePostingHookResult(
            rejection=rejection, enrichment_details=enrichment_details
        )
        self.assertEqual(rejection, pre_posting_hook_result.rejection)
        self.assertEqual(enrichment_details, pre_posting_hook_result.enrichment_details)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_none(self):
        pre_posting_hook_result = PrePostingHookResult(enrichment_details=None)
        self.assertEqual(None, pre_posting_hook_result.enrichment_details)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_equality(self):
        enrichment_details = {
            "pi_id_1": PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
            "pi_id_2": PostingInstructionEnrichment(details={"3": "c", "4": "d"}),
        }
        pre_posting_hook_result = PrePostingHookResult(enrichment_details=enrichment_details)
        other_enrichment_details = {
            "pi_id_1": PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
            "pi_id_2": PostingInstructionEnrichment(details={"3": "c", "4": "d"}),
        }
        other_pre_posting_hook_result = PrePostingHookResult(
            enrichment_details=other_enrichment_details
        )
        self.assertEqual(enrichment_details, other_enrichment_details)
        self.assertEqual(pre_posting_hook_result, other_pre_posting_hook_result)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_unequal(self):
        enrichment_details = {
            "pi_id_1": PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
            "pi_id_2": PostingInstructionEnrichment(details={"3": "c", "4": "d"}),
        }
        pre_posting_hook_result = PrePostingHookResult(enrichment_details=enrichment_details)
        other_enrichment_details = {
            "pi_id_3": PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
            "pi_id_4": PostingInstructionEnrichment(details={"3": "c", "4": "d"}),
        }
        other_pre_posting_hook_result = PrePostingHookResult(
            enrichment_details=other_enrichment_details
        )
        self.assertNotEqual(enrichment_details, other_enrichment_details)
        self.assertNotEqual(pre_posting_hook_result, other_pre_posting_hook_result)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_wrong_type_raises(self):
        enrichment_details = "PostingInstructionEnrichment"
        with self.assertRaises(StrongTypingError) as ex:
            PrePostingHookResult(enrichment_details=enrichment_details)
        self.assertEqual(
            "'enrichment_details' expected dict[str, PostingInstructionEnrichment] if populated, got 'PostingInstructionEnrichment' of type str",
            str(ex.exception),
        )

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_wrong_type_key_raises(self):
        enrichment_details = {
            123: PostingInstructionEnrichment(details={"1": "a", "2": "b"}),
        }
        with self.assertRaises(StrongTypingError) as ex:
            PrePostingHookResult(enrichment_details=enrichment_details)
        self.assertEqual(
            "'enrichment_details.key' expected str, got '123' of type int",
            str(ex.exception),
        )

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_pre_posting_hook_result_with_enrichment_details_wrong_type_value_raises(self):
        enrichment_details = {
            "pi_id": 123,
        }
        with self.assertRaises(StrongTypingError) as ex:
            PrePostingHookResult(enrichment_details=enrichment_details)
        self.assertEqual(
            "'enrichment_details.value' expected PostingInstructionEnrichment, got '123' of type int",
            str(ex.exception),
        )

    def test_activation_hook_result_without_directives_or_return_values(self):
        activation_hook_result = ActivationHookResult()
        self.assertEqual([], activation_hook_result.account_notification_directives)
        self.assertEqual([], activation_hook_result.posting_instructions_directives)
        self.assertEqual({}, activation_hook_result.scheduled_events_return_value)

    def test_activation_hook_result_with_directives_and_return_values(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        activation_hook_result = ActivationHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            scheduled_events_return_value=self.test_scheduled_events_return_value,
        )
        self.assertEqual(
            account_notification_directives,
            activation_hook_result.account_notification_directives,
        )
        self.assertEqual(
            posting_instructions_directives,
            activation_hook_result.posting_instructions_directives,
        )
        self.assertEqual(
            self.test_scheduled_events_return_value,
            activation_hook_result.scheduled_events_return_value,
        )
        

    @patch.object(hook_results, "validate_account_directives")
    def test_activation_hook_result_validates_account_directives(
        self, mock_validate_account_directives: Mock
    ):
        ActivationHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            scheduled_events_return_value=self.test_scheduled_events_return_value,
        )
        mock_validate_account_directives.assert_called_once_with(
            account_directives=self.test_account_notification_directives,
            posting_directives=self.test_posting_instructions_directives,
        )

    

    def test_scheduled_event_hook_result_without_directives(self):
        scheduled_event_hook_result = ScheduledEventHookResult()
        self.assertEqual([], scheduled_event_hook_result.account_notification_directives)
        self.assertEqual([], scheduled_event_hook_result.posting_instructions_directives)
        self.assertEqual([], scheduled_event_hook_result.update_account_event_type_directives)

    def test_scheduled_event_hook_result_with_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        scheduled_event_hook_result = ScheduledEventHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        self.assertEqual(
            account_notification_directives,
            scheduled_event_hook_result.account_notification_directives,
        )
        self.assertEqual(
            posting_instructions_directives,
            scheduled_event_hook_result.posting_instructions_directives,
        )
        self.assertEqual(
            update_account_event_type_directives,
            scheduled_event_hook_result.update_account_event_type_directives,
        )

    @patch.object(hook_results, "validate_account_directives")
    def test_scheduled_event_hook_result_validates_account_directives(
        self, mock_validate_account_directives: Mock
    ):
        ScheduledEventHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            update_account_event_type_directives=self.test_update_account_event_type_directives,
        )
        mock_validate_account_directives.assert_called_once_with(
            account_directives=self.test_account_notification_directives,
            posting_directives=self.test_posting_instructions_directives,
            update_events=self.test_update_account_event_type_directives,
            is_scheduled_event_hook=True,
        )

    def test_scheduled_event_hook_result_repr(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        scheduled_event_hook_result = ScheduledEventHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        expected = (
            f"ScheduledEventHookResult(account_notification_directives={repr(account_notification_directives)}, "
            f"posting_instructions_directives={repr(posting_instructions_directives)}, "
            f"update_account_event_type_directives={repr(update_account_event_type_directives)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(scheduled_event_hook_result))

    def test_scheduled_event_hook_result_equality(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        scheduled_event_hook_result = ScheduledEventHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_scheduled_event_hook_result = ScheduledEventHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )

        self.assertEqual(
            scheduled_event_hook_result,
            other_scheduled_event_hook_result,
        )

    def test_scheduled_event_hook_result_unequal_update_account_event_type_directives(self):
        account_notification_directives = [
            AccountNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        posting_instructions_directives = self.test_posting_instructions_directives
        update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        other_update_account_event_type_directives = [
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=datetime(2042, 3, 27, tzinfo=ZoneInfo("UTC")),
            )
        ]
        scheduled_event_hook_result = ScheduledEventHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=update_account_event_type_directives,
        )
        other_scheduled_event_hook_result = ScheduledEventHookResult(
            account_notification_directives=account_notification_directives,
            posting_instructions_directives=posting_instructions_directives,
            update_account_event_type_directives=other_update_account_event_type_directives,
        )

        self.assertNotEqual(
            scheduled_event_hook_result,
            other_scheduled_event_hook_result,
        )

    def test_scheduled_event_hook_result_from_proto_skips_validation(self):
        scheduled_event_hook_result = ScheduledEventHookResult(
            update_account_event_type_directives=True, _from_proto=True
        )
        self.assertEqual(True, scheduled_event_hook_result.update_account_event_type_directives)

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_validate_account_directives_raises_with_posting_directive_rejection_reasons_for_non_scheduled_hook(
        self,
    ):
        with self.assertRaises(InvalidSmartContractError) as e:
            validate_account_directives(
                account_directives=[],
                posting_directives=[
                    self.test_posting_instructions_directive_with_rejection_reasons
                ],
            )
        self.assertEqual(
            "PostingInstructionsDirective.non_blocking_rejection_reasons can only be "
            "populated in Scheduled Event Hook Results",
            str(e.exception),
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_validate_account_directives_allows_posting_directive_rejection_reasons_for_scheduled_hook(
        self,
    ):
        # No error raised.
        validate_account_directives(
            account_directives=[],
            posting_directives=[self.test_posting_instructions_directive_with_rejection_reasons],
            is_scheduled_event_hook=True,
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_validate_supervisee_directives_raises_with_posting_directive_rejection_reasons_for_non_scheduled_hook(
        self,
    ):
        with self.assertRaises(InvalidSmartContractError) as e:
            validate_supervisee_directives(
                supervisee_account_directives={},
                supervisee_posting_directives={
                    "account_id_1": [
                        self.test_posting_instructions_directive_with_rejection_reasons
                    ]
                },
                supervisee_update_account_directives={},
            )
        self.assertEqual(
            "PostingInstructionsDirective.non_blocking_rejection_reasons can only be "
            "populated in Scheduled Event Hook Results",
            str(e.exception),
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_validate_supervisee_directives_allows_posting_directive_rejection_reasons_for_scheduled_hook(
        self,
    ):
        # No error raised.
        validate_supervisee_directives(
            supervisee_account_directives={},
            supervisee_posting_directives={
                "account_id_1": [self.test_posting_instructions_directive_with_rejection_reasons]
            },
            supervisee_update_account_directives={},
            is_scheduled_event_hook=True,
        )

    

    def test_supervisor_post_posting_hook_result_without_directives(self):
        supervisor_post_posting_hook_result = SupervisorPostPostingHookResult()
        self.assertEqual([], supervisor_post_posting_hook_result.plan_notification_directives)
        self.assertEqual([], supervisor_post_posting_hook_result.update_plan_event_type_directives)

        self.assertEqual(
            {}, supervisor_post_posting_hook_result.supervisee_account_notification_directives
        )
        self.assertEqual(
            {}, supervisor_post_posting_hook_result.supervisee_posting_instructions_directives
        )
        self.assertEqual(
            {}, supervisor_post_posting_hook_result.supervisee_update_account_event_type_directives
        )

    def test_supervisor_post_posting_hook_result_with_directives(self):
        supervisor_post_posting_hook_result = SupervisorPostPostingHookResult(
            plan_notification_directives=self.test_plan_notification_directives,
            update_plan_event_type_directives=self.test_update_plan_event_type_directives,
            supervisee_account_notification_directives=self.test_supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=self.test_supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=self.test_supervisee_update_account_event_type_directives,
        )
        self.assertEqual(
            self.test_plan_notification_directives,
            supervisor_post_posting_hook_result.plan_notification_directives,
        )
        self.assertEqual(
            self.test_update_plan_event_type_directives,
            supervisor_post_posting_hook_result.update_plan_event_type_directives,
        )

        self.assertEqual(
            self.test_supervisee_account_notification_directives,
            supervisor_post_posting_hook_result.supervisee_account_notification_directives,
        )
        self.assertEqual(
            self.test_supervisee_posting_instructions_directives,
            supervisor_post_posting_hook_result.supervisee_posting_instructions_directives,
        )
        self.assertEqual(
            self.test_supervisee_update_account_event_type_directives,
            supervisor_post_posting_hook_result.supervisee_update_account_event_type_directives,
        )

    @patch.object(hook_results, "validate_supervisee_directives")
    def test_supervisor_post_posting_hook_result_validates_account_directives(
        self, mock_validate_supervisee_directives: Mock
    ):
        SupervisorPostPostingHookResult(
            plan_notification_directives=self.test_plan_notification_directives,
            update_plan_event_type_directives=self.test_update_plan_event_type_directives,
            supervisee_account_notification_directives=self.test_supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=self.test_supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=self.test_supervisee_update_account_event_type_directives,
        )
        mock_validate_supervisee_directives.assert_called_once_with(
            self.test_supervisee_account_notification_directives,
            self.test_supervisee_posting_instructions_directives,
            self.test_supervisee_update_account_event_type_directives,
        )

    def test_supervisor_post_posting_hook_result_repr(self):
        plan_notification_directives = [
            PlanNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        update_plan_event_type_directives = [
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                skip=True,
            )
        ]
        supervisee_account_notification_directives = {
            self.test_account_id: [
                AccountNotificationDirective(
                    notification_type="test_notification_type",
                    notification_details={"key1": "value1"},
                )
            ]
        }
        supervisee_posting_instructions_directives = {
            self.test_account_id: self.test_posting_instructions_directives
        }
        supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }

        supervisor_post_posting_hook_result = SupervisorPostPostingHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        expected = (
            f"SupervisorPostPostingHookResult(plan_notification_directives={repr(plan_notification_directives)}, "
            f"update_plan_event_type_directives={repr(update_plan_event_type_directives)}, "
            f"supervisee_account_notification_directives={repr(supervisee_account_notification_directives)}, "
            f"supervisee_posting_instructions_directives={repr(supervisee_posting_instructions_directives)}, "
            f"supervisee_update_account_event_type_directives={repr(supervisee_update_account_event_type_directives)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(supervisor_post_posting_hook_result))

    def test_supervisor_post_posting_hook_result_equality(self):
        plan_notification_directives = [
            PlanNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        update_plan_event_type_directives = [
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                skip=True,
            )
        ]
        supervisee_account_notification_directives = {
            self.test_account_id: [
                AccountNotificationDirective(
                    notification_type="test_notification_type",
                    notification_details={"key1": "value1"},
                )
            ]
        }
        supervisee_posting_instructions_directives = {
            self.test_account_id: self.test_posting_instructions_directives
        }
        supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }

        supervisor_post_posting_hook_result = SupervisorPostPostingHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        other_supervisor_post_posting_hook_result = SupervisorPostPostingHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )

        self.assertEqual(
            supervisor_post_posting_hook_result,
            other_supervisor_post_posting_hook_result,
        )

    def test_supervisor_post_posting_hook_result_unequal_supervisee_update_account_event_type_directives(
        self,
    ):
        plan_notification_directives = [
            PlanNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        update_plan_event_type_directives = [
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                skip=True,
            )
        ]
        supervisee_account_notification_directives = {
            self.test_account_id: [
                AccountNotificationDirective(
                    notification_type="test_notification_type",
                    notification_details={"key1": "value1"},
                )
            ]
        }
        supervisee_posting_instructions_directives = {
            self.test_account_id: self.test_posting_instructions_directives
        }
        supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }
        other_supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_42",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }

        supervisor_post_posting_hook_result = SupervisorPostPostingHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        other_supervisor_post_posting_hook_result = SupervisorPostPostingHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=other_supervisee_update_account_event_type_directives,
        )

        self.assertNotEqual(
            supervisor_post_posting_hook_result,
            other_supervisor_post_posting_hook_result,
        )

    def test_supervisor_pre_posting_hook_result(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(rejection=rejection)
        self.assertEqual(rejection, supervisor_pre_posting_hook_result.rejection)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_supervisor_pre_posting_hook_result_with_enrichment(self):
        enrichment_1 = PostingInstructionEnrichment(details={"a1": "11", "b1": "12"})
        enrichment_2 = PostingInstructionEnrichment(details={"a2": "21", "b2": "22"})
        enrichment_details = {
            "account_id_1": {"instruction_id_1": enrichment_1},
            "account_id_2": {"instruction_id_2": enrichment_2},
        }
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            enrichment_details=enrichment_details,
        )
        self.assertEqual(enrichment_details, supervisor_pre_posting_hook_result.enrichment_details)

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_supervisor_pre_posting_hook_result_enrichment_repr(self):
        enrichment_1 = PostingInstructionEnrichment(details={"a": "1"})
        enrichment_2 = PostingInstructionEnrichment(details={"b": "2"})
        enrichment_details = {
            "account_id_1": {"instruction_id_1": enrichment_1},
            "account_id_2": {"instruction_id_2": enrichment_2},
        }
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            enrichment_details=enrichment_details,
        )
        expected = (
            "SupervisorPrePostingHookResult(rejection=None, "
            + "enrichment_details={"
            + "'account_id_1': {'instruction_id_1': PostingInstructionEnrichment(details={'a': '1'})}, "
            + "'account_id_2': {'instruction_id_2': PostingInstructionEnrichment(details={'b': '2'})}"
            + "})"
        )
        self.assertEqual(expected, repr(supervisor_pre_posting_hook_result))

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_supervisor_pre_posting_hook_result_equality_enrichment(self):
        enrichment_1 = PostingInstructionEnrichment(details={"a": "1"})
        enrichment_2 = PostingInstructionEnrichment(details={"b": "2"})
        enrichment_details = {
            "account_id_1": {"instruction_id_1": enrichment_1},
            "account_id_2": {"instruction_id_2": enrichment_2},
        }
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            enrichment_details=enrichment_details,
        )
        other_enrichment_1 = PostingInstructionEnrichment(details={"a": "1"})
        other_enrichment_2 = PostingInstructionEnrichment(details={"b": "2"})
        other_enrichment_details = {
            "account_id_1": {"instruction_id_1": other_enrichment_1},
            "account_id_2": {"instruction_id_2": other_enrichment_2},
        }
        other_supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            enrichment_details=other_enrichment_details,
        )
        self.assertEqual(
            supervisor_pre_posting_hook_result, other_supervisor_pre_posting_hook_result
        )

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_supervisor_pre_posting_hook_result_unequal_enrichment(self):
        enrichment_1 = PostingInstructionEnrichment(details={"a": "1"})
        enrichment_2 = PostingInstructionEnrichment(details={"b": "2"})
        enrichment_details = {
            "account_id_1": {"instruction_id_1": enrichment_1},
            "account_id_2": {"instruction_id_2": enrichment_2},
        }
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            enrichment_details=enrichment_details,
        )
        other_enrichment_1 = PostingInstructionEnrichment(details={"a": "1"})
        other_enrichment_2 = PostingInstructionEnrichment(details={"b": "3"})  # Subtle difference
        other_enrichment_details = {
            "account_id_1": {"instruction_id_1": other_enrichment_1},
            "account_id_2": {"instruction_id_2": other_enrichment_2},
        }
        other_supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            enrichment_details=other_enrichment_details,
        )
        self.assertNotEqual(
            supervisor_pre_posting_hook_result, other_supervisor_pre_posting_hook_result
        )

    @skip_if_not_enabled(ENRICH_POSTING_INSTRUCTIONS)
    def test_supervisor_pre_posting_hook_raises_with_invalid_enrichment_values(self):
        with self.assertRaises(StrongTypingError) as ex:
            SupervisorPrePostingHookResult(enrichment_details=True)
        self.assertEqual(
            "'enrichment_details' expected dict[str, dict[str, PostingInstructionEnrichment]] "
            + "if populated, got 'True' of type bool",
            str(ex.exception),
        )

    def test_supervisor_pre_posting_hook_result_rejection_repr(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(rejection=rejection)
        expected = (
            "SupervisorPrePostingHookResult(rejection=Rejection(message='Rejection', "
            + "reason_code=RejectionReason.INSUFFICIENT_FUNDS), "
            + "enrichment_details=None)"
        )
        self.assertEqual(expected, repr(supervisor_pre_posting_hook_result))

    def test_supervisor_pre_posting_hook_result_equality_rejection(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(rejection=rejection)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS
        )
        other_supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            rejection=other_rejection
        )

        self.assertEqual(
            supervisor_pre_posting_hook_result, other_supervisor_pre_posting_hook_result
        )

    def test_supervisor_pre_posting_hook_result_unequal_rejection(self):
        rejection = Rejection(message="Rejection", reason_code=RejectionReason.INSUFFICIENT_FUNDS)
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(rejection=rejection)
        other_rejection = Rejection(
            message="Rejection", reason_code=RejectionReason.CLIENT_CUSTOM_REASON
        )
        other_supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult(
            rejection=other_rejection
        )

        self.assertNotEqual(
            supervisor_pre_posting_hook_result, other_supervisor_pre_posting_hook_result
        )

    def test_supervisor_pre_posting_hook_result_with_no_rejection_or_enrichment(self):
        supervisor_pre_posting_hook_result = SupervisorPrePostingHookResult()
        self.assertEqual(None, supervisor_pre_posting_hook_result.rejection)

    def test_supervisor_pre_posting_hook_raises_with_invalid_rejection_values(self):
        with self.assertRaises(StrongTypingError) as ex:
            SupervisorPrePostingHookResult(rejection=True)
        self.assertEqual(
            "'rejection' expected Rejection, got 'True' of type bool",
            str(ex.exception),
        )

    def test_supervisor_scheduled_event_hook_result_without_directives(self):
        supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult()
        self.assertEqual([], supervisor_scheduled_event_hook_result.plan_notification_directives)
        self.assertEqual(
            [], supervisor_scheduled_event_hook_result.update_plan_event_type_directives
        )

        self.assertEqual(
            {}, supervisor_scheduled_event_hook_result.supervisee_account_notification_directives
        )
        self.assertEqual(
            {}, supervisor_scheduled_event_hook_result.supervisee_posting_instructions_directives
        )
        self.assertEqual(
            {},
            supervisor_scheduled_event_hook_result.supervisee_update_account_event_type_directives,
        )

    def test_supervisor_scheduled_event_hook_result_with_directives(self):
        supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult(
            plan_notification_directives=self.test_plan_notification_directives,
            update_plan_event_type_directives=self.test_update_plan_event_type_directives,
            supervisee_account_notification_directives=self.test_supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=self.test_supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=self.test_supervisee_update_account_event_type_directives,
        )
        self.assertEqual(
            self.test_plan_notification_directives,
            supervisor_scheduled_event_hook_result.plan_notification_directives,
        )
        self.assertEqual(
            self.test_update_plan_event_type_directives,
            supervisor_scheduled_event_hook_result.update_plan_event_type_directives,
        )

        self.assertEqual(
            self.test_supervisee_account_notification_directives,
            supervisor_scheduled_event_hook_result.supervisee_account_notification_directives,
        )
        self.assertEqual(
            self.test_supervisee_posting_instructions_directives,
            supervisor_scheduled_event_hook_result.supervisee_posting_instructions_directives,
        )
        self.assertEqual(
            self.test_supervisee_update_account_event_type_directives,
            supervisor_scheduled_event_hook_result.supervisee_update_account_event_type_directives,
        )

    @patch.object(hook_results, "validate_supervisee_directives")
    def test_supervisor_scheduled_event_hook_result_validates_account_directives(
        self, mock_validate_supervisee_directives: Mock
    ):
        SupervisorScheduledEventHookResult(
            plan_notification_directives=self.test_plan_notification_directives,
            update_plan_event_type_directives=self.test_update_plan_event_type_directives,
            supervisee_account_notification_directives=self.test_supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=self.test_supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=self.test_supervisee_update_account_event_type_directives,
        )
        mock_validate_supervisee_directives.assert_called_once_with(
            self.test_supervisee_account_notification_directives,
            self.test_supervisee_posting_instructions_directives,
            self.test_supervisee_update_account_event_type_directives,
            is_scheduled_event_hook=True,
        )

    def test_supervisor_scheduled_event_hook_result_repr(self):
        plan_notification_directives = [
            PlanNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        update_plan_event_type_directives = [
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                skip=True,
            )
        ]
        supervisee_account_notification_directives = {
            self.test_account_id: [
                AccountNotificationDirective(
                    notification_type="test_notification_type",
                    notification_details={"key1": "value1"},
                )
            ]
        }
        supervisee_posting_instructions_directives = {
            self.test_account_id: self.test_posting_instructions_directives
        }
        supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }

        supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        expected = (
            f"SupervisorScheduledEventHookResult(plan_notification_directives={repr(plan_notification_directives)}, "
            f"update_plan_event_type_directives={repr(update_plan_event_type_directives)}, "
            f"supervisee_account_notification_directives={repr(supervisee_account_notification_directives)}, "
            f"supervisee_posting_instructions_directives={repr(supervisee_posting_instructions_directives)}, "
            f"supervisee_update_account_event_type_directives={repr(supervisee_update_account_event_type_directives)})"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(supervisor_scheduled_event_hook_result))

    def test_supervisor_scheduled_event_hook_result_equality(self):
        plan_notification_directives = [
            PlanNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        update_plan_event_type_directives = [
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                skip=True,
            )
        ]
        supervisee_account_notification_directives = {
            self.test_account_id: [
                AccountNotificationDirective(
                    notification_type="test_notification_type",
                    notification_details={"key1": "value1"},
                )
            ]
        }
        supervisee_posting_instructions_directives = {
            self.test_account_id: self.test_posting_instructions_directives
        }
        supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }

        supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        other_supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        self.assertEqual(
            supervisor_scheduled_event_hook_result,
            other_supervisor_scheduled_event_hook_result,
        )

    def test_supervisor_scheduled_event_hook_result_unequal_supervisee_update_account_event_type_directives(
        self,
    ):
        plan_notification_directives = [
            PlanNotificationDirective(
                notification_type="test_notification_type",
                notification_details={"key1": "value1"},
            )
        ]
        update_plan_event_type_directives = [
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                skip=True,
            )
        ]
        supervisee_account_notification_directives = {
            self.test_account_id: [
                AccountNotificationDirective(
                    notification_type="test_notification_type",
                    notification_details={"key1": "value1"},
                )
            ]
        }
        supervisee_posting_instructions_directives = {
            self.test_account_id: self.test_posting_instructions_directives
        }
        supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }
        other_supervisee_update_account_event_type_directives = {
            self.test_account_id: [
                UpdateAccountEventTypeDirective(
                    event_type="event_type_1",
                    end_datetime=datetime(2042, 3, 27, tzinfo=ZoneInfo("UTC")),
                )
            ]
        }

        supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=supervisee_update_account_event_type_directives,
        )
        other_supervisor_scheduled_event_hook_result = SupervisorScheduledEventHookResult(
            plan_notification_directives=plan_notification_directives,
            update_plan_event_type_directives=update_plan_event_type_directives,
            supervisee_account_notification_directives=supervisee_account_notification_directives,
            supervisee_posting_instructions_directives=supervisee_posting_instructions_directives,
            supervisee_update_account_event_type_directives=other_supervisee_update_account_event_type_directives,
        )
        self.assertNotEqual(
            supervisor_scheduled_event_hook_result,
            other_supervisor_scheduled_event_hook_result,
        )

    def test_conversion_hook_result_without_directives_or_return_values(self):
        conversion_hook_result = ConversionHookResult()
        self.assertEqual([], conversion_hook_result.account_notification_directives)
        self.assertEqual([], conversion_hook_result.posting_instructions_directives)
        self.assertEqual({}, conversion_hook_result.scheduled_events_return_value)
        

    def test_conversion_hook_result_with_directives_and_return_values(self):
        conversion_hook_result = ConversionHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            scheduled_events_return_value=self.test_scheduled_events_return_value,
        )
        self.assertEqual(
            self.test_account_notification_directives,
            conversion_hook_result.account_notification_directives,
        )
        self.assertEqual(
            self.test_posting_instructions_directives,
            conversion_hook_result.posting_instructions_directives,
        )
        self.assertEqual(
            self.test_scheduled_events_return_value,
            conversion_hook_result.scheduled_events_return_value,
        )
        self.assertIsNone(conversion_hook_result.rejection)

    @patch.object(hook_results, "validate_account_directives")
    def test_conversion_hook_result_validates_account_directives(
        self, mock_validate_account_directives: Mock
    ):
        ConversionHookResult(
            account_notification_directives=self.test_account_notification_directives,
            posting_instructions_directives=self.test_posting_instructions_directives,
            scheduled_events_return_value=self.test_scheduled_events_return_value,
        )
        mock_validate_account_directives.assert_called_once_with(
            account_directives=self.test_account_notification_directives,
            posting_directives=self.test_posting_instructions_directives,
        )

    

    def test_conversion_hook_result_raises_with_invalid_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            ConversionHookResult(account_notification_directives=True)
        expected = (
            "Expected list of AccountNotificationDirective objects for 'account_directives', got "
            "'True'"
        )
        self.assertEqual(expected, str(ex.exception))
        with self.assertRaises(StrongTypingError) as ex:
            ConversionHookResult(posting_instructions_directives=True)
        expected = (
            "Expected list of PostingInstructionsDirective objects for 'posting_directives', got "
            "'True'"
        )
        self.assertEqual(expected, str(ex.exception))
        with self.assertRaises(StrongTypingError) as ex:
            ConversionHookResult(scheduled_events_return_value=True)
        expected = "Expected dict, got 'True' of type bool"
        self.assertEqual(expected, str(ex.exception))

    

    # SmartContractDescriptor

    def test_smart_contract_descriptor(self):
        supervised_smart_contract = SmartContractDescriptor(
            alias="test1",
            smart_contract_version_id="test_smart_contract_version_id",
            supervise_post_posting_hook=True,
        )
        self.assertEqual("test1", supervised_smart_contract.alias)

    def test_smart_contract_descriptor_repr(self):
        supervised_smart_contract = SmartContractDescriptor(
            alias="test1",
            smart_contract_version_id="test_smart_contract_version_id",
            supervise_post_posting_hook=True,
        )
        expected = (
            "SmartContractDescriptor(alias='test1', "
            + "smart_contract_version_id='test_smart_contract_version_id', "
            + "supervise_post_posting_hook=True, supervised_hooks=None)"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(supervised_smart_contract))

    def test_smart_contract_descriptor_equality(self):
        supervised_smart_contract = SmartContractDescriptor(
            alias="test1",
            smart_contract_version_id="test_smart_contract_version_id",
            supervise_post_posting_hook=True,
        )
        other_supervised_smart_contract = SmartContractDescriptor(
            alias="test1",
            smart_contract_version_id="test_smart_contract_version_id",
            supervise_post_posting_hook=True,
        )
        self.assertEqual(supervised_smart_contract, other_supervised_smart_contract)

    def test_smart_contract_descriptor_unequal_alias(self):
        supervised_smart_contract = SmartContractDescriptor(
            alias="test1",
            smart_contract_version_id="test_smart_contract_version_id",
            supervise_post_posting_hook=True,
        )
        other_supervised_smart_contract = SmartContractDescriptor(
            alias="test2",
            smart_contract_version_id="test_smart_contract_version_id",
            supervise_post_posting_hook=True,
        )
        self.assertNotEqual(supervised_smart_contract, other_supervised_smart_contract)

    def test_smart_contract_descriptor_raises_if_alias_not_populated(self):
        with self.assertRaises(StrongTypingError) as ex:
            SmartContractDescriptor(
                alias=None, smart_contract_version_id="test_smart_contract_version_id"
            )
        self.assertEqual("SmartContractDescriptor 'alias' must be populated", str(ex.exception))

    def test_smart_contract_descriptor_raises_if_smart_contract_version_id_not_populated(self):
        with self.assertRaises(StrongTypingError) as ex:
            SmartContractDescriptor(alias="alias", smart_contract_version_id=None)
        self.assertEqual(
            "SmartContractDescriptor 'smart_contract_version_id' must be populated",
            str(ex.exception),
        )

    def test_smart_contract_descriptor_no_supervised_hooks(self):
        supervised_smart_contract = SmartContractDescriptor(
            alias="test1", smart_contract_version_id="test_smart_contract_version_id"
        )
        self.assertEqual("test1", supervised_smart_contract.alias)
        self.assertIsNone(supervised_smart_contract.supervised_hooks)

    def test_smart_contract_descriptor_raises_with_invalid_supervised_hooks_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            SmartContractDescriptor(
                alias="test1",
                smart_contract_version_id="test_smart_contract_version_id",
                supervised_hooks="foo",
            )
        self.assertEqual(
            "'SmartContractDescriptor.supervised_hooks' expected SupervisedHooks if populated, got "
            "'foo' of type str",
            str(ex.exception),
        )

    # Parameter

    def test_can_construct_parameter(self):
        shape = NumberShape()
        parameter = Parameter(
            name="name",
            description="description",
            display_name="display_name",
            level=ParameterLevel.INSTANCE,
            default_value=42,
            shape=shape,
        )

        self.assertEqual("name", parameter.name)
        self.assertEqual("description", parameter.description)
        self.assertEqual("display_name", parameter.display_name)
        self.assertEqual(ParameterLevel.INSTANCE, parameter.level)
        self.assertEqual(42, parameter.default_value)
        self.assertEqual(shape, parameter.shape)

    def test_parameter_repr(self):
        parameter = Parameter(
            name="name",
            description="description",
            display_name="display_name",
            level=ParameterLevel.INSTANCE,
            default_value=42,
            shape=NumberShape(),
        )
        expected = (
            "Parameter(name='name', shape=NumberShape(min_value=None, max_value=None, step=None), "
            + "level=ParameterLevel.INSTANCE, derived=False, display_name='display_name', "
            + "description='description', default_value=42, update_permission=None)"
        )
        self.assertEqual(expected, repr(parameter))

    def test_parameter_equality(self):
        shape = NumberShape()
        parameter = Parameter(
            name="name",
            description="description",
            display_name="display_name",
            level=ParameterLevel.INSTANCE,
            default_value=42,
            shape=shape,
        )
        other_shape = NumberShape()
        other_parameter = Parameter(
            name="name",
            description="description",
            display_name="display_name",
            level=ParameterLevel.INSTANCE,
            default_value=42,
            shape=other_shape,
        )

        self.assertEqual(parameter, other_parameter)

    def test_parameter_unequal_shape(self):
        shape = NumberShape()
        parameter = Parameter(
            name="name",
            description="description",
            display_name="display_name",
            level=ParameterLevel.INSTANCE,
            default_value=42,
            shape=shape,
        )
        other_shape = NumberShape(min_value=42)
        other_parameter = Parameter(
            name="name",
            description="description",
            display_name="display_name",
            level=ParameterLevel.INSTANCE,
            default_value=42,
            shape=other_shape,
        )

        self.assertNotEqual(parameter, other_parameter)

    # PlanNotificationDirective

    def test_plan_notification_directive_equality(self):
        plan_notification_directive = PlanNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key1": "value1"},
        )
        other_plan_notification_directive = PlanNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key1": "value1"},
        )
        self.assertEqual(plan_notification_directive, other_plan_notification_directive)

    def test_plan_notification_directive_unequal_notification_details(self):
        plan_notification_directive = PlanNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key1": "value1"},
        )
        other_plan_notification_directive = PlanNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key1": "value42"},
        )
        self.assertNotEqual(plan_notification_directive, other_plan_notification_directive)

    # PostingInstructionsDirective

    def test_posting_instructions_directive_repr_inherited_from_mixin(self):
        directive = self.test_posting_instructions_directives[0]
        self.assertTrue(issubclass(PostingInstructionsDirective, ContractsLanguageDunderMixin))
        self.assertIn("PostingInstructionsDirective", repr(directive))

    def test_posting_instructions_directive_equality(self):
        posting_instructions_directive = self.test_posting_instructions_directives[0]
        other_custom_instructions = CustomInstruction(
            postings=[
                Posting(
                    amount=Decimal(1),
                    credit=True,
                    account_id="1",
                    denomination="GBP",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
                Posting(
                    amount=Decimal(1),
                    credit=False,
                    account_id="2",
                    denomination="GBP",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
            ]
        )
        other_posting_instructions_directive = PostingInstructionsDirective(
            client_batch_id="international-payment",
            value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            posting_instructions=[other_custom_instructions],
        )
        self.assertEqual(posting_instructions_directive, other_posting_instructions_directive)

    def test_posting_instructions_directive_unequal_posting_instructions(self):
        posting_instructions_directive = self.test_posting_instructions_directives[0]
        other_custom_instructions = CustomInstruction(
            postings=[
                Posting(
                    amount=Decimal(1),
                    credit=True,
                    account_id="1",
                    denomination="GBP",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
                Posting(
                    amount=Decimal(1),
                    credit=False,
                    account_id="42",
                    denomination="GBP",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    phase=Phase.COMMITTED,
                ),
            ]
        )
        other_posting_instructions_directive = PostingInstructionsDirective(
            client_batch_id="international-payment",
            value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
            posting_instructions=[other_custom_instructions],
        )
        self.assertNotEqual(posting_instructions_directive, other_posting_instructions_directive)

    # Logger

    def test_logger_debug_to_stderr(self):
        logger = Logger.instance()

        with StringIO() as buf:
            with redirect_stderr(buf):
                logger.debug("hello from the tside")

            self.assertEqual("hello from the tside", buf.getvalue().strip())

    def test_logger_debug_raises_with_invalid_type(self):
        logger = Logger.instance()

        with self.assertRaises(StrongTypingError) as ex:
            logger.debug({"hello": "from", "the": "tside"})

        self.assertEqual(
            "'message' expected str, got '{'hello': 'from', 'the': 'tside'}' of type dict",
            str(ex.exception),
        )

        with self.assertRaises(StrongTypingError) as ex:
            logger.debug(["hello", "from", "the", "tside"])

        self.assertEqual(
            "'message' expected str, got '['hello', 'from', 'the', 'tside']' of type list",
            str(ex.exception),
        )

    def test_logger_raises_on_init(self):
        with self.assertRaises(Exception) as ex:
            Logger()
        self.assertEqual("Logger is a singleton. Use instance() instead.", str(ex.exception))

    # Data Fetcher Decorators
    fetcher_decorator_error = "decorator should not pass anything to hook"

    def test_requires_decorator(self):
        @requires(
            balances="latest",
            calendar=["cal_1"],
            data_scope="all",
            event_type="EVENT",
            flags=True,
            last_execution_datetime=["EVENT"],
            parameters=True,
            postings=True,
        )
        def hook(*args, **kwargs):
            self.assertEqual(args, (), self.fetcher_decorator_error)
            self.assertEqual(kwargs, {}, self.fetcher_decorator_error)

        hook()

    def test_fetch_account_data_decorator(self):
        @fetch_account_data(
            balances=["fetcher_1"],
            event_type="EVENT",
            parameters=["fetcher_2"],
            postings=["fetcher_3"],
            flags=["flags_fetcher_1"],
        )
        def hook(*args, **kwargs):
            self.assertEqual(args, (), self.fetcher_decorator_error)
            self.assertEqual(kwargs, {}, self.fetcher_decorator_error)

        hook()

    # Attribute Hook Result

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_hook_result_with_decimal_value(self):
        attribute_hook_result = AttributeHookResult(attribute_value=Decimal(1000))
        self.assertEqual(attribute_hook_result.attribute_value, Decimal(1000))

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_hook_result_with_datetime_value(self):
        attribute_hook_result = AttributeHookResult(attribute_value=datetime(2024, 1, 1))
        self.assertEqual(attribute_hook_result.attribute_value, datetime(2024, 1, 1))

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_hook_result_with_str_value(self):
        attribute_hook_result = AttributeHookResult(attribute_value="and thanks for all the fish")
        self.assertEqual(attribute_hook_result.attribute_value, "and thanks for all the fish")

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_hook_result_with_none_value(self):
        attribute_hook_result = AttributeHookResult()
        self.assertEqual(attribute_hook_result.attribute_value, None)

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_hook_result_raises_with_unsupported_value(self):
        with self.assertRaises(StrongTypingError) as ex:
            AttributeHookResult(attribute_value=1)
        self.assertEqual(
            "'attribute_value' expected Union[Decimal, datetime, str] if populated, got '1' of type int",
            str(ex.exception),
        )

    # PostParameterChangeAdjustmentHookResult
    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_parameter_change_adjustment_hook_result_without_directives(self):
        post_parameter_change_adjustment_hook_result = PostParameterChangeAdjustmentHookResult()
        self.assertEqual(
            [], post_parameter_change_adjustment_hook_result.posting_instructions_directives
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_parameter_change_adjustment_hook_result_with_directives(self):
        post_parameter_change_adjustment_hook_result = PostParameterChangeAdjustmentHookResult(
            posting_instructions_directives=self.test_posting_instructions_directives,
        )
        self.assertEqual(
            self.test_posting_instructions_directives,
            post_parameter_change_adjustment_hook_result.posting_instructions_directives,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_parameter_change_adjustment_hook_result_repr(self):
        self.assertTrue(
            issubclass(PostParameterChangeAdjustmentHookResult, ContractsLanguageDunderMixin),
        )
        self.assertIn(
            "PostParameterChangeAdjustmentHookResult",
            repr(PostParameterChangeAdjustmentHookResult),
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_parameter_change_adjustment_hook_result_equality(self):
        posting_instructions_directives = self.test_posting_instructions_directives
        post_parameter_change_adjustment_hook_result = PostParameterChangeAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )
        other_post_parameter_change_adjustment_hook_result = (
            PostParameterChangeAdjustmentHookResult(
                posting_instructions_directives=deepcopy(posting_instructions_directives),
            )
        )

        self.assertEqual(
            post_parameter_change_adjustment_hook_result,
            other_post_parameter_change_adjustment_hook_result,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_parameter_change_adjustment_hook_result_unequal_posting_instruction_directives(
        self,
    ):
        posting_instructions_directives = self.test_posting_instructions_directives
        other_posting_instructions_directives = [
            PostingInstructionsDirective(
                client_batch_id="different-client-batch-id",
                value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                posting_instructions=self.test_posting_instructions,
            )
        ]

        post_parameter_change_adjustment_hook_result = PostParameterChangeAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )
        other_post_parameter_change_adjustment_hook_result = (
            PostParameterChangeAdjustmentHookResult(
                posting_instructions_directives=other_posting_instructions_directives,
            )
        )

        self.assertNotEqual(
            post_parameter_change_adjustment_hook_result,
            other_post_parameter_change_adjustment_hook_result,
        )

    # PostPostingAdjustmentHookResult
    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_posting_adjustment_hook_result_without_directives(self):
        post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult()
        self.assertEqual([], post_posting_adjustment_hook_result.posting_instructions_directives)

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_posting_adjustment_hook_result_with_directives(self):
        post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult(
            posting_instructions_directives=self.test_posting_instructions_directives,
        )
        self.assertEqual(
            self.test_posting_instructions_directives,
            post_posting_adjustment_hook_result.posting_instructions_directives,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_posting_adjustment_hook_result_repr(self):
        self.assertTrue(
            issubclass(PostPostingAdjustmentHookResult, ContractsLanguageDunderMixin),
        )
        self.assertIn(
            "PostPostingAdjustmentHookResult",
            repr(PostPostingAdjustmentHookResult),
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_posting_adjustment_hook_result_equality(self):
        posting_instructions_directives = self.test_posting_instructions_directives
        post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )
        other_post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult(
            posting_instructions_directives=deepcopy(posting_instructions_directives),
        )

        self.assertEqual(
            post_posting_adjustment_hook_result,
            other_post_posting_adjustment_hook_result,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_posting_adjustment_hook_result_unequal_posting_instructions_directives(self):
        posting_instructions_directives = self.test_posting_instructions_directives
        other_posting_instructions_directives = [
            PostingInstructionsDirective(
                client_batch_id="different-client-batch-id",
                value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                posting_instructions=self.test_posting_instructions,
            )
        ]
        post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )
        other_post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult(
            posting_instructions_directives=other_posting_instructions_directives,
        )

        self.assertNotEqual(
            post_posting_adjustment_hook_result,
            other_post_posting_adjustment_hook_result,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_post_posting_adjustment_hook_result_from_proto_skips_validation(self):
        post_posting_adjustment_hook_result = PostPostingAdjustmentHookResult(
            posting_instructions_directives=True, _from_proto=True
        )
        self.assertEqual(True, post_posting_adjustment_hook_result.posting_instructions_directives)

    # ScheduledEventAdjustmentHookResult
    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_without_directives(self):
        scheduled_event_hook_result = ScheduledEventAdjustmentHookResult()
        self.assertEqual([], scheduled_event_hook_result.posting_instructions_directives)

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_with_directives(self):
        scheduled_event_hook_result = ScheduledEventAdjustmentHookResult(
            posting_instructions_directives=self.test_posting_instructions_directives,
        )
        self.assertEqual(
            self.test_posting_instructions_directives,
            scheduled_event_hook_result.posting_instructions_directives,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_repr(self):
        self.assertTrue(
            issubclass(ScheduledEventAdjustmentHookResult, ContractsLanguageDunderMixin),
        )
        self.assertIn(
            "ScheduledEventAdjustmentHookResult",
            repr(ScheduledEventAdjustmentHookResult),
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_equality(self):
        posting_instructions_directives = self.test_posting_instructions_directives

        scheduled_event_hook_result = ScheduledEventAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )
        other_scheduled_event_hook_result = ScheduledEventAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )

        self.assertEqual(
            scheduled_event_hook_result,
            other_scheduled_event_hook_result,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_unequal_posting_instructions_directives(
        self,
    ):
        posting_instructions_directives = self.test_posting_instructions_directives
        other_posting_instructions_directives = [
            PostingInstructionsDirective(
                client_batch_id="different-client-batch-id",
                value_datetime=datetime(2022, 3, 27, tzinfo=ZoneInfo("UTC")),
                posting_instructions=self.test_posting_instructions,
            )
        ]
        scheduled_event_hook_result = ScheduledEventAdjustmentHookResult(
            posting_instructions_directives=posting_instructions_directives,
        )
        other_scheduled_event_hook_result = ScheduledEventAdjustmentHookResult(
            posting_instructions_directives=other_posting_instructions_directives,
        )

        self.assertNotEqual(
            scheduled_event_hook_result,
            other_scheduled_event_hook_result,
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_from_proto_skips_validation(self):
        scheduled_event_hook_result = ScheduledEventAdjustmentHookResult(
            posting_instructions_directives=True,
            _from_proto=True,
        )
        self.assertTrue(scheduled_event_hook_result.posting_instructions_directives)

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_scheduled_event_adjustment_hook_result_spec(self):
        spec = ScheduledEventAdjustmentHookResult._spec(  # noqa: SLF001
            language_code=symbols.Languages.ENGLISH
        )
        self.assertEqual(spec.name, "ScheduledEventAdjustmentHookResult")
        self.assertEqual(
            spec.docstring, "The hook result of the `scheduled_event_adjustment_hook`."
        )
        self.assertEqual(spec.public_methods, {})

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instruction_rejection_reason_enum(self):
        self.assertEqual(PostingInstructionRejectionReason.RESTRICTION_PREVENT_DEBITS.value, 1)
        self.assertEqual(PostingInstructionRejectionReason.RESTRICTION_PREVENT_CREDITS.value, 2)
        self.assertEqual(PostingInstructionRejectionReason.RESTRICTION_LIMIT_DEBITS.value, 3)
        self.assertEqual(PostingInstructionRejectionReason.RESTRICTION_LIMIT_CREDITS.value, 4)
        self.assertEqual(PostingInstructionRejectionReason.RESTRICTION_REVIEW_DEBITS.value, 5)
        self.assertEqual(PostingInstructionRejectionReason.RESTRICTION_REVIEW_CREDITS.value, 6)
        self.assertEqual(PostingInstructionRejectionReason.INSUFFICIENT_FUNDS.value, 7)
        self.assertEqual(PostingInstructionRejectionReason.AGAINST_TERMS_AND_CONDITIONS.value, 8)
        self.assertEqual(PostingInstructionRejectionReason.CLIENT_CUSTOM_REASON.value, 9)
        self.assertEqual(PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID.value, 10)
        self.assertEqual(PostingInstructionRejectionReason.WRONG_DENOMINATION.value, 11)
