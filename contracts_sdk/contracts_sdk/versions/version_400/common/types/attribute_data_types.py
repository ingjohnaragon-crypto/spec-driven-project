from datetime import datetime
from decimal import Decimal
from functools import lru_cache

from .....utils import symbols, types_utils


class AttributeDataType(types_utils.ContractsLanguageDunderMixin):
    """Base class used to declare an attributes data type."""

    _valid_data_types: list


class AttributeDecimalType(AttributeDataType):
    def __init__(self) -> None:
        self._valid_data_types = [Decimal]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="AttributeDecimalType",
            docstring="""
                An attribute data type indicating that the returned attribute value must
                be a `Decimal` type or None.
            """,
            public_attributes=[],
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new AttributeDecimalType object.",
                args=[],
            ),
        )


class AttributeDateTimeType(AttributeDataType):
    def __init__(self) -> None:
        self._valid_data_types = [datetime]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="AttributeDateTimeType",
            docstring="""
                An attribute data type indicating that the returned attribute value must
                be a `datetime` type or None.
            """,
            public_attributes=[],
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new AttributeDateTimeType object.",
                args=[],
            ),
        )


class AttributeStringType(AttributeDataType):
    def __init__(self) -> None:
        self._valid_data_types = [str]

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="AttributeStringType",
            docstring="""
                An attribute data type indicating that the returned attribute value must
                be a `str` type or None.
            """,
            public_attributes=[],
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new AttributeStringType object.",
                args=[],
            ),
        )
