from __future__ import annotations  # noqa:F407
from functools import lru_cache
import bisect

from decimal import Decimal
from datetime import datetime
from typing import Optional, Union, Callable, TypeVar, Generic

from ..types import Balance, CalendarEvent, OptionalValue, UnionItemValue
from ...common.docs import _common_docs_path
from .....utils import symbols, types_utils
from .....utils.timezone_utils import validate_timezone_is_utc


_timeseries_value_type_str = (
    "Union[Balance, bool, Decimal, str, datetime, OptionalValue, UnionItemValue, int, None]"
)
_parameter_type_str = "Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int, None]"
_parameter_value_type_str = "Union[datetime, Decimal, str, None]"

TimeseriesItemType = TypeVar("TimeseriesItemType")


class TimeseriesItem(
    types_utils.ContractsLanguageDunderMixin,
    Generic[TimeseriesItemType],
):
    at_datetime: datetime
    value: TimeseriesItemType

    def __init__(self, item, _from_proto=False):
        if not _from_proto:
            validate_timezone_is_utc(
                item[0],
                "at_datetime",
                "TimeseriesItem",
            )
        self.at_datetime = item[0]
        self.value = item[1]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return types_utils.ClassSpec(
            name="TimeseriesItem",
            docstring="""
                Represents a timeseries datapoint, containing a datetime and value.
            """,
            public_attributes=cls._public_attributes(language_code),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="at_datetime",
                type="datetime",
                docstring=(
                    "The datetime of the timeseries datapoint. "
                    "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                ),
            ),
            types_utils.ValueSpec(
                name="value",
                type=_timeseries_value_type_str,
                docstring=(
                    "The value of the Timeseries datapoint at 'at_datetime'. "
                    "The type of this value will depend on the type of the Timeseries "
                    "(such as `BalanceTimeseries`, `FlagTimeseries` or "
                    "`ParameterTimeseries`)."
                ),
            ),
        ]


class Timeseries(list, Generic[TimeseriesItemType]):
    @staticmethod
    def return_on_empty() -> TimeseriesItemType:
        # must be defined for implementations
        raise NotImplementedError("return_on_empty not implemented")

    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, TimeseriesItemType]]] = None,
        _from_proto: bool = False,
    ) -> None:
        self._from_proto = _from_proto
        if iterable is None:
            iterable = []
        self.extend(TimeseriesItem(item, _from_proto) for item in iterable)

    def at(self, *, at_datetime: datetime, inclusive: bool = True) -> TimeseriesItemType:
        validate_timezone_is_utc(
            at_datetime,
            "at_datetime",
            f"{self.__class__.__name__}.at()",
        )
        start_datetimes = [entry.at_datetime for entry in self]
        if inclusive:
            # bisect_right gives the index of the first entry strictly exceeding the datetime
            index = bisect.bisect_right(start_datetimes, at_datetime) - 1
        else:
            # bisect_left gives the index of the first entry exceeding or equal to the datetime
            index = bisect.bisect_left(start_datetimes, at_datetime) - 1
        if index >= 0:
            return self[index].value
        return self.return_on_empty()

    def before(self, *, at_datetime: datetime) -> TimeseriesItemType:
        validate_timezone_is_utc(
            at_datetime,
            "at_datetime",
            f"{self.__class__.__name__}.before()",
        )
        return self.at(at_datetime=at_datetime, inclusive=False)

    def latest(self) -> TimeseriesItemType:
        if not self:
            return self.return_on_empty()
        return self[-1].value

    def all(self) -> list[TimeseriesItem[TimeseriesItemType]]:
        return self

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="Timeseries",
            docstring="A generic timeseries.",
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=(
                        "Returns the latest available TimeseriesItem as of the given timestamp."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="datetime",
                            type="datetime",
                            docstring=(
                                "The timestamp as of which to fetch the latest TimeseriesItem. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="TimeseriesItem",
                        docstring="The latest TimeseriesItem as of the timestamp provided.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available TimeseriesItem as of just before the "
                        "given timestamp."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The timestamp just before which to fetch the "
                                "latest TimeseriesItem. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type=cls.item_type,
                        docstring=(
                            "The latest TimeseriesItem as of just before the timestamp provided."
                        ),
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last available TimeseriesItem in the Timeseries.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="TimeseriesItem",
                        docstring="The latest available TimeseriesItem.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring=(
                        "Returns a list of all available TimeseriesItem values across time."
                    ),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available TimeseriesItem values and their timestamps.",
                    ),
                ),
            ],
        )


class BalanceTimeseries(Timeseries[Balance]):
    return_on_empty: Callable = lambda *_: Balance()

    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, Balance]]] = None,
        _from_proto: bool = False,
    ) -> None:
        super().__init__(iterable, _from_proto)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="BalanceTimeseries",
            docstring=f"""
                A timeseries of balances for the Account.

                The 'at', 'before', and 'latest' methods (and the `.value` attribute of each
                [TimeseriesItem]({_common_docs_path}classes/#TimeseriesItem)
                returned via 'all') return a Balance object.

                To find the "total" balance for the Account, or a given address inside the
                Account, you must sum the relevant Balance objects for the appropriate datetime.
                """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=(
                        "Returns the latest available Balance object as of the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime from which to fetch the latest Balance object. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="Balance",
                        docstring=("The latest Balance object as of the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available Balance object as of just before the "
                        "given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime just before which to fetch the "
                                "latest Balance object. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="Balance",
                        docstring=(
                            "The latest Balance object as of just before the datetime provided."
                        ),
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last available Balance in the Timeseries. If the "
                    "Timeseries is fetched using a `BalancesIntervalFetcher`, the last element "
                    "in the Timeseries can be before or after the hook `effective_datetime` "
                    "depending on the Interval `end`. If no Interval `end` is defined, "
                    "the last known element is returned.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="Balance",
                        docstring="The latest available Balance object.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring=(
                        "Returns a list of all available Balance object values across time."
                    ),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available Balance object values and the datetime for each.",
                    ),
                ),
            ],
        )


class FlagTimeseries(Timeseries[bool]):
    return_on_empty: Callable = lambda *_: False

    def __init__(self, iterable: Optional[list[tuple[datetime, bool]]] = None) -> None:
        super().__init__(iterable)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="FlagTimeseries",
            docstring="""
                    A timeseries for the active status for a given flag definition.
                    If the flag definition does not exist, the timeseries will be empty
                    and .at() will always return False.
                """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=("Returns the latest available flag as of the given datetime."),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime from which to fetch the latest flag. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="bool",
                        docstring=("The latest flag as of the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available flag as of just before the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime just before which to fetch the latest flag. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="bool",
                        docstring=("The latest flag as of just before the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last available flag in the Timeseries.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="bool",
                        docstring="The latest available flag.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring=("Returns a list of all available flag values across time."),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available flag values and their datetimes.",
                    ),
                ),
            ],
        )


class FlagValueTimeseries(Timeseries[bool]):
    return_on_empty: Callable = lambda *_: False

    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, bool]]] = None,
        _from_proto: bool = False,
    ) -> None:
        super().__init__(iterable, _from_proto)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="FlagValueTimeseries",
            docstring="""
                    A timeseries for the active status for a given flag definition.
                    If the flag definition does not exist, the timeseries will be empty
                    and .at() will always return False.
                """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=("Returns the latest available flag as of the given datetime."),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime from which to fetch the latest flag. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="bool",
                        docstring=("The latest flag as of the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available flag as of just before the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime just before which to fetch the latest flag. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="bool",
                        docstring=("The latest flag as of just before the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last available flag value in the Timeseries. If the "
                    "Timeseries is fetched using a `FlagsIntervalFetcher`, the last element "
                    "in the Timeseries can be before or after the hook `effective_datetime` "
                    "depending on the Interval `end`. If no Interval `end` is defined, "
                    "the last known element is returned.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="bool",
                        docstring="The latest available flag.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring=("Returns a list of all available flag values across time."),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available flag values and their datetimes.",
                    ),
                ),
            ],
        )


class ParameterTimeseries(
    Timeseries[Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int, None]]
):
    return_on_empty: Callable = lambda *_: None

    def __init__(
        self,
        iterable: Optional[
            list[
                tuple[
                    datetime,
                    Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int, None],
                ]
            ]
        ] = None,
    ) -> None:
        super().__init__(iterable)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ParameterTimeseries",
            docstring="""
                    A timeseries of Parameter objects.
                """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=(
                        "Returns the latest available Parameter value as of the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime as of which to fetch the latest Parameter value. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type=_parameter_type_str,
                        docstring=("The latest Parameter value as of the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available Parameter value as of immediately before "
                        "the datetime provided."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime just before which to fetch the "
                                "latest Parameter value. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type=_parameter_type_str,
                        docstring=(
                            "The latest Parameter value as of immediately before the datetime "
                            "provided."
                        ),
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last available Parameter value in the Timeseries.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type=_parameter_type_str,
                        docstring="The latest available Parameter value.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring=("Returns a list of all available Parameter values across time."),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available Balance object values and the datetime for each.",
                    ),
                ),
            ],
        )


class ParameterValueTimeseries(Timeseries[Union[datetime, Decimal, str, None]]):
    return_on_empty: Callable = lambda *_: None

    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, Union[datetime, Decimal, str, None]]]] = None,
        _from_proto: bool = False,
    ) -> None:
        super().__init__(iterable, _from_proto)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ParameterValueTimeseries",
            docstring="""
                    A timeseries of Parameter values. For optional parameters this may return `None`
                    at any point in time. For non-optional parameters, Vault will prevent changes
                    that would result in `None`, with the following exceptions:
                      - Setting the `effective_to_timestamp` of an inherited Parameter Value
                      - Cancellation of an inherited Parameter Value
                      - Conversion from a Smart Contract where the parameter was optional, and a
                        future or past time has no value (the change will only be rejected if there
                        is no value at the time the conversion is done)
                """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=(
                        "Returns the latest available Parameter value as of the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime as of which to fetch the latest Parameter value. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type=_parameter_value_type_str,
                        docstring=("The latest Parameter value as of the datetime provided."),
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available Parameter value as of immediately before "
                        "the datetime provided."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime just before which to fetch the "
                                "latest Parameter value. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type=_parameter_value_type_str,
                        docstring=(
                            "The latest Parameter value as of immediately before the datetime "
                            "provided."
                        ),
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last available Parameter value in the Timeseries. If the "
                    "Timeseries is fetched using a `ParametersIntervalFetcher`, the last element "
                    "in the Timeseries can be before or after the hook `effective_datetime` "
                    "depending on the Interval `end`. If no Interval `end` is defined, "
                    "the last known element is returned.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type=_parameter_value_type_str,
                        docstring="The latest available Parameter value.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring=("Returns a list of all available Parameter values across time."),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available Parameter values and their datetimes. "
                        "This function will always return an entry for the start date "
                        "of the Interval. If there is no Parameter value "
                        "defined at the start of the Interval, the value will "
                        "be set to None.",
                    ),
                ),
            ],
        )


class CalendarTimeseries(Timeseries[list[CalendarEvent]]):
    return_on_empty: Callable = lambda *_: []

    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, list[CalendarEvent]]]] = None,
        _from_proto: bool = False,
    ) -> None:
        super().__init__(iterable, _from_proto)

    @staticmethod
    def _from_calendar_events(
        calendar_events: list[CalendarEvent],
        interval_start: datetime,
        interval_end: datetime,
    ) -> CalendarTimeseries:
        """
        Helper method that takes a list of CalendarEvent objects and flattens them into a timeseries.
        Each timeseries item represents the CalendarEvents which are active between the
        corresponding timestamp and the timestamp of the next timeseries item.
        Note that the lists of CalendarEvent objects are ordered
        by (start_datetime, end_datetime, id) ascending.

        The timeseries will always begin with interval_start and end with interval_end.
        """

        """
        E.g.:
        Input Calendar Events:
        Time        <--0------1------2------3------4------5------6------7------8-->
        Interval       |-------------------------------------------------------|
        CE1                   [--------------------)
        CE2                          [--------------------)
        CE3                                 [-------------)
        CE4                                               [--------------------)
        CE5                                               [-------------)

        Output (ordered by end_datetime):
        T0, []
        T1, [CE1]
        T2, [CE1, CE2]
        T3, [CE1, CE2, CE3]
        T4, [CE2, CE3]
        T5, [CE5, CE4]
        T7, [CE4]
        T8, []
        """

        # Add interval start time since this should always be included
        ts: list[tuple[datetime, list[CalendarEvent]]] = [(interval_start, [])]
        time_buckets: set[datetime] = {interval_start}

        # Initialise time buckets for timeseries keys of datetimes for when there is a change of
        # active calendar events
        for ce in calendar_events:
            start_time = interval_start if ce.start_datetime < interval_start else ce.start_datetime
            end_time = interval_end if ce.end_datetime > interval_end else ce.end_datetime
            if start_time not in time_buckets:
                time_buckets.add(start_time)
                ts.append((start_time, []))
            if end_time not in time_buckets:
                time_buckets.add(end_time)
                ts.append((end_time, []))

        ts = sorted(ts, key=lambda v: v[0])

        for ce in calendar_events:
            for dt, events in ts:
                if dt >= ce.end_datetime:
                    # if timestamp is equal to/after CalendarEvent has ended, this CE is not active
                    break
                if ce.start_datetime <= dt:
                    # if timestamp is after or equal to CalendarEvent start (and CalendarEvent has
                    # not ended as per check above), this CE must be active, so append
                    events.append(ce)

        # Sort calendar events by (start_datetime, end_datetime, id) to ensure determinism.
        for _, events in ts:
            events.sort(key=lambda ce: (ce.start_datetime, ce.end_datetime, ce.id))

        return CalendarTimeseries(ts)

    @staticmethod
    @lru_cache()
    def _spec(language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="CalendarTimeseries",
            docstring=f"""
                A timeseries of active calendar events.

                The 'at', 'before', and 'latest' methods (and the `.value` attribute of each
                [TimeseriesItem]({_common_docs_path}classes/#TimeseriesItem)
                returned via 'all') return a list of CalendarEvent objects.

                Each timeseries item is a `List[CalendarEvent]` which represents the calendar events
                which are active between the corresponding timestamp and the timestamp of
                the next timeseries item.
                Note that the list of CalendarEvent objects in the timeseries item are ordered
                by (start_datetime, end_datetime, id) ascending.
                """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="at",
                    docstring=(
                        "Returns the latest available active calendar events as of the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The datetime at which to fetch the active calendar events for. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="List[CalendarEvent]",
                        docstring="The active calendar events at the datetime provided.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring=(
                        "Returns the latest available active calendar events as of immediately "
                        "before the given datetime."
                    ),
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring=(
                                "The timestamp just before which to fetch the "
                                "latest active calendar events. "
                                "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                            ),
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="List[CalendarEvent]",
                        docstring="The active calendar events at the datetime provided.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring=(
                        "Returns the last available active calendar events in the Timeseries. When the "
                        "Timeseries is fetched using a `CalendarsIntervalFetcher`, the last element "
                        "in the Timeseries can be before or after the hook `effective_datetime` "
                        "depending on the Interval `end`. If no Interval `end` is defined, "
                        "the last known timeseries element is returned."
                    ),
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[CalendarEvent]",
                        docstring="The latest available active calendar events.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring="Returns a list of all active CalendarEvents across time.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="List[TimeseriesItem]",
                        docstring="All available active calendar events and their datetimes. "
                        "This function will always return an entry for the start date "
                        "of the Interval. If there are no active calendar events "
                        "at the start of the Interval, the value will "
                        "be set to an empty list.",
                    ),
                ),
            ],
        )


class DiscreteTimeseries(list, Generic[TimeseriesItemType]):
    # By definition of discrete timeseries, if timestamp not in timeseries, the result must be None.
    return_on_empty: Callable = lambda *_: None

    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, TimeseriesItemType]]] = None,
        _from_proto: bool = False,
    ) -> None:
        self._from_proto = _from_proto
        if iterable is None:
            iterable = []
        self.extend(TimeseriesItem(item, _from_proto) for item in iterable)

    def get(self, *, at_datetime: datetime) -> Optional[TimeseriesItem]:
        validate_timezone_is_utc(
            at_datetime,
            "at_datetime",
            f"{self.__class__.__name__}.get()",
        )
        for entry in self:
            if at_datetime == entry.at_datetime:
                return entry
        return self.return_on_empty()

    def before(self, *, at_datetime: datetime) -> Optional[TimeseriesItem]:
        validate_timezone_is_utc(
            at_datetime,
            "at_datetime",
            f"{self.__class__.__name__}.before()",
        )
        start_datetimes = [entry.at_datetime for entry in self]
        index = bisect.bisect_left(start_datetimes, at_datetime) - 1
        if index >= 0:
            return self[index]
        return self.return_on_empty()

    def after(self, *, at_datetime: datetime) -> Optional[TimeseriesItem]:
        validate_timezone_is_utc(
            at_datetime,
            "at_datetime",
            f"{self.__class__.__name__}.after()",
        )
        start_datetimes = [entry.at_datetime for entry in self]
        index = bisect.bisect_right(start_datetimes, at_datetime)
        if index < len(start_datetimes):
            return self[index]
        return self.return_on_empty()

    def latest(self) -> TimeseriesItem:
        if not self:
            # There should always be at least one item in a fetched
            # DiscreteTimeseries so this should not happen.
            return self.return_on_empty()
        return self[-1]

    def all(self) -> list[TimeseriesItem[TimeseriesItemType]]:
        return self

    def between(
        self,
        *,
        start_datetime: datetime,
        end_datetime: datetime,
        inclusive_start_datetime: bool = True,
        inclusive_end_datetime: bool = True,
    ) -> DiscreteTimeseries:
        validate_timezone_is_utc(
            start_datetime,
            "start_datetime",
            f"{self.__class__.__name__}.between()",
        )
        validate_timezone_is_utc(
            end_datetime,
            "end_datetime",
            f"{self.__class__.__name__}.between()",
        )
        if inclusive_start_datetime and inclusive_end_datetime:
            iterable = [
                (entry.at_datetime, entry.value)
                for entry in self
                if start_datetime <= entry.at_datetime <= end_datetime
            ]
        elif inclusive_start_datetime and (not inclusive_end_datetime):
            iterable = [
                (entry.at_datetime, entry.value)
                for entry in self
                if start_datetime <= entry.at_datetime < end_datetime
            ]
        elif (not inclusive_start_datetime) and inclusive_end_datetime:
            iterable = [
                (entry.at_datetime, entry.value)
                for entry in self
                if start_datetime < entry.at_datetime <= end_datetime
            ]
        elif (not inclusive_start_datetime) and (not inclusive_end_datetime):
            iterable = [
                (entry.at_datetime, entry.value)
                for entry in self
                if start_datetime < entry.at_datetime < end_datetime
            ]
        return DiscreteTimeseries(iterable=iterable, _from_proto=self._from_proto)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        # TODO(TM-90457): populate spec
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name=f"{cls.__name__}",
            docstring="",
            public_attributes=[],
            public_methods=[],
        )





class BalanceDiscreteTimeseries(DiscreteTimeseries[Balance]):
    def __init__(
        self,
        iterable: Optional[list[tuple[datetime, Balance]]] = None,
        _from_proto: bool = False,
    ) -> None:
        super().__init__(iterable, _from_proto)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name=f"{cls.__name__}",
            docstring=f"""
                A discrete timeseries of balances for the Account.

                The `get()`, `before()`, `after()`, and `latest()` methods return a
                [TimeseriesItem]({_common_docs_path}classes/#TimeseriesItem) object, where the
                `.value` of each `TimeseriesItem` returns a
                [Balance]({_common_docs_path}classes/#Balance) object.

                The `between()` method returns a subset of the discrete timeseries.

                To find the total balance for the Account or a given address inside the
                Account, sum the relevant `Balance` objects for the appropriate datetime.
            """,
            public_attributes=[],
            public_methods=[
                types_utils.MethodSpec(
                    name="get",
                    docstring="""
                        Returns the `TimeseriesItem` object at a given datetime in the
                        `BalanceDiscreteTimeseries`. If the given datetime does not have
                        an associated `TimeseriesItem`, returns `None`.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring="""
                                The datetime from which to fetch the `TimeseriesItem` object.
                                Must be a timezone-aware UTC datetime using the ZoneInfo class.
                            """,
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="TimeseriesItem | None",
                        docstring="The `TimeseriesItem` object at the datetime provided.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="before",
                    docstring="""
                        Returns the `TimeseriesItem` object just before a given datetime in the
                        `BalanceDiscreteTimeseries`. If there are no such datapoints, returns `None`.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring="""
                                The datetime just before which to fetch the `TimeseriesItem` object.
                                Must be a timezone-aware UTC datetime using the ZoneInfo class.
                            """,
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="TimeseriesItem | None",
                        docstring="The `TimeseriesItem` object at just before the datetime provided.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="after",
                    docstring="""
                        Returns the `TimeseriesItem` object just after a given datetime in the
                        `BalanceDiscreteTimeseries`. If there are no such datapoints, returns `None`.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="at_datetime",
                            type="datetime",
                            docstring="""
                                The datetime just after which to fetch the `TimeseriesItem` object.
                                Must be a timezone-aware UTC datetime using the ZoneInfo class.
                            """,
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="TimeseriesItem | None",
                        docstring="The `TimeseriesItem` object at just after the datetime provided.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="latest",
                    docstring="Returns the last `TimeseriesItem` object in the `BalanceDiscreteTimeseries`.",
                    args=[],
                    return_value=types_utils.ReturnValueSpec(
                        type="TimeseriesItem",
                        docstring="The last `TimeseriesItem` object in the timeseries.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="all",
                    docstring="""
                        Returns a list of all available `TimeseriesItem` objects across
                        the discrete interval.
                    """,
                    args=[],
                    return_value=types_utils.ReturnValueSpec(
                        type="List[TimeseriesItem]",
                        docstring="All available `TimeseriesItem` objects.",
                    ),
                ),
                types_utils.MethodSpec(
                    name="between",
                    docstring="""
                        Returns a subset of the original `BalanceDiscreteTimeseries`
                        which contains the datapoints between the `start_datetime` and
                        `end_datetime` inclusively. If there are no datapoints between
                        these timestamps, the timeseries will be empty.
                    """,
                    args=[
                        types_utils.ValueSpec(
                            name="start_datetime",
                            type="datetime",
                            docstring="""
                                The start datetime of the range of the subset.
                                Must be a timezone-aware UTC datetime using the ZoneInfo class.
                            """,
                        ),
                        types_utils.ValueSpec(
                            name="end_datetime",
                            type="datetime",
                            docstring="""
                                The end datetime of the range of the subset.
                                Must be a timezone-aware UTC datetime using the ZoneInfo class.
                            """,
                        ),
                    ],
                    return_value=types_utils.ReturnValueSpec(
                        type="BalanceDiscreteTimeseries",
                        docstring="""
                            The subset of the `BalanceDiscreteTimeseries` laying
                            between `start_datetime` and `end_datetime` inclusively.
                        """,
                    ),
                ),
            ],
        )
