from typing import Optional

from ...common.docs import _common_docs_path
from .enums import DateFailover
from .....utils import exceptions, types_utils

from functools import lru_cache
from .....utils import symbols




class Period(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        days: Optional[int] = None,
        months: Optional[int] = None,
        date_failover: Optional[DateFailover] = None,
    ):
        self.class_name = self.__class__.__name__
        self.days = days
        self.months = months
        self.date_failover = (
            DateFailover.FIRST_VALID_DAY_BEFORE
            if date_failover is None and self.months is not None
            else date_failover
        )
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(
            self.days,
            int,
            is_optional=True,
            prefix=f"{self.class_name}.days",
        )
        types_utils.validate_type(
            self.months,
            int,
            is_optional=True,
            prefix=f"{self.class_name}.months",
        )
        types_utils.validate_type(
            self.date_failover,
            DateFailover,
            is_optional=True,
            prefix=f"{self.class_name}.date_failover",
        )
        if (self.days is not None and self.months is not None) or (
            self.days is None and self.months is None
        ):
            raise exceptions.InvalidSmartContractError(
                f"Exactly one of {self.class_name}.days or {self.class_name}.months must be populated."
            )
        if self.days is not None:
            if self.days <= 0:
                raise exceptions.InvalidSmartContractError(
                    f"Attribute {self.class_name}.days must be greater than 0, got value {self.days}."
                )
            elif self.date_failover is not None:
                raise exceptions.InvalidSmartContractError(
                    f"Attribute {self.class_name}.date_failover cannot be populated with {self.class_name}.days."
                )
        if self.months is not None:
            if self.months <= 0:
                raise exceptions.InvalidSmartContractError(
                    f"Attribute {self.class_name}.months must be greater than 0, got value {self.months}."
                )
            elif not self.date_failover:
                raise exceptions.InvalidSmartContractError(
                    f"Attribute {self.class_name}.date_failover must be populated."
                )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="days",
                type="Optional[int]",
                docstring="""
                    Exactly one of `days` or `months` should be specified. 
                    The unit of the sampling period measured in days, as a positive 
                    integer.
                """,
            ),
            types_utils.ValueSpec(
                name="months",
                type="Optional[int]",
                docstring="""
                    Exactly one of `days` or `months` should be specified. 
                    The unit of the sampling period measured in months, as a positive 
                    integer. The discrete interval fetcher
                    will fetch the data on a monthly basis on the 
                    same calendar day as the fetcher `start`.
                """,
            ),
            types_utils.ValueSpec(
                name="date_failover",
                type="Optional[DateFailover]",
                docstring=f"""
                    The [DateFailover]({_common_docs_path}enums/#DateFailover) to specify the 
                    failover strategy for the monthly sampling period when the calendar day 
                    falls outside the particular month. If it is not set, 
                    it defaults to `DateFailover.FIRST_VALID_DAY_BEFORE`.
                """,
            ),
        ]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="Period",
            docstring=(
                "The fixed time between balance observations in discrete interval fetchers. "
                "Exactly one of `days` or `months` must be specified. \n"
                """\n**Examples:**
                * `Period(days=2)` indicates that the observation points are on every 
                other day. 
                * `Period(months=3, date_failover=DateFailover.FIRST_VALID_DAY_AFTER)`
                indicates that the observation points are every 3 months on the same calendar 
                day as fetcher `start`. If the next observation point falls outside the particular 
                month, the observation point will be the first valid day 
                after the missing day in the month."""
            ),
            constructor=types_utils.ConstructorSpec(
                docstring="",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF00
        )
