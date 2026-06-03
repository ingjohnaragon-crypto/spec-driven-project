from datetime import datetime
from typing import Optional, Dict
from functools import lru_cache

from .....utils import symbols, types_utils
from .....utils.timezone_utils import validate_timezone_is_utc


class FlagsObservation(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        flags: Dict[str, bool],
        value_datetime: Optional[datetime] = None,
        _from_proto: bool = False,
    ):
        self.flags = flags
        self.value_datetime = value_datetime
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(
            self.value_datetime,
            datetime,
            prefix="FlagsObservation.value_datetime",
            is_optional=True,
        )
        if self.value_datetime is not None:
            validate_timezone_is_utc(
                self.value_datetime,
                "value_datetime",
                "FlagsObservation",
            )
        types_utils.validate_type(
            self.flags, dict, hint="dict[str, bool]", prefix="FlagsObservation.flags"
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="FlagsObservation",
            docstring="""
                A mapping of flag IDs to their values at a fixed point in time.
            """,
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new FlagsObservation object.",
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
                name="flags",
                type="Union[Dict[str, bool], defaultdict[str, bool]]",
                docstring="""
                    The flags at the given datetime. This value has type defaultdict if
                    the FlagsObservationFetcher did not provide a FlagsFilter. Otherwise, this
                    value has type dict, containing an entry for each of the flag definition
                    ids specified in the FlagsFilter of the interval fetcher.
                """,
            ),
            types_utils.ValueSpec(
                name="value_datetime",
                type="Optional[datetime]",
                docstring="""
                    The time at which the flags are observed. This attribute will be None for
                    a live observation. Must be a timezone-aware UTC datetime using
                    the ZoneInfo class.
                """,
            ),
        ]
