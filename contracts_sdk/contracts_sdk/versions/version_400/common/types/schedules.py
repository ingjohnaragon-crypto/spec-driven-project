from functools import lru_cache
from decimal import Decimal

from .enums import ScheduleFailover

from .....utils import exceptions, symbols, types_utils
from ...common.docs import _common_docs_path


class EndOfMonthSchedule(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        failover: ScheduleFailover = ScheduleFailover.FIRST_VALID_DAY_BEFORE,
    ):
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.failover = failover
        self._validate_attributes()

    def _validate_attributes(self):
        class_name = self.__class__.__name__

        for item_name, item, allowed_range in [
            ("day", self.day, range(1, 32)),
            ("hour", self.hour, range(0, 24)),
            ("minute", self.minute, range(0, 60)),
            ("second", self.second, range(0, 60)),
        ]:
            types_utils.validate_type(
                item,
                (Decimal, int),
                hint="int",
                prefix=f"{class_name}.{item_name}",
            )
            if item % 1 != 0:
                raise exceptions.InvalidSmartContractError(
                    f"Argument {item_name} of EndOfMonthSchedule object is"
                    f" not an integer value in range({allowed_range[0]}-{allowed_range[-1]})."
                )
            if item not in allowed_range:
                raise exceptions.InvalidSmartContractError(
                    f"Argument {item_name} of EndOfMonthSchedule object is"
                    f" out of range({allowed_range[0]}-{allowed_range[-1]})."
                )
        types_utils.validate_type(self.failover, ScheduleFailover, prefix=f"{class_name}.failover")

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(name="day", type="int", docstring="Day of the month (1-31)."),
            types_utils.ValueSpec(
                name="hour", type="Optional[int]", docstring="Hour of the day (0-23)."
            ),
            types_utils.ValueSpec(
                name="minute", type="Optional[int]", docstring="Minute of the hour (0-59)."
            ),
            types_utils.ValueSpec(
                name="second", type="Optional[int]", docstring="Second of the minute (0-59)."
            ),
            types_utils.ValueSpec(
                name="failover",
                type="Optional[ScheduleFailover]",
                docstring="The failover strategy for this schedule.",
            ),
        ]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="EndOfMonthSchedule",
            docstring="",
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring=f"""
                Define a recurring monthly schedule that automatically handles the varying lengths
                of different months. You must place the definitions within the `schedule_method`
                attribute for a given event; define this event with a
                [ScheduledEvent]({_common_docs_path}classes/#ScheduledEvent)
                within [activation_hook](../../smart_contracts_api_reference4xx/hooks/#activation_hook)
                or [conversion_hook](../../smart_contracts_api_reference4xx/hooks/#conversion_hook)
                or within the `schedule_method` attribute of the
                [UpdateAccountEventTypeDirective]({_common_docs_path}classes/#UpdateAccountEventTypeDirective)
                or [UpdatePlanEventTypeDirective]({_common_docs_path}classes/#UpdatePlanEventTypeDirective)
                classes, so that the schedule recurs on a monthly basis. This method is available
                for both Smart and Supervisor Contracts.

                Note: You can only use EndOfMonthSchedule with
                [vault.events_timezone](/reference/contracts/contracts_api_4xx/smart_contracts_api_reference4xx/vault/#attributes-events_timezone)
                set to its default of UTC.

                """,
                args=cls._public_attributes(language_code),
            ),
        )
