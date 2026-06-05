from datetime import datetime, timezone
from unittest import TestCase
from zoneinfo import ZoneInfo


from ..types.calendars import CalendarEvent, CalendarEvents, CalendarsObservation
from .....utils.exceptions import InvalidSmartContractError, StrongTypingError
from .....utils.types_utils import ContractsLanguageDunderMixin

from .....utils.feature_flags import (
    skip_if_not_enabled,
    CALENDAR_FETCHERS,
)


class TestPublicCommonV400CalendarEvents(TestCase):
    def test_calendar_event(self):
        calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        self.assertEqual("test 1", calendar_event.id)

    def test_calendar_event_equality(self):
        calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        other_calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        self.assertEqual(calendar_event, other_calendar_event)

    def test_calendar_event_unequal_start_datetime(self):
        calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        other_calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(999, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        self.assertNotEqual(calendar_event, other_calendar_event)

    def test_calendar_event_repr(self):
        calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        self.assertTrue(issubclass(CalendarEvent, ContractsLanguageDunderMixin))
        self.assertIn("CalendarEvent", repr(calendar_event))

    def test_calendar_event_start_datetime_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarEvent(
                id="test 1",
                calendar_id="123",
                start_datetime=datetime(2015, 1, 1),
                end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "'start_datetime' of CalendarEvent is not timezone aware.",
            str(ex.exception),
        )

    def test_calendar_event_start_datetime_raises_with_non_utc_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarEvent(
                id="test 1",
                calendar_id="123",
                start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("US/Pacific")),
                end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "'start_datetime' of CalendarEvent must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_calendar_event_start_datetime_raises_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarEvent(
                id="test 1",
                calendar_id="123",
                start_datetime=datetime.fromtimestamp(1, timezone.utc),
                end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
            )
        self.assertEqual(
            "'start_datetime' of CalendarEvent must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_calendar_event_end_datetime_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarEvent(
                id="test 1",
                calendar_id="123",
                start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(2015, 1, 2),
            )
        self.assertEqual(
            "'end_datetime' of CalendarEvent is not timezone aware.",
            str(ex.exception),
        )

    def test_calendar_event_end_datetime_raises_with_non_utc_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarEvent(
                id="test 1",
                calendar_id="123",
                start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("US/Pacific")),
            )
        self.assertEqual(
            "'end_datetime' of CalendarEvent must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_calendar_event_end_datetime_raises_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarEvent(
                id="test 1",
                calendar_id="123",
                start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
                end_datetime=datetime.fromtimestamp(1, timezone.utc),
            )
        self.assertEqual(
            "'end_datetime' of CalendarEvent must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_calendar_events(self):
        calendar_events = CalendarEvents(
            calendar_events=[
                CalendarEvent(
                    id="test 1",
                    calendar_id="123",
                    start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
                    end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
                ),
                CalendarEvent(
                    id="test 2",
                    calendar_id="124",
                    start_datetime=datetime(2016, 1, 1, tzinfo=ZoneInfo("UTC")),
                    end_datetime=datetime(2016, 1, 2, tzinfo=ZoneInfo("UTC")),
                ),
            ]
        )
        self.assertEqual(2, len(calendar_events))
        self.assertEqual("test 1", calendar_events[0].id)
        self.assertEqual("test 2", calendar_events[1].id)

    def test_calendar_events_equality(self):
        calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        other_calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        calendar_events = CalendarEvents(calendar_events=[calendar_event])
        other_calendar_events = CalendarEvents(calendar_events=[other_calendar_event])

        self.assertEqual(calendar_events, other_calendar_events)

    def test_calendar_events_unequal_calendar_events(self):
        calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2015, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        other_calendar_event = CalendarEvent(
            id="test 1",
            calendar_id="123",
            start_datetime=datetime(2015, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(999, 1, 2, tzinfo=ZoneInfo("UTC")),
        )
        calendar_events = CalendarEvents(calendar_events=[calendar_event])
        other_calendar_events = CalendarEvents(calendar_events=[other_calendar_event])

        self.assertNotEqual(calendar_events, other_calendar_events)


class TestPublicCommonV400CalendarsObservation(TestCase):
    def setUp(self) -> None:
        self.calendar_event_1 = CalendarEvent(
            id="ce1",
            calendar_id="c1",
            start_datetime=datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2099, 1, 1, tzinfo=ZoneInfo("UTC")),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_observation_repr(self):
        calendars_observation = CalendarsObservation(calendars={})
        self.assertTrue(issubclass(CalendarsObservation, ContractsLanguageDunderMixin))
        self.assertIn(CalendarsObservation.__name__, repr(calendars_observation))

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_observation_equality(self):
        calendars_observation_1 = CalendarsObservation(
            calendars={"c1": [self.calendar_event_1]},
            value_datetime=datetime(2024, 12, 31, tzinfo=ZoneInfo("UTC")),
        )
        calendars_observation_2 = CalendarsObservation(
            calendars={"c1": [self.calendar_event_1]},
            value_datetime=datetime(2024, 12, 31, tzinfo=ZoneInfo("UTC")),
        )
        self.assertEqual(calendars_observation_1, calendars_observation_2)

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_observation_populates_attributes_from_kwargs(self):
        calendars_observation = CalendarsObservation(
            calendars={"c1": [self.calendar_event_1]},
            value_datetime=datetime(2024, 12, 31, tzinfo=ZoneInfo("UTC")),
        )
        self.assertEqual(calendars_observation.calendars, {"c1": [self.calendar_event_1]})
        self.assertEqual(
            calendars_observation.value_datetime, datetime(2024, 12, 31, tzinfo=ZoneInfo("UTC"))
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_observation_calendars_kwarg_validation(self):
        # assert is not None
        with self.assertRaises(StrongTypingError) as ex:
            CalendarsObservation(calendars=None)
        self.assertEqual(
            "'CalendarsObservation.calendars' expected dict[str, list[CalendarEvent]], got None",
            str(ex.exception),
        )

        # assert is dict
        with self.assertRaises(StrongTypingError) as ex:
            CalendarsObservation(calendars=["c1"])
        self.assertEqual(
            "'CalendarsObservation.calendars' expected dict[str, list[CalendarEvent]], got '['c1']' of type list",
            str(ex.exception),
        )

        # assert dict key is str
        with self.assertRaises(StrongTypingError) as ex:
            CalendarsObservation(calendars={1: []})
        self.assertEqual(
            "'CalendarsObservation.calendars[1] key' expected str, got '1' of type int",
            str(ex.exception),
        )

        # assert dict val is list
        with self.assertRaises(StrongTypingError) as ex:
            CalendarsObservation(calendars={"c1": "CalendarEvents"})
        self.assertEqual(
            "'CalendarsObservation.calendars[\"c1\"] value' expected list, got 'CalendarEvents' of type str",
            str(ex.exception),
        )

        # assert dict val is list of CalendarEvent
        with self.assertRaises(StrongTypingError) as ex:
            CalendarsObservation(calendars={"c1": [True]})
        self.assertEqual(
            "'CalendarsObservation.calendars[c1][0]' expected CalendarEvent, got 'True' of type bool",
            str(ex.exception),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendars_observation_value_datetime_kwarg_validation(self):
        # assert is datetime
        with self.assertRaises(StrongTypingError) as ex:
            CalendarsObservation(calendars={}, value_datetime=1)
        self.assertEqual(
            "'CalendarsObservation.value_datetime' expected Optional[datetime] if populated, got '1' of type int",
            str(ex.exception),
        )
        # assert has timezone set
        with self.assertRaises(InvalidSmartContractError) as ex:
            CalendarsObservation(calendars={}, value_datetime=datetime(1, 2, 3))
        self.assertEqual(
            "'value_datetime' of CalendarsObservation is not timezone aware.",
            str(ex.exception),
        )
