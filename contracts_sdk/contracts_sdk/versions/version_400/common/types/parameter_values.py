from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import Dict, Union, Optional


from .....utils import symbols, types_utils
from .....utils.timezone_utils import validate_timezone_is_utc

_parameter_value_type_str = "Union[datetime, Decimal, str, None]"


class ParametersObservation(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        parameters: Dict[str, Union[str, datetime, Decimal, None]],
        value_datetime: Optional[datetime],
        _from_proto: bool = False,
    ):
        self.value_datetime = value_datetime
        self.parameters = parameters
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if self.value_datetime:
            validate_timezone_is_utc(
                self.value_datetime,
                "value_datetime",
                "ParametersObservation",
            )
        for key, value in self.parameters.items():
            if isinstance(value, datetime):
                validate_timezone_is_utc(
                    self.parameters[key],
                    'parameters["' + key + '"]',
                    "ParametersObservation",
                )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="ParametersObservation",
            docstring="A mapping of parameter IDs to their values at a fixed point in time.",
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
                name="parameters",
                type=f"Dict[str, {_parameter_value_type_str}]",
                docstring="Map of parameter ID to value.",
            ),
            types_utils.ValueSpec(
                name="value_datetime",
                type="Optional[datetime]",
                docstring=(
                    "The datetime at which the parameters are observed. "
                    "This is a timezone-aware UTC datetime using the ZoneInfo class. "
                    "This attribute will be None for a live observation."
                ),
            ),
        ]
