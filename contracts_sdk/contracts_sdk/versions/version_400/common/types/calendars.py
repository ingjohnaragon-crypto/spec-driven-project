from datetime import datetime
from functools import lru_cache


from .....utils import symbols, types_utils
from .....utils.timezone_utils import validate_timezone_is_utc

from typing import List, Optional


class CalendarEvent(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        id: str,
        calendar_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
        _from_proto: bool = False,
    ):
        self.id = id
        self.calendar_id = calendar_id
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        validate_timezone_is_utc(
            self.start_datetime,
            "start_datetime",
            "CalendarEvent",
        )
        validate_timezone_is_utc(
            self.end_datetime,
            "end_datetime",
            "CalendarEvent",
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="id",
                type="str",
                docstring="""
                    Uniquely identifies the Calendar Event in the Vault Calendar resource.
                """,
            ),
            types_utils.ValueSpec(
                name="calendar_id",
                type="str",
                docstring="""
                    The ID of the Calendar that this Calendar Event belongs to.
                """,
            ),
            types_utils.ValueSpec(
                name="start_datetime",
                type="datetime",
                docstring="""
                    The logical datetime at which the Calendar Event is effective from (inclusive).
                    Must be a timezone-aware UTC datetime using the ZoneInfo class.
                """,
            ),
            types_utils.ValueSpec(
                name="end_datetime",
                type="datetime",
                docstring="""
                    The logical datetime at which the Calendar Event is effective to (exclusive).
                    Must be a timezone-aware UTC datetime using the ZoneInfo class.
                """,
            ),
        ]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="CalendarEvent",
            docstring="""
                A unique event resource defined in the Vault Calendar.
            """,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="",
                args=cls._public_attributes(language_code),
            ),
        )


class CalendarEvents(list):
    def __init__(self, *, calendar_events: Optional[List[CalendarEvent]] = None):
        calendar_events_default_list = []
        if calendar_events is not None:
            calendar_events_default_list = calendar_events
        super().__init__(calendar_events_default_list)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="CalendarEvents",
            docstring="A list of CalendarEvent objects.",
            constructor=types_utils.ConstructorSpec(
                docstring="",
                args=[
                    types_utils.ValueSpec(
                        name="calendar_events",
                        type="Optional[List[CalendarEvent]]",
                        docstring="""
                            A list of CalendarEvent objects.
                        """,
                    ),
                ],
            ),
        )


class CalendarsObservation(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        calendars: dict[str, list[CalendarEvent]],
        value_datetime: Optional[datetime] = None,
        _from_proto: bool = False,
    ):
        self.value_datetime = value_datetime
        self.calendars = calendars
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        self._validate_calendars_arg()
        self._validate_value_datetime_arg()

    def _validate_calendars_arg(self):
        types_utils.validate_type(
            self.calendars,
            dict,
            check_empty=True,
            hint=f"dict[str, list[{CalendarEvent.__name__}]]",
            prefix=f"{self.__class__.__name__}.calendars",
        )
        for k, v in self.calendars.items():
            types_utils.validate_type(
                k,
                str,
                check_empty=True,
                prefix=f"{self.__class__.__name__}.calendars[{k}] key",
            )
            types_utils.validate_type(
                v,
                list,
                prefix=f'{self.__class__.__name__}.calendars["{k}"] value',
            )
            for i, calendar_event in enumerate(v):
                types_utils.validate_type(
                    calendar_event,
                    CalendarEvent,
                    prefix=f"{self.__class__.__name__}.calendars[{k}][{i}]",
                )

    def _validate_value_datetime_arg(self):
        types_utils.validate_type(
            self.value_datetime,
            datetime,
            is_optional=True,
            hint="Optional[datetime]",
            prefix=f"{self.__class__.__name__}.value_datetime",
        )
        if self.value_datetime:
            validate_timezone_is_utc(
                self.value_datetime,
                "value_datetime",
                CalendarsObservation.__name__,
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name=cls.__name__,
            docstring="""
                A mapping of calendar IDs to active calendar events at a fixed point in time.
            """,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="", args=cls._public_attributes(language_code)
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return [
            types_utils.ValueSpec(
                name="calendars",
                type=f"Dict[str, List[{CalendarEvent.__name__}]",
                docstring="Map of calendar ID to list of active calendar events at the given time.",
            ),
            types_utils.ValueSpec(
                name="value_datetime",
                type="Optional[datetime]",
                docstring="""
                    The datetime at which the calendars are observed.
                    This attribute will be None for a live observation.
                    Must be a timezone-aware UTC datetime using the ZoneInfo class.
                """,
            ),
        ]
