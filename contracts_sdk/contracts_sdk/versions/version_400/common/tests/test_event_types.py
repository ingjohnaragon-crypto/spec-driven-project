from copy import deepcopy
from unittest import TestCase
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ..types import (
    EndOfMonthSchedule,
    EventTypesGroup,
    LastScheduledEventDateTimesObservation,
    ScheduledEvent,
    ScheduleExpression,
    ScheduleSkip,
    
    SmartContractEventType,
    SupervisorContractEventType,
)

from .....utils.exceptions import (
    StrongTypingError,
    InvalidSmartContractError,
)
from .....utils.feature_flags import (
    is_fflag_enabled,
    skip_if_not_enabled,
    ADJUSTMENTS,
    SCHEDULER_EXECUTION_TIMES,
    SERVICING_GROUPS,
)

from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)


class TestPublicCommonV400EventTypesGroup(TestCase):
    def test_event_types_group_can_be_created(self):
        event_types_group = EventTypesGroup(
            name="TestEventTypesGroup", event_types_order=["EVENT_TYPE1", "EVENT_TYPE2"]
        )
        self.assertEqual(event_types_group.name, "TestEventTypesGroup")
        self.assertEqual(event_types_group.event_types_order, ["EVENT_TYPE1", "EVENT_TYPE2"])

    def test_event_types_group_equality(self):
        event_types_group = EventTypesGroup(
            name="TestEventTypesGroup", event_types_order=["EVENT_TYPE1", "EVENT_TYPE2"]
        )
        other_event_types_group = EventTypesGroup(
            name="TestEventTypesGroup", event_types_order=["EVENT_TYPE1", "EVENT_TYPE2"]
        )

        self.assertEqual(event_types_group, other_event_types_group)

    def test_event_types_group_unequal_event_types_order(self):
        event_types_group = EventTypesGroup(
            name="TestEventTypesGroup", event_types_order=["EVENT_TYPE1", "EVENT_TYPE2"]
        )
        other_event_types_group = EventTypesGroup(
            name="TestEventTypesGroup", event_types_order=["EVENT_TYPE1", "EVENT_TYPE3"]
        )

        self.assertNotEqual(event_types_group, other_event_types_group)

    def test_event_types_group_repr(self):
        event_types_group = EventTypesGroup(
            name="TestEventTypesGroup", event_types_order=["EVENT_TYPE1", "EVENT_TYPE2"]
        )
        expected = (
            "EventTypesGroup(name='TestEventTypesGroup', "
            + "event_types_order=['EVENT_TYPE1', 'EVENT_TYPE2'])"
        )
        self.assertEqual(expected, repr(event_types_group))

    def test_event_types_group_empty_name(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            EventTypesGroup(name="", event_types_order=["EVENT_TYPE1", "EVENT_TYPE2"])
        self.assertEqual("EventTypesGroup 'name' must be populated", str(ex.exception))

    def test_event_types_group_raises_with_empty_event_types_order(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            EventTypesGroup(name="TestEvenTypesGroup", event_types_order=[])
        self.assertEqual("'event_types_order' must be a non empty list, got []", str(ex.exception))

    def test_event_types_group_not_enough_event_types(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            EventTypesGroup(name="TestEvenTypesGroup", event_types_order=["EVENT_TYPE"])
        self.assertEqual("An EventTypesGroup must have at least two event types", str(ex.exception))


class TestPublicCommonV400ScheduleExpression(TestCase):
    def test_schedule_expression_can_be_created(self):
        schedule_expression = ScheduleExpression(day="3", year="2050")
        self.assertEqual(schedule_expression.day, "3")
        self.assertEqual(schedule_expression.year, "2050")

    def test_schedule_expression_equality(self):
        schedule_expression = ScheduleExpression(day="3", year="2050")
        other_schedule_expression = ScheduleExpression(day="3", year="2050")
        self.assertEqual(schedule_expression, other_schedule_expression)

    def test_schedule_expression_unequal_year(self):
        schedule_expression = ScheduleExpression(day="3", year="2050")
        other_schedule_expression = ScheduleExpression(day="3", year="2051")
        self.assertNotEqual(schedule_expression, other_schedule_expression)

    def test_schedule_expression_str(self):
        schedule_expression = ScheduleExpression(
            day=15,
            day_of_week=3,
            hour=20,
            minute=30,
            second=30,
            month=6,
            year=2000,
        )
        expected = "30 30 20 15 6 3 2000"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_some_defaults(self):
        schedule_expression = ScheduleExpression(
            day=15,
            hour=20,
            minute=30,
            month=6,
        )
        expected = "0 30 20 15 6 * *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_second_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            second=0,
        )
        expected = "0 * * * * * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            second=1,
        )
        expected = "1 * * * * * *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_minute_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            minute=0,
        )
        expected = "0 0 * * * * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            minute=30,
        )
        expected = "0 30 * * * * *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_hour_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            hour=0,
        )
        expected = "0 0 0 * * * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            hour=20,
        )
        expected = "0 0 20 * * * *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_day_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            day=1,
        )
        expected = "0 0 0 1 * * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            day=5,
        )
        expected = "0 0 0 5 * * *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_month_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            month=1,
        )
        expected = "0 0 0 1 1 * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            month=6,
        )
        expected = "0 0 0 1 6 * *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_day_of_week_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            day_of_week="*",
        )
        expected = "0 0 0 * * * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            day_of_week=3,
        )
        expected = "0 0 0 * * 3 *"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_str_with_year_as_least_significant_field(self):
        schedule_expression = ScheduleExpression(
            year="*",
        )
        expected = "0 0 0 1 1 * *"
        self.assertEqual(expected, str(schedule_expression))

        schedule_expression = ScheduleExpression(
            year=2050,
        )
        expected = "0 0 0 1 1 * 2050"
        self.assertEqual(expected, str(schedule_expression))

    def test_schedule_expression_repr(self):
        schedule_expression = ScheduleExpression(
            day=15,
            day_of_week=3,
            hour=20,
            minute=30,
            second=30,
            month=6,
            year=2000,
        )
        expected = (
            "ScheduleExpression(second=30, minute=30, hour=20, day=15, "
            + "month=6, day_of_week=3, year=2000)"
        )
        self.assertEqual(expected, repr(schedule_expression))

    def test_schedule_expression_int_values(self):
        schedule_expression = ScheduleExpression(
            day=15,
            day_of_week=3,
            hour=20,
            minute=30,
            second=30,
            month=6,
            year=2000,
        )
        self.assertEqual(schedule_expression.day, 15)
        self.assertEqual(schedule_expression.day_of_week, 3)
        self.assertEqual(schedule_expression.hour, 20)
        self.assertEqual(schedule_expression.minute, 30)
        self.assertEqual(schedule_expression.second, 30)
        self.assertEqual(schedule_expression.month, 6)
        self.assertEqual(schedule_expression.year, 2000)

    def test_schedule_expression_zero_values(self):
        schedule_expression = ScheduleExpression(
            hour=0,
        )
        self.assertEqual(schedule_expression.hour, 0)
        # Defaults
        self.assertIsNone(schedule_expression.day)
        self.assertIsNone(schedule_expression.day_of_week)
        self.assertIsNone(schedule_expression.minute)
        self.assertIsNone(schedule_expression.second)
        self.assertIsNone(schedule_expression.month)
        self.assertIsNone(schedule_expression.year)

    def test_schedule_expression_string_values(self):
        schedule_expression = ScheduleExpression(
            day="*/2",
            day_of_week="MON",
            hour="1,2,3",
            minute="*/15",
            second="*/30",
            month="*",
            year="*",
        )
        self.assertEqual(schedule_expression.day, "*/2")
        self.assertEqual(schedule_expression.day_of_week, "MON")
        self.assertEqual(schedule_expression.hour, "1,2,3")
        self.assertEqual(schedule_expression.minute, "*/15")
        self.assertEqual(schedule_expression.second, "*/30")
        self.assertEqual(schedule_expression.month, "*")
        self.assertEqual(schedule_expression.year, "*")

    def test_schedule_expression_invalid_type_day(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                day=False,
                year=2000,
            )
        expected = "'day' expected Union[int, str] if populated, got 'False' of type bool"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_type_day_of_week(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                day_of_week=False,
                month=6,
            )
        expected = "'day_of_week' expected Union[int, str] if populated, got 'False' of type bool"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_type_hour(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                day=15,
                hour=(),
            )
        expected = "'hour' expected Union[int, str] if populated, got '()' of type tuple"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_type_minute(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                hour=30,
                minute={},
            )
        expected = "'minute' expected Union[int, str] if populated, got '{}' of type dict"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_type_second(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                second=False,
            )
        expected = "'second' expected Union[int, str] if populated, got 'False' of type bool"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_type_month(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                month=False,
                year=2000,
            )
        expected = "'month' expected Union[int, str] if populated, got 'False' of type bool"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_type_year(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleExpression(
                year=False,
            )
        expected = "'year' expected Union[int, str] if populated, got 'False' of type bool"
        self.assertEqual(expected, str(ex.exception))

    def test_empty_schedule_expression_raises(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduleExpression()
        expected = "Empty ScheduleExpression not allowed"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_regex(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduleExpression(
                day="-1",
                year=2000,
            )
        expected = "Invalid cron expression defined by ScheduleExpression: [0 0 0 -1 * * 2000]"
        self.assertEqual(expected, str(ex.exception))

    def test_schedule_expression_invalid_regex_field_boundary(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduleExpression(
                day="3",
                year=1960,
            )
        expected = "Invalid cron expression defined by ScheduleExpression: [0 0 0 3 * * 1960]"
        self.assertEqual(expected, str(ex.exception))


class TestPublicCommonV400ScheduleSkip(TestCase):
    def test_schedule_skip_with_end_datetime(self):
        skip_schedule = ScheduleSkip(
            end=datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(
            skip_schedule.end, datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        )

    def test_schedule_skip_equality(self):
        skip_schedule = ScheduleSkip(
            end=datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        )
        other_skip_schedule = ScheduleSkip(
            end=datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        )

        self.assertEqual(skip_schedule, other_skip_schedule)

    def test_schedule_skip_unequal_end(self):
        skip_schedule = ScheduleSkip(
            end=datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        )
        other_skip_schedule = ScheduleSkip(
            end=datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("America/Los_Angeles"))
        )

        self.assertNotEqual(skip_schedule, other_skip_schedule)

    def test_schedule_skip_repr(self):
        skip_schedule = ScheduleSkip(
            end=datetime(year=2021, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        )
        expected = (
            "ScheduleSkip(end=datetime.datetime(2021, 12, 31, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')))"
        )
        self.assertEqual(expected, repr(skip_schedule))

    def test_schedule_skip_raises_with_end_datetime_not_provided(self):
        with self.assertRaises(TypeError) as ex:
            ScheduleSkip()
        self.assertEqual(
            "ScheduleSkip.__init__() missing 1 required keyword-only argument: 'end'",
            str(ex.exception),
        )

    def test_schedule_skip_raises_with_end_datetime_none(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduleSkip(end=None)
        self.assertEqual("ScheduleSkip 'end' must be populated", str(ex.exception))

    def test_schedule_skip_raises_with_end_datetime_invalid(self):
        with self.assertRaises(StrongTypingError) as ex:
            ScheduleSkip(end=False)
        self.assertEqual("Expected datetime, got 'False' of type bool", str(ex.exception))


class TestPublicCommonV400ScheduledEvent(TestCase):
    def test_scheduled_event(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")
        skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        )

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            skip=skip,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(end_datetime, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)
        self.assertEqual(skip, scheduled_event.skip)

    def test_scheduled_event_equality(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")
        skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        )
        other_schedule_expression = ScheduleExpression(day="5")
        other_skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        )

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            skip=skip,
        )
        other_scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=other_schedule_expression,
            skip=other_skip,
        )

        self.assertEqual(scheduled_event, other_scheduled_event)

    def test_scheduled_event_unequal_expression(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")
        skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        )
        other_schedule_expression = ScheduleExpression(day="10")
        other_skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        )

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            skip=skip,
        )
        other_scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=other_schedule_expression,
            skip=other_skip,
        )

        self.assertNotEqual(scheduled_event, other_scheduled_event)

    def test_scheduled_event_unequal_skip(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")
        skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        )
        other_schedule_expression = ScheduleExpression(day="5")
        other_skip = ScheduleSkip(
            end=datetime(year=2000, month=1, day=24, tzinfo=ZoneInfo("UTC")),
        )

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            skip=skip,
        )
        other_scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=other_schedule_expression,
            skip=other_skip,
        )

        self.assertNotEqual(scheduled_event, other_scheduled_event)

    def test_scheduled_event_repr(self):
        scheduled_event = ScheduledEvent(
            start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
            expression=ScheduleExpression(day="5"),
            skip=ScheduleSkip(
                end=datetime(year=2000, month=1, day=20, tzinfo=ZoneInfo("UTC")),
            ),
        )
        expected = (
            "ScheduledEvent(start_datetime="
            + "datetime.datetime(2000, 1, 1, 0, 0, tzinfo=zoneinfo.ZoneInfo(key='UTC')), "
            + "end_datetime=datetime.datetime"
            + "(2000, 2, 1, 0, 0, tzinfo=zoneinfo.ZoneInfo(key='UTC')), "
            + "expression=ScheduleExpression(second=None, minute=None, hour=None, "
            + "day='5', month=None, day_of_week=None, year=None), "
            + "schedule_method=None, "
            + "skip=ScheduleSkip(end=datetime.datetime(2000, 1, 20, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC'))))"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(scheduled_event))

    def test_scheduled_event_raises_with_naive_start_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduledEvent(
                start_datetime=datetime(2022, 1, 1),
            )
        self.assertEqual(
            "'start_datetime' of ScheduledEvent is not timezone aware.",
            str(ex.exception),
        )

    def test_scheduled_event_raises_with_naive_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduledEvent(
                start_datetime=datetime(1970, 1, 1, second=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(2022, 1, 1),
            )
        self.assertEqual(
            "'end_datetime' of ScheduledEvent is not timezone aware.",
            str(ex.exception),
        )

    def test_scheduled_event_raises_with_naive_skip_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ScheduledEvent(
                start_datetime=datetime(1970, 1, 1, second=1, tzinfo=ZoneInfo("UTC")),
                skip=ScheduleSkip(
                    end=datetime(year=2000, month=1, day=20),
                ),
            )
        self.assertEqual(
            "'end' of ScheduleSkip is not timezone aware.",
            str(ex.exception),
        )

    def test_scheduled_event_schedule_method(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_method = EndOfMonthSchedule(day=5)

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            schedule_method=schedule_method,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(end_datetime, scheduled_event.end_datetime)
        self.assertEqual(schedule_method, scheduled_event.schedule_method)

    def test_scheduled_event_with_no_start_end_datetimes(self):
        schedule_expression = ScheduleExpression(day="5")
        scheduled_event = ScheduledEvent(expression=schedule_expression)
        self.assertEqual(None, scheduled_event.start_datetime)
        self.assertEqual(None, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)

    def test_scheduled_event_invalid_start_datetime_raises(self):
        with self.assertRaises(StrongTypingError) as e:
            ScheduledEvent(
                start_datetime=True,
                end_datetime=datetime(year=2000, month=2, day=1),
                expression=ScheduleExpression(day="5"),
            )
        self.assertEqual(
            "'ScheduledEvent.start_datetime' expected datetime if populated, "
            "got 'True' of type bool",
            str(e.exception),
        )

    def test_scheduled_event_no_end_datetime(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            expression=schedule_expression,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(None, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)

    def test_scheduled_event_invalid_end_datetime_raises(self):
        with self.assertRaises(StrongTypingError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=True,
                expression=ScheduleExpression(day="5"),
            )
        self.assertEqual(
            "'ScheduledEvent.end_datetime' expected datetime if populated, got 'True' of type "
            "bool",
            str(e.exception),
        )

    def test_scheduled_event_no_end_datetime_expression_schedule_method_or_skip_raises(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "ScheduledEvent must have exactly one of expression or schedule_method set",
            str(e.exception),
        )

    def test_scheduled_event_expression_and_schedule_method_raises(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(day="5"),
                schedule_method=EndOfMonthSchedule(day=5),
            )
        self.assertEqual(
            "ScheduledEvent must not have both expression and schedule_method set",
            str(e.exception),
        )

    def test_scheduled_event_with_skip_expression_and_schedule_method_raises(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(day="5"),
                schedule_method=EndOfMonthSchedule(day=5),
                skip=True,
            )
        self.assertEqual(
            "ScheduledEvent must not have both expression and schedule_method set",
            str(e.exception),
        )

    def test_scheduled_event_invalid_expression_raises(self):
        with self.assertRaises(StrongTypingError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
                expression=True,
            )
        self.assertEqual(
            "'ScheduledEvent.expression' expected ScheduleExpression if populated, got 'True' of "
            "type bool",
            str(e.exception),
        )

    def test_scheduled_event_invalid_schedule_method_raises(self):
        with self.assertRaises(StrongTypingError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
                schedule_method=True,
            )
        self.assertEqual(
            "'ScheduledEvent.schedule_method' expected EndOfMonthSchedule if populated, got "
            "'True' of type bool",
            str(e.exception),
        )

    def test_scheduled_event_no_skip(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(end_datetime, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)

    def test_scheduled_event_invalid_skip_raises(self):
        with self.assertRaises(StrongTypingError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
                expression=ScheduleExpression(day="5"),
                skip="not-a-skip",
            )
        self.assertEqual(
            "'ScheduledEvent.skip' expected Union[bool, ScheduleSkip] if populated, got "
            "'not-a-skip' of type str",
            str(e.exception),
        )

    def test_scheduled_event_indefinite_skip(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            skip=True,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(end_datetime, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)
        self.assertEqual(True, scheduled_event.skip)

    def test_scheduled_event_unskip(self):
        start_datetime = datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        schedule_expression = ScheduleExpression(day="5")

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            skip=False,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(end_datetime, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)
        self.assertEqual(False, scheduled_event.skip)

    def test_scheduled_event_from_proto_skips_validation(self):
        start_datetime = "not-datetime"
        end_datetime = 2022
        schedule_expression = True
        schedule_method = "not-end-of-month-schedule"

        scheduled_event = ScheduledEvent(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            expression=schedule_expression,
            schedule_method=schedule_method,
            _from_proto=True,
        )
        self.assertEqual(start_datetime, scheduled_event.start_datetime)
        self.assertEqual(end_datetime, scheduled_event.end_datetime)
        self.assertEqual(schedule_expression, scheduled_event.expression)

    def test_scheduled_event_not_exactly_one_of_expression_and_schedule_method_raises(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "ScheduledEvent must have exactly one of expression or schedule_method set",
            str(e.exception),
        )

    def test_scheduled_event_with_skip_not_exactly_one_of_expression_and_schedule_method_raises_(
        self,
    ):
        with self.assertRaises(InvalidSmartContractError) as e:
            ScheduledEvent(
                start_datetime=datetime(year=2000, month=1, day=1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(year=2000, month=2, day=1, tzinfo=ZoneInfo("UTC")),
                skip=True,
            )
        self.assertEqual(
            "ScheduledEvent must have exactly one of expression or schedule_method set",
            str(e.exception),
        )


class TestPublicCommonV400SmartContractEventType(TestCase):
    def test_smart_contract_event_type_can_be_created(self):
        event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG"])
        self.assertEqual(event_type.name, "name")
        self.assertEqual(event_type.scheduler_tag_ids, ["TAG"])

    def test_smart_contract_event_type_equality(self):
        event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG"])
        other_event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG"])
        self.assertEqual(event_type, other_event_type)

    def test_smart_contract_event_type_unequal_scheduler_tag_ids(self):
        event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG"])
        other_event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG2"])
        self.assertNotEqual(event_type, other_event_type)

    def test_smart_contract_event_type_repr(self):
        event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG"])
        expected = "SmartContractEventType(name='name', scheduler_tag_ids=['TAG'])"
        if is_fflag_enabled(ADJUSTMENTS):
            expected = "SmartContractEventType(name='name', scheduler_tag_ids=['TAG'], adjustment_point=False)"
        self.assertEqual(expected, repr(event_type))

    def test_smart_contract_event_type_when_name_empty(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            SmartContractEventType(name="", scheduler_tag_ids=["TAG"])
        expected = (
            "SmartContractEventType 'name' must be populated. Current attributes are "
            + "SmartContractEventType(name='', scheduler_tag_ids=['TAG'])"
        )
        if is_fflag_enabled(ADJUSTMENTS):
            expected = (
                "SmartContractEventType 'name' must be populated. Current attributes are "
                + "SmartContractEventType(name='', scheduler_tag_ids=['TAG'], adjustment_point=False)"
            )
        self.assertEqual(expected, str(ex.exception))

    def test_smart_contract_event_type_when_scheduler_tag_ids_invalid(self):
        with self.assertRaises(StrongTypingError) as ex:
            SmartContractEventType(name="name", scheduler_tag_ids="invalid")
        self.assertEqual(
            "Expected list of str objects for 'scheduler_tag_ids', got 'invalid'", str(ex.exception)
        )

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_smart_contract_event_type_adjustment_point_defaults_to_false(self):
        event_type = SmartContractEventType(name="name", scheduler_tag_ids=["TAG"])
        expected = SmartContractEventType(
            name="name", scheduler_tag_ids=["TAG"], adjustment_point=False
        )
        self.assertEqual(expected, event_type)

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_smart_contract_event_type_adjustment_point_can_be_set_to_true(self):
        event_type = SmartContractEventType(
            name="name", scheduler_tag_ids=["TAG"], adjustment_point=True
        )
        self.assertTrue(event_type.adjustment_point)
        self.assertIsInstance(event_type.adjustment_point, bool)

    @skip_if_not_enabled(ADJUSTMENTS)
    def test_smart_contract_event_type_adjustment_point_invalid_type_raises_error(self):
        with self.assertRaises(StrongTypingError) as ex:
            SmartContractEventType(
                name="name", scheduler_tag_ids=["TAG"], adjustment_point="hello world"
            )
        self.assertEqual(
            "'SmartContractEventType.adjustment_point' expected bool if populated, got 'hello world' of type str",
            str(ex.exception),
        )


class TestPublicCommonV400SupervisorContractEventType(TestCase):
    def test_supervisor_contract_event_type_can_be_created(self):
        event_type_name = "TEST_EVENT_1"
        scheduler_tag_ids = ["TEST_TAG_1", "TEST_TAG_2"]
        overrides_event_types = [
            ("S1", "TEST_EVENT_2"),
            ("S2", "TEST_EVENT_3"),
        ]

        event_type = SupervisorContractEventType(
            name=event_type_name,
            scheduler_tag_ids=scheduler_tag_ids,
            overrides_event_types=overrides_event_types,
        )

        self.assertEqual(event_type_name, event_type.name)
        self.assertEqual(scheduler_tag_ids, event_type.scheduler_tag_ids)
        self.assertEqual(overrides_event_types, event_type.overrides_event_types)

    def test_supervisor_contract_event_type_equality(self):
        event_type = SupervisorContractEventType(
            name="name",
            scheduler_tag_ids=["TAG"],
            overrides_event_types=[
                ("S1", "TEST_EVENT_2"),
                ("S2", "TEST_EVENT_3"),
            ],
        )
        other_event_type = SupervisorContractEventType(
            name="name",
            scheduler_tag_ids=["TAG"],
            overrides_event_types=[
                ("S1", "TEST_EVENT_2"),
                ("S2", "TEST_EVENT_3"),
            ],
        )

        self.assertEqual(event_type, other_event_type)

    def test_supervisor_contract_event_type_unequal_overrides_event_types(self):
        event_type = SupervisorContractEventType(
            name="name",
            scheduler_tag_ids=["TAG"],
            overrides_event_types=[
                ("S1", "TEST_EVENT_2"),
                ("S2", "TEST_EVENT_3"),
            ],
        )
        other_event_type = SupervisorContractEventType(
            name="name",
            scheduler_tag_ids=["TAG"],
            overrides_event_types=[
                ("S1", "TEST_EVENT_2"),
                ("S2", "TEST_EVENT_42"),
            ],
        )

        self.assertNotEqual(event_type, other_event_type)

    def test_supervisor_contract_event_type_repr(self):
        event_type = SupervisorContractEventType(
            name="TEST_EVENT_1",
            scheduler_tag_ids=["TEST_TAG_1", "TEST_TAG_2"],
            overrides_event_types=[
                ("S1", "TEST_EVENT_2"),
                ("S2", "TEST_EVENT_3"),
            ],
        )

        expected = (
            "SupervisorContractEventType(name='TEST_EVENT_1', "
            + "scheduler_tag_ids=['TEST_TAG_1', 'TEST_TAG_2'], "
            + "overrides_event_types=[('S1', 'TEST_EVENT_2'), ('S2', 'TEST_EVENT_3')])"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(event_type))

    def test_supervisor_contract_event_type_when_name_empty(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            SupervisorContractEventType(name="", scheduler_tag_ids=["TAG"])
        expected = (
            "SupervisorContractEventType 'name' must be populated. "
            + "Current attributes are SupervisorContractEventType(name='', "
            + "scheduler_tag_ids=['TAG'], overrides_event_types=None)"
        )
        self.maxDiff = None
        self.assertEqual(expected, str(ex.exception))

    def test_supervisor_contract_event_type_when_scheduler_tag_ids_invalid(self):
        with self.assertRaises(StrongTypingError) as ex:
            SupervisorContractEventType(name="name", scheduler_tag_ids="invalid")
        self.assertEqual(
            "Expected list of str objects for 'scheduler_tag_ids', got 'invalid'", str(ex.exception)
        )

    def test_supervisor_contract_event_type_when_scheduler_tag_ids_invalid_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            SupervisorContractEventType(name="name", scheduler_tag_ids=["TAG", 5])
        self.assertEqual("Expected str, got '5' of type int", str(ex.exception))

    def test_supervisor_contract_event_type_when_overrides_event_types_invalid(self):
        with self.assertRaises(StrongTypingError) as ex:
            SupervisorContractEventType(
                name="name", scheduler_tag_ids=["TAG"], overrides_event_types="invalid"
            )
        self.assertEqual(
            "Expected list of Tuple[str, str] objects for 'overrides_event_types', got "
            "'invalid'",
            str(ex.exception),
        )

    def test_supervisor_contract_event_type_when_overrides_event_types_invalid_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            SupervisorContractEventType(
                name="name",
                scheduler_tag_ids=["TAG"],
                overrides_event_types=[("S1", "TEST_EVENT_1"), 5],
            )
        self.assertEqual("Expected Tuple[str, str], got '5' of type int", str(ex.exception))


class TestPublicCommonV400ServicingContractEventType(TestCase):
    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_can_be_created(self):
        event_type_name = "TEST_EVENT_1"

        servicing_contract_event_type = ServicingContractEventType(
            name=event_type_name,
        )

        self.assertEqual(event_type_name, servicing_contract_event_type.name)

    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_equality(self):
        servicing_contract_event_type = ServicingContractEventType(
            name="name",
        )
        other_servicing_contract_event_type = ServicingContractEventType(
            name="name",
        )

        self.assertEqual(servicing_contract_event_type, other_servicing_contract_event_type)

    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_unequal_names(self):
        servicing_contract_event_type = ServicingContractEventType(
            name="name",
        )
        other_servicing_contract_event_type = ServicingContractEventType(
            name="eman",
        )

        self.assertNotEqual(servicing_contract_event_type, other_servicing_contract_event_type)

    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_repr(self):
        servicing_contract_event_type = ServicingContractEventType(
            name="TEST_EVENT_1",
        )

        expected = f"ServicingContractEventType(name={repr(servicing_contract_event_type.name)})"
        self.maxDiff = None
        self.assertEqual(expected, repr(servicing_contract_event_type))

    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_raise_when_name_empty(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            ServicingContractEventType(name="")
        expected = "'ServicingContractEventType.name' must be a non-empty string"
        self.maxDiff = None
        self.assertEqual(expected, str(ex.exception))

    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_raise_when_name_none(self):
        with self.assertRaises(StrongTypingError) as ex:
            ServicingContractEventType(name=None)
        expected = "'ServicingContractEventType.name' expected str, got None"
        self.maxDiff = None
        self.assertEqual(expected, str(ex.exception))

    @skip_if_not_enabled(SERVICING_GROUPS)
    def test_servicing_contract_event_type_raise_when_name_wrong_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            ServicingContractEventType(name=42)
        expected = "'ServicingContractEventType.name' expected str, got '42' of type int"
        self.maxDiff = None
        self.assertEqual(expected, str(ex.exception))


class TestPublicCommonV400LastScheduledEventDateTimesObservation(TestCase):
    def setUp(self) -> None:
        self.last_scheduled_event_datetimes_dict = {
            "event_type_1": datetime(2020, 1, 2, tzinfo=ZoneInfo("UTC")),
            "event_type_2": None,
        }

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        last_scheduled_event_datetimes_observation = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
            value_datetime=value_datetime,
        )
        self.assertEqual(value_datetime, last_scheduled_event_datetimes_observation.value_datetime)
        self.assertEqual(
            self.last_scheduled_event_datetimes_dict,
            last_scheduled_event_datetimes_observation.last_scheduled_event_datetimes,
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_no_value_datetime(self):
        last_scheduled_event_datetimes_observation = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict
        )
        self.assertIsNone(last_scheduled_event_datetimes_observation.value_datetime)
        self.assertEqual(
            self.last_scheduled_event_datetimes_dict,
            last_scheduled_event_datetimes_observation.last_scheduled_event_datetimes,
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_equality(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        last_scheduled_event_datetimes_observation_1 = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
            value_datetime=value_datetime,
        )
        last_scheduled_event_datetimes_observation_2 = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=deepcopy(self.last_scheduled_event_datetimes_dict),
            value_datetime=deepcopy(value_datetime),
        )
        self.assertEqual(
            last_scheduled_event_datetimes_observation_1,
            last_scheduled_event_datetimes_observation_2,
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_equality_different_from_proto(self):
        """Should be equal if all public attributes are equal by value."""
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        last_scheduled_event_datetimes_observation_1 = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
            value_datetime=value_datetime,
        )
        last_scheduled_event_datetimes_observation_2 = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
            value_datetime=value_datetime,
            _from_proto=True,
        )
        self.assertEqual(
            last_scheduled_event_datetimes_observation_1,
            last_scheduled_event_datetimes_observation_2,
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_unequal_datetimes(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        last_scheduled_event_datetimes_dict_2 = {
            "event_type_1": None,
            "event_type_2": datetime(year=2020, month=1, day=20, tzinfo=ZoneInfo("UTC")),
        }
        last_scheduled_event_datetimes_observation_1 = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
            value_datetime=value_datetime,
        )
        last_scheduled_event_datetimes_observation_2 = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=last_scheduled_event_datetimes_dict_2,
            value_datetime=value_datetime,
        )
        self.assertNotEqual(
            last_scheduled_event_datetimes_observation_1,
            last_scheduled_event_datetimes_observation_2,
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_repr(self):
        christmas_day = datetime(year=2022, month=12, day=25, tzinfo=ZoneInfo("UTC"))
        last_scheduled_event_datetimes_observation = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
            value_datetime=christmas_day,
        )
        self.assertTrue(
            issubclass(LastScheduledEventDateTimesObservation, ContractsLanguageDunderMixin)
        )
        self.assertIn(
            "LastScheduledEventDateTimesObservation",
            repr(last_scheduled_event_datetimes_observation),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_repr_empty_dict(self):
        last_scheduled_event_datetimes_observation = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes={}, value_datetime=None
        )
        expected_repr = "LastScheduledEventDateTimesObservation(last_scheduled_event_datetimes={}, value_datetime=None)"
        self.assertEqual(expected_repr, repr(last_scheduled_event_datetimes_observation))

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_raises_error_with_wrong_last_scheduled_event_datetimes_type(
        self,
    ):
        with self.assertRaises(StrongTypingError) as e:
            christmas_day = datetime(year=2022, month=12, day=25, tzinfo=ZoneInfo("UTC"))
            LastScheduledEventDateTimesObservation(
                last_scheduled_event_datetimes=1, value_datetime=christmas_day
            )
        self.assertEqual(
            "'LastScheduledEventDateTimesObservation.last_scheduled_event_datetimes' expected dict[str, Optional[datetime]], got '1' of type int",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_raises_error_with_wrong_value_datetime_type(
        self,
    ):
        with self.assertRaises(StrongTypingError) as e:
            LastScheduledEventDateTimesObservation(
                last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
                value_datetime=1,
            )
        self.assertEqual(
            "'LastScheduledEventDateTimesObservation.value_datetime' expected datetime if populated, got '1' of type int",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_raises_error_with_value_datetime_not_timezone_aware(
        self,
    ):
        with self.assertRaises(InvalidSmartContractError) as e:
            naive_datetime = datetime(year=2020, month=2, day=20)
            LastScheduledEventDateTimesObservation(
                last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
                value_datetime=naive_datetime,
            )
        self.assertEqual(
            "'value_datetime' of LastScheduledEventDateTimesObservation is not timezone aware.",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_raises_with_non_utc_timezone(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("US/Pacific"))
        with self.assertRaises(InvalidSmartContractError) as e:
            LastScheduledEventDateTimesObservation(
                last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            str(e.exception),
            "'value_datetime' of LastScheduledEventDateTimesObservation must have timezone UTC, currently "
            "US/Pacific.",
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_raises_with_non_zoneinfo_timezone(self):
        value_datetime = datetime.fromtimestamp(1, timezone.utc)
        with self.assertRaises(InvalidSmartContractError) as e:
            LastScheduledEventDateTimesObservation(
                last_scheduled_event_datetimes=self.last_scheduled_event_datetimes_dict,
                value_datetime=value_datetime,
            )
        self.assertEqual(
            "'value_datetime' of LastScheduledEventDateTimesObservation must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    @skip_if_not_enabled(SCHEDULER_EXECUTION_TIMES)
    def test_last_scheduled_event_datetimes_observation_no_value_datetime_and_empty_balances(self):
        last_scheduled_event_datetimes_observation = LastScheduledEventDateTimesObservation(
            last_scheduled_event_datetimes={}
        )
        self.assertIsNone(last_scheduled_event_datetimes_observation.value_datetime)
        self.assertEqual(
            {}, last_scheduled_event_datetimes_observation.last_scheduled_event_datetimes
        )
