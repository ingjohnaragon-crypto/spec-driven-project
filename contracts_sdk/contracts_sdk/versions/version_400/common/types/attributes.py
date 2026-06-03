from typing import Union
from functools import lru_cache

from .attribute_data_types import AttributeDateTimeType, AttributeDecimalType, AttributeStringType
from .....utils import symbols, types_utils





class Attribute(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        name: str,
        data_type: Union[AttributeDateTimeType, AttributeDecimalType, AttributeStringType],
    ):
        self.name = name
        self.data_type = data_type
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(self.name, str, prefix="name", check_empty=True)
        types_utils.validate_type(
            self.data_type,
            (AttributeDecimalType, AttributeDateTimeType, AttributeStringType),
            prefix="data_type",
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="Attribute",
            docstring="""
                A property of the Account associated with this Smart Contract whose
                value is calculated by executing the [attribute_hook](../../smart_contracts_api_reference4xx/hooks/#attribute_hook).
            """,
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new Attribute object.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_attributes=cls._public_attributes(language_code),  # noqa: SLF001
            public_methods=[],
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
                docstring="The name of the attribute. This must be unique across all attributes in the Contract metadata.",
            ),
            types_utils.ValueSpec(
                name="data_type",
                type="Union[AttributeDecimalType, AttributeDateTimeType, AttributeStringType]",
                docstring="The expected type of the value that is returned when [attribute_hook](../../smart_contracts_api_reference4xx/hooks/#attribute_hook) is invoked for this attribute.",
            ),
        ]



