from datetime import datetime
from functools import lru_cache
from typing import Optional, Union, List, Tuple

from .schedules import EndOfMonthSchedule

from ...common.docs import _common_docs_path
from .....utils import cron
from .....utils import exceptions
from .....utils import symbols
from .....utils import types_utils
from .....utils.timezone_utils import validate_datetime_is_timezone_aware, validate_timezone_is_utc
from .....utils.feature_flags import is_fflag_enabled

from .....utils.feature_flags import ADJUSTMENTS


class EventTypesGroup(types_utils.ContractsLanguageDunderMixin):
    def __init__(self, *, name: str, event_types_order: List[str]):
        self.name = name
        self.event_types_order = event_types_order
        self._validate_attributes()

    def _validate_attributes(self):
        if self.name is None or self.name == "":
            raise exceptions.InvalidSmartContractError("EventTypesGroup 'name' must be populated")

        types_utils.get_iterator(
            self.event_types_order, "str", "event_types_order", check_empty=True
        )
        if len(self.event_types_order) < 2:
            raise exceptions.InvalidSmartContractError(
                "An EventTypesGroup must have at least two event types"
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        docstring = f"""
            A [group of event types](/reference/scheduler/#concepts-schedule_groups) that defines
            the scheduling order for events in the group. If any EventTypesGroup is
            defined in a Smart Contract, a list of
            [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)s must also be defined.
            Every event type from a group must be defined in the event types list.
            EventTypesGroups are unique for each account. Events associated with different
            accounts are **NOT** added to the same group even if the EventTypesGroup names
            match.

            Any events within an EventTypesGroup that are supervised with
            [flexible supervision](/reference/contracts/contracts_api_4xx/supervisor_overview/#flexible_supervision)
            will no longer be considered a part of that EventTypesGroup. This means that:
            * Supervised events are **not** guaranteed to be executed in the order
             specified by the original EventTypesGroup. However, unsupervised events are
             guaranteed to be executed in the specified order.
            * Vault skips the original event (defined in the Smart Contract) and the Supervisor
             Contract event runs instead. Since an account is not aware of whether it is being
             supervised, the original event will report a success and the next event
             in the EventTypesGroup will be triggered immediately
             (regardless of whether the Supervisor Contract event has run).
        """

        return types_utils.ClassSpec(
            name="EventTypesGroup",
            docstring=docstring,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new EventTypesGroup",
                args=cls._public_attributes(language_code),
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="name",
                type="str",
                docstring="""
                    The name of the EventTypesGroup. Names have to be unique within a Smart
                    Contract.
                """,
            ),
            types_utils.ValueSpec(
                name="event_types_order",
                type="List[str]",
                docstring=f"""
                    A list of string [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)
                     names that belong to a group. A group consists of at least two
                    [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)s.
                    A [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)
                    cannot belong to more than one group. This list defines the order of
                    [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)s
                    inside a group.
                    Any [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)s
                    grouped together are executed based on the order of this list.
                    Note: in a Supervisor Contract, Event Types are of type
                    [SupervisorContractEventType]({_common_docs_path}classes/#SupervisorContractEventType).
                """,
            ),
        ]


class ScheduleExpression(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        second: Optional[Union[str, int]] = None,
        minute: Optional[Union[str, int]] = None,
        hour: Optional[Union[str, int]] = None,
        day: Optional[Union[str, int]] = None,
        month: Optional[Union[str, int]] = None,
        day_of_week: Optional[Union[str, int]] = None,
        year: Optional[Union[str, int]] = None,
    ):
        self.second = second
        self.minute = minute
        self.hour = hour
        self.day = day
        self.month = month
        self.day_of_week = day_of_week
        self.year = year
        self._validate_attributes()

    def __str__(self):
        has_seen_least_significant_field = False
        fields_and_defaults = [
            (self.second, "0"),
            (self.minute, "0"),
            (self.hour, "0"),
            (self.day_of_week, "*"),
            (self.day, "1"),
            (self.month, "1"),
            (self.year, "*"),
        ]
        cron_fields = []
        for field, default in fields_and_defaults:
            if field is not None:
                cron_fields.append(str(field))
                has_seen_least_significant_field = True
            else:
                cron_fields.append("*" if has_seen_least_significant_field else default)

        # The fields take an order of precedence `second < minute < hour < day_of_week < day < month < year`
        # to assign default values. However, when displaying this as a cron expression, Vault uses a
        # generic format of "{second} {minute} {hour} {day} {month} {day_of_week} {year}".
        # For example, this matches the format of the `time_expression` field under the
        # corresponding Core API `Schedule` object.
        cron_fields[3], cron_fields[4], cron_fields[5] = (
            cron_fields[4],
            cron_fields[5],
            cron_fields[3],
        )

        return " ".join(cron_fields)

    def _validate_attributes(self):
        types_utils.validate_type(
            self.second,
            (int, str),
            prefix="second",
            is_optional=True,
            check_empty=True,
        )
        types_utils.validate_type(
            self.minute,
            (int, str),
            prefix="minute",
            is_optional=True,
            check_empty=True,
        )
        types_utils.validate_type(
            self.hour,
            (int, str),
            prefix="hour",
            is_optional=True,
            check_empty=True,
        )
        types_utils.validate_type(
            self.day,
            (int, str),
            prefix="day",
            is_optional=True,
            check_empty=True,
        )
        types_utils.validate_type(
            self.month,
            (int, str),
            prefix="month",
            is_optional=True,
            check_empty=True,
        )
        types_utils.validate_type(
            self.day_of_week,
            (int, str),
            prefix="day_of_week",
            is_optional=True,
            check_empty=True,
        )
        types_utils.validate_type(
            self.year,
            (int, str),
            prefix="year",
            is_optional=True,
            check_empty=True,
        )
        if all(
            attr is None
            for attr in [
                self.second,
                self.hour,
                self.minute,
                self.day,
                self.month,
                self.day_of_week,
                self.year,
            ]
        ):
            raise exceptions.InvalidSmartContractError("Empty ScheduleExpression not allowed")
        if not cron.validate_cron(str(self)):
            raise exceptions.InvalidSmartContractError(
                f"Invalid cron expression defined by ScheduleExpression: [{str(self)}]"
            )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="second", type="Optional[Union[str, int]]", docstring="Second (0-59)."
            ),
            types_utils.ValueSpec(
                name="minute", type="Optional[Union[str, int]]", docstring="Minute (0-59)."
            ),
            types_utils.ValueSpec(
                name="hour", type="Optional[Union[str, int]]", docstring="Hour (0-23)."
            ),
            types_utils.ValueSpec(
                name="day",
                type="Optional[Union[str, int]]",
                docstring='Day of the month (1-31). "last" may be used to denote the last day of the month.',
            ),
            types_utils.ValueSpec(
                name="month",
                type="Optional[Union[str, int]]",
                docstring="Month (1-12 or jan-dec, case-insensitive).",
            ),
            types_utils.ValueSpec(
                name="day_of_week",
                type="Optional[Union[str, int]]",
                docstring="Day of the week (0-6 or mon-sun, case-insensitive).",
            ),
            types_utils.ValueSpec(
                name="year", type="Optional[Union[str, int]]", docstring="Year (4-digit year)."
            ),
        ]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduleExpression",
            docstring=(
                "The schedule definition associated with an Event Type. All schedule definition "
                "attributes must be based on the Account's operating timezone. The "
                "[events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone) "
                "is inherited from the "
                "[Processing Group](/reference/processing_groups/), "
                "if set. Otherwise it can be set as a field defined in the "
                "[Smart](../../smart_contracts_api_reference4xx/metadata/#events_timezone) and "
                "[Supervisor](../../supervisor_contracts_api_reference4xx/metadata/#events_timezone) "
                "Contract metadata. If neither of these is set, "
                "[vault.events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone) "
                "defaults to UTC. Complex expressions under each attribute are supported with the following rules:\n"
                "[%autowidth,options='header'] \n"
                "|=== \n"
                "|Expression |Description \n"
                "\n"
                "|* |Fire on every value \n"
                "| */a      | Fire on every `a`th value, starting from the minimum. \n"
                "| a-b      | Fire on any value within the `a-b` range (`a` must be smaller than `b`). \n"
                "| a-b/c    a| Fire on every `c`th value within the `a-b` range. \n"
                "| x,y,z    | Fire on any matching expression; can combine any number of any of the above expressions. \n"
                "|=== \n"
            ),
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring=(
                    "Constructs a new ScheduleExpression. At least one of the optional attributes "
                    "must be provided. Fields take an order of precedence `second < minute < hour < day_of_week < day < month < year`, "
                    "where fields after the first explicitly defined field default to `*`, while "
                    "the fields before that default to their minimum values. "
                    "`day_of_week` always defaults to `*`. For example, `day=1, minute=20` is "
                    "equivalent to `second=0, minute=20, hour='\*', day=1, month='*', day_of_week='\*', year='*'`. "
                    "The scheduled event will then execute on the first day of every month on "
                    "every year at the 20th minute of every hour."
                ),
                args=cls._public_attributes(language_code),
            ),
        )


class ScheduleSkip(types_utils.ContractsLanguageDunderMixin):
    def __init__(self, *, end: datetime, _from_proto: bool = False):
        self.end = end
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if self.end is None:
            raise exceptions.InvalidSmartContractError("ScheduleSkip 'end' must be populated")
        types_utils.validate_type(self.end, datetime)
        validate_datetime_is_timezone_aware(
            self.end,
            "end",
            "ScheduleSkip",
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduleSkip",
            docstring="""
                Defines the skip period for a Schedule.
            """,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ScheduleSkip object.",
                args=cls._public_attributes(language_code),
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        return [
            types_utils.ValueSpec(
                name="end",
                type="datetime",
                docstring=(
                    "The local datetime until which the Schedule will be skipped. "
                    "Must be timezone aware using the `ZoneInfo` class and be based "
                    "on the Account's operating timezone. The "
                    "[events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone) "
                    "is inherited from the "
                    "[Processing Group](/reference/processing_groups/), "
                    "if set. Otherwise it can be set as a field defined in the "
                    "[Smart](../../smart_contracts_api_reference4xx/metadata/#events_timezone) or "
                    "[Supervisor](../../supervisor_contracts_api_reference4xx/metadata/#events_timezone) "
                    "Contract metadata. If neither of these is set, "
                    "[vault.events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone) "
                    "defaults to UTC."
                ),
            )
        ]


class ScheduledEvent(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        expression: Optional[ScheduleExpression] = None,
        schedule_method: Optional[EndOfMonthSchedule] = None,
        skip: Optional[Union[bool, ScheduleSkip]] = False,
        _from_proto: bool = False,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.expression = expression
        self.schedule_method = schedule_method
        self.skip = skip
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        # None is only allowed for existing scheduled events returned via `conversion_hook`.
        # This is validated in the private subclass of the ScheduledEvent.
        types_utils.validate_type(
            self.start_datetime,
            datetime,
            is_optional=True,
            hint="datetime",
            prefix="ScheduledEvent.start_datetime",
        )
        if self.start_datetime is not None:
            validate_datetime_is_timezone_aware(
                self.start_datetime,
                "start_datetime",
                "ScheduledEvent",
            )
        types_utils.validate_type(
            self.end_datetime,
            datetime,
            is_optional=True,
            hint="datetime",
            prefix="ScheduledEvent.end_datetime",
        )
        if self.end_datetime is not None:
            validate_datetime_is_timezone_aware(
                self.end_datetime,
                "end_datetime",
                "ScheduledEvent",
            )
        types_utils.validate_type(
            self.expression,
            ScheduleExpression,
            is_optional=True,
            hint="ScheduleExpression",
            prefix="ScheduledEvent.expression",
        )
        types_utils.validate_type(
            self.schedule_method,
            EndOfMonthSchedule,
            is_optional=True,
            hint="EndOfMonthSchedule",
            prefix="ScheduledEvent.schedule_method",
        )
        types_utils.validate_type(
            self.skip,
            (bool, ScheduleSkip),
            is_optional=True,
            hint="Union[bool, ScheduleSkip]",
            prefix="ScheduledEvent.skip",
        )

        if self.expression and self.schedule_method:
            raise exceptions.InvalidSmartContractError(
                "ScheduledEvent must not have both expression and schedule_method set"
            )
        if not self.expression and not self.schedule_method:
            raise exceptions.InvalidSmartContractError(
                "ScheduledEvent must have exactly one of expression or schedule_method set"
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ScheduledEvent",
            docstring="The native representation of a schedule which an event will adhere to.",
            public_attributes=cls._public_attributes(language_code),  # noqa SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new ScheduledEvent object.",
                args=cls._public_attributes(language_code),  # noqa SLF001
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="start_datetime",
                type="Optional[datetime]",
                docstring="""
                    The datetime from which the schedule will be effective.
                    Must be timezone aware using the `ZoneInfo` class and be based
                    on the Account's operating timezone. The
                    [events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone)
                    is inherited from the
                    [Processing Group](/reference/processing_groups/),
                    if set. Otherwise it can be set as a field defined in the
                    [Smart](../../smart_contracts_api_reference4xx/metadata/#events_timezone) or
                    [Supervisor](../../supervisor_contracts_api_reference4xx/metadata/#events_timezone)
                    Contract metadata. If neither of these is set,
                    [vault.events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone)
                    defaults to UTC. Note that the `start_datetime` is required for any new
                    `ScheduledEvents` returned by `activation_hook` or `conversion_hook`.
                    However, existing schedules will start from their last
                    successful execution time and so the `start_datetime` for existing
                    `ScheduledEvent`s in the `conversion_hook` must be omitted (or set to None, or remain
                    unchanged), as any other value will result in an error.
                    Note that the `start_datetime` cannot be before a hook `effective_datetime`
                    for new `event_types` returned in the account or plan `activation_hook`
                    and `conversion_hook`.
                """,
            ),
            types_utils.ValueSpec(
                name="end_datetime",
                type="Optional[datetime]",
                docstring="""
                    The datetime until which the schedule will be effective.
                    Must be timezone aware using the `ZoneInfo` class and be based
                    on the Account's operating timezone. The
                    [events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone)
                    is inherited from the
                    [Processing Group](/reference/processing_groups/),
                    if set. Otherwise it can be set as a field defined in the
                    [Smart](../../smart_contracts_api_reference4xx/metadata/#events_timezone) or
                    [Supervisor](../../supervisor_contracts_api_reference4xx/metadata/#events_timezone)
                    Contract metadata. If neither of these is set,
                    [vault.events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone)
                    defaults to UTC.
                """,
            ),
            types_utils.ValueSpec(
                name="expression",
                type="Optional[ScheduleExpression]",
                docstring="""
                    The cron expression defining the schedule, represented as a native object.
                    Either `expression` or `schedule_method` must be populated.
                """,
            ),
            types_utils.ValueSpec(
                name="schedule_method",
                type="Optional[EndOfMonthSchedule]",
                docstring="""
                    The schedule definition for a recurring monthly event, represented as a
                    native object. Either `expression` or `schedule_method` must be
                    populated.
                """,
            ),
            types_utils.ValueSpec(
                name="skip",
                type="Optional[Union[bool, ScheduleSkip]]",
                docstring="""
                    Skip a schedule until a given datetime. If set to `True`, the schedule will
                    be skipped indefinitely until this field is updated.
                """,
            ),
        ]


class EventType(types_utils.ContractsLanguageDunderMixin):
    def __init__(self, *, name: str, scheduler_tag_ids: Optional[List[str]] = None):
        self.name = name
        self.scheduler_tag_ids = scheduler_tag_ids
        self._validate_attributes()

    def _validate_attributes(self):
        if self.name is None or self.name == "":
            raise exceptions.InvalidSmartContractError(
                f"{self.__class__.__name__} 'name' must be populated. "
                + f"Current attributes are {repr(self)}"
            )

        if self.scheduler_tag_ids:
            iterator = types_utils.get_iterator(self.scheduler_tag_ids, "str", "scheduler_tag_ids")
            for item in iterator:
                types_utils.validate_type(item, str, hint="str")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="EventType",
            docstring=f"""
                Each scheduled event in a Smart Contract has an event type associated with it.
                Each event type must have a unique name within each Smart Contract and can have
                optional Scheduler tags. Each Smart Contract must include a list of all
                [SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)s
                included in its [activation_hook](../../smart_contracts_api_reference4xx/hooks/#activation_hook) and
                [conversion_hook](../../smart_contracts_api_reference4xx/hooks/#conversion_hook).
            """,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new EventType", args=cls._public_attributes(language_code)
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="name",
                type="str",
                docstring="""
                    The name of the Event Type. This name will be the same as the name defined in
                    [activation_hook](../../smart_contracts_api_reference4xx/hooks/#activation_hook) or
                    [conversion_hook](../../smart_contracts_api_reference4xx/hooks/#conversion_hook).
                """,
            ),
            types_utils.ValueSpec(
                name="scheduler_tag_ids",
                type="Optional[List[str]]",
                docstring="""
                    An optional list of string ids for the
                    [account schedule tags](/api/core_api/#Account_schedule_tags-AccountScheduleTag) of an
                    Event Type. The tags must be created in the Scheduler
                    before they are referenced in a Smart Contract. Vault Core environments
                    with the Multiple Processing Groups Extension enforce this on Product
                    Version creation. The tag IDs are global in Vault and must exactly match the
                    tag IDs created in the Scheduler. Event Types in different contracts with the
                    same tag will be linked together. Defaults to no tags if a tag ID is not
                    provided.
                """,
            ),
        ]


class SmartContractEventType(EventType):
    def __init__(
        self,
        *,
        name: str,
        scheduler_tag_ids: Optional[List[str]] = None,
        adjustment_point: Optional[bool] = None,
    ):
        if is_fflag_enabled(ADJUSTMENTS):
            self.adjustment_point = adjustment_point
            types_utils.validate_type(
                self.adjustment_point,
                bool,
                prefix="SmartContractEventType.adjustment_point",
                is_optional=True,
            )
            if self.adjustment_point is None:
                self.adjustment_point = False
        else:
            if adjustment_point is not None:
                raise exceptions.IllegalPython(
                    "SmartContractEventType.__init__() got unexpected keyword argument 'adjustment_point'"
                )
        super().__init__(name=name, scheduler_tag_ids=scheduler_tag_ids)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SmartContractEventType",
            docstring=(
                "Each scheduled event in a Smart Contract has an event type associated with it. "
                "Each event type must have a unique name within each Smart Contract and can have "
                "optional Scheduler tags. Each Smart Contract must include a list of all "
                f"[SmartContractEventType]({_common_docs_path}classes/#SmartContractEventType)"
                "s included in its "
                "[activation_hook](../../smart_contracts_api_reference4xx/hooks/#activation_hook) and "
                "[conversion_hook](../../smart_contracts_api_reference4xx/hooks/#conversion_hook)."
            ),
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SmartContractEventType",
                args=cls._public_attributes(language_code),
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")
        public_attributes = super()._public_attributes(language_code)
        if is_fflag_enabled(ADJUSTMENTS):
            public_attributes.append(
                types_utils.ValueSpec(
                    name="adjustment_point",
                    type="Optional[bool]",
                    docstring="""
                        If set to `True` then the schedule will be marked as an adjustment point.
                        If the adjustment_strategy is `AdjustmentStrategy.SCHEDULE_TRIGGERED` then an
                        adjustment process will be run before the scheduled_event_hook for that
                        event is executed. An `adjustment_point` can only be set to `True` if the
                        adjustment_strategy is defined in the metadata of the Smart Contract. If the
                        adjustment_strategy is `AdjustmentStrategy.SCHEDULE_TRIGGERED`, then at least one
                        SmartContractEventType will need to have `adjustment_point = True`. The
                        default value of `adjustment_point` is `False`.
                    """,
                ),
            )
        return public_attributes


class SupervisorContractEventType(EventType):
    def __init__(
        self,
        *,
        name: str,
        scheduler_tag_ids: Optional[List[str]] = None,
        overrides_event_types: Optional[List[Tuple[str, str]]] = None,
    ):
        self.overrides_event_types = overrides_event_types
        super().__init__(name=name, scheduler_tag_ids=scheduler_tag_ids)

    def _validate_attributes(self):
        super()._validate_attributes()

        if self.overrides_event_types:
            iterator = types_utils.get_iterator(
                self.overrides_event_types, "Tuple[str, str]", "overrides_event_types"
            )
            for item in iterator:
                types_utils.validate_type(item, tuple, hint="Tuple[str, str]")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="SupervisorContractEventType",
            docstring=(
                "Each scheduled event in a Supervisor Contract has an event type associated with it. "
                "Each event type must have a unique name within each Supervisor Contract and can have "
                "optional Scheduler tags. Each Supervisor Contract must include a list of all "
                f"[SupervisorContractEventType]({_common_docs_path}classes/#SupervisorContractEventType)s"
                " included in its "
                "[activation_hook](../../supervisor_contracts_api_reference4xx/hooks/#activation_hook) and "
                "[conversion_hook](../../supervisor_contracts_api_reference4xx/hooks/#conversion_hook)."
            ),
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new SupervisorContractEventType",
                args=cls._public_attributes(language_code),
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        public_attributes = EventType._public_attributes(language_code)  # noqa: SLF001
        public_attributes.append(
            types_utils.ValueSpec(
                name="overrides_event_types",
                type="Optional[List[Tuple[str, str]]]",
                docstring=f"""
                    A list of (Smart Contract `alias`, `event_type`) tuples specifying which are the overridden Schedules for each
                    [SupervisorContractEventType]({_common_docs_path}classes/#SupervisorContractEventType).
                    If not provided, this
                    [SupervisorContractEventType]({_common_docs_path}classes/#SupervisorContractEventType)
                    does not override any of the Supervisee Schedules. The Smart Contract alias is the alias
                    defined in the [SmartContractDescriptor]({_common_docs_path}classes/#SmartContractDescriptor).
                    Note that each SupervisorContractEventType can only override one Schedule
                    per Supervisee. If multiple Supervisee Schedules need to be overridden,
                    this has to be done using multiple Supervisee EventTypes.
                """,
            ),
        )
        return public_attributes





class LastScheduledEventDateTimesObservation(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        last_scheduled_event_datetimes: dict[str, Optional[datetime]],
        value_datetime: Optional[datetime] = None,
        _from_proto: bool = False,
    ):
        self.value_datetime = value_datetime
        self.last_scheduled_event_datetimes = last_scheduled_event_datetimes
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        self._validate_value_datetime_arg()
        types_utils.validate_type(
            self.last_scheduled_event_datetimes,
            dict,
            check_empty=True,
            hint="dict[str, Optional[datetime]]",
            prefix=f"{self.__class__.__name__}.last_scheduled_event_datetimes",
        )

        for key, value in self.last_scheduled_event_datetimes.items():
            if isinstance(value, datetime):
                validate_timezone_is_utc(
                    self.last_scheduled_event_datetimes[key],
                    'last_scheduled_event_datetimes["' + key + '"]',
                    "LastScheduledEventDateTimesObservation",
                )

    def _validate_value_datetime_arg(self):
        types_utils.validate_type(
            self.value_datetime,
            datetime,
            is_optional=True,
            hint="datetime",
            prefix=f"{self.__class__.__name__}.value_datetime",
        )
        if self.value_datetime:
            validate_timezone_is_utc(
                self.value_datetime,
                "value_datetime",
                LastScheduledEventDateTimesObservation.__name__,
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name=cls.__name__,
            docstring=f"""
                A mapping of event types to last scheduled event datetime at a fixed point in time.

                [IMPORTANT]
                ====
                Existing Customer Accounts cannot be converted to a Smart Contract with
                [LastScheduledEventDateTimesObservationFetcher]({_common_docs_path}classes/#LastScheduledEventDateTimesObservationFetcher)
                if their current Smart Contract is not already using it, due to data access limitations.
                Future Vault Core improvements aim to address these limitations.
                ====
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
                name="last_scheduled_event_datetimes",
                type="dict[str, Optional[datetime]]",
                docstring="""
                    Map of event type to last scheduled event datetime.
                    If the `event_type` has never executed successfully, the mapped value is `None`.
                """,
            ),
            types_utils.ValueSpec(
                name="value_datetime",
                type="Optional[datetime]",
                docstring=(
                    "The datetime at which the last scheduled event datetimes are observed. "
                    "This is a timezone-aware UTC datetime using the ZoneInfo class. "
                    "This attribute will be None for a live observation."
                ),
            ),
        ]
