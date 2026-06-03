from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from inspect import isclass
from typing import Optional, Union

from .enums import ParameterLevel, ParameterUpdatePermission

from ...common.docs import _common_docs_path
from .....utils import exceptions
from .....utils import symbols
from .....utils import types_utils
from .....utils.timezone_utils import validate_timezone_is_utc


_parameter_value_type_str = "Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int]"


class Shape(types_utils.ContractsLanguageDunderMixin):
    """Used as base class for type checking"""

    def _validate_attributes(self):
        """
        Perform shape attribute validation when required.
        E.g. StringShape does not require any attribute validation,
        so calling this empty base class method is valid.
        """

    @staticmethod
    def _validate_native_value(value: str, *_):
        types_utils.validate_type(value, str)


class NumberShape(Shape):
    def __init__(
        self,
        *,
        min_value: Optional[Union[Decimal, int]] = None,
        max_value: Optional[Union[Decimal, int]] = None,
        step: Optional[Union[Decimal, int]] = None,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(
            self.min_value, (Decimal, int), prefix="min_value", is_optional=True
        )
        types_utils.validate_type(
            self.max_value, (Decimal, int), prefix="max_value", is_optional=True
        )
        types_utils.validate_type(self.step, (Decimal, int), prefix="step", is_optional=True)
        if self.min_value and self.max_value and self.min_value > self.max_value:
            raise exceptions.InvalidSmartContractError(
                "NumberShape min_value must be less than max_value"
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="NumberShape",
            docstring="""
                A Parameter shape defining a floating-point number.

                Note: This only applies to Smart Contract Parameters. For the Core API Parameters
                constraint equivalent, see [Parameter shape to constraint mapping](/vault_core_overview/whats_new_in_vc5/overview#parameter_shape_to_constraint_mapping).

                Metadata `max_value`, `min_value` and `step` can be associated with the parameter,
                but not all metadata is validated by Vault. Only `GLOBAL` and `INSTANCE` level
                parameter fields `max_value` and `min_value` are validated.

                Parameter value type: `Union[Decimal, int]`.
            """,
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new NumberShape.",
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
                name="min_value",
                type="Optional[Union[Decimal, int]]",
                docstring="Metadata describing the minimum allowed numerical value.",
            ),
            types_utils.ValueSpec(
                name="max_value",
                type="Optional[Union[Decimal, int]]",
                docstring="Metadata describing the maximum allowed numerical value.",
            ),
            types_utils.ValueSpec(
                name="step",
                type="Optional[Union[Decimal, int]]",
                docstring="Metadata describing the step in allowed values.",
            ),
        ]

    @staticmethod
    def _validate_native_value(value: Union[Decimal, int], *_):  # type: ignore
        types_utils.validate_type(value, (Decimal, int))


class StringShape(Shape):
    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="StringShape",
            docstring="""
                A Parameter shape defining a string.

                Note: This only applies to Smart Contract Parameters. For the Core API Parameters
                constraint equivalent, see [Parameter shape to constraint mapping](/vault_core_overview/whats_new_in_vc5/overview#parameter_shape_to_constraint_mapping).

                Parameter value type: `str`.
            """,
            public_attributes=[],
            public_methods=[],
        )


class AccountIdShape(Shape):
    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="AccountIdShape",
            docstring="""
                A Parameter shape defining an Account id (a string).

                Note: This only applies to Smart Contract Parameters. For the Core API Parameters
                constraint equivalent, see [Parameter shape to constraint mapping](/vault_core_overview/whats_new_in_vc5/overview#parameter_shape_to_constraint_mapping).

                Parameter value type: `str`.
            """,
            public_attributes=[],
            public_methods=[],
        )


class DenominationShape(Shape):
    def __init__(self, *, permitted_denominations: Optional[list[str]] = None):
        self.permitted_denominations = permitted_denominations
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(
            self.permitted_denominations,
            list,
            is_optional=True,
            hint="list[str]",
            prefix="permitted_denominations",
        )
        if self.permitted_denominations is not None:
            iterator = types_utils.get_iterator(
                self.permitted_denominations, "str", "permitted_denominations", check_empty=False
            )
            for item in iterator:
                types_utils.validate_type(item, str)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="DenominationShape",
            docstring="""
                A Parameter shape defining an denomination (a string).

                Note: This only applies to Smart Contract Parameters. For the Core API Parameters
                constraint equivalent, see [Parameter shape to constraint mapping](/vault_core_overview/whats_new_in_vc5/overview#parameter_shape_to_constraint_mapping).

            """,
            constructor=types_utils.ConstructorSpec(
                docstring="""
                    Constructs a new DenominationShape.

                    Parameter value type: `str`.
                """,
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
                name="permitted_denominations",
                type="Optional[List[str]]",
                docstring="Metadata describing which denominations are permitted.",
            ),
        ]


class DateShape(Shape):
    def __init__(
        self,
        *,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
    ):
        self.min_date = min_date
        self.max_date = max_date
        self._validate_attributes()

    def _validate_attributes(self):
        types_utils.validate_type(self.min_date, datetime, prefix="min_date", is_optional=True)
        types_utils.validate_type(self.max_date, datetime, prefix="max_date", is_optional=True)
        if self.min_date:
            validate_timezone_is_utc(
                self.min_date,
                "min_date",
                "DateShape",
            )
        if self.max_date:
            validate_timezone_is_utc(
                self.max_date,
                "max_date",
                "DateShape",
            )
        if self.min_date and self.max_date and self.max_date < self.min_date:
            raise exceptions.InvalidSmartContractError(
                "DateShape min_date must be less than max_date"
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="DateShape",
            docstring=f"""
                Specifies that the enclosing [Parameter]({_common_docs_path}classes/#Parameter)
                object refers to a date, whose value is a Python datetime. The datetime assignment takes the form
                `datetime(YYYY, MM, DD)`, where the datetime value needs to be a valid date. Any
                value that does not use the date format `%Y-%m-%d` will trigger an `IllegalPython`
                error.

                Note: This only applies to Smart Contract Parameters. For the Core API Parameters
                constraint equivalent, see [Parameter shape to constraint mapping](/vault_core_overview/whats_new_in_vc5/overview#parameter_shape_to_constraint_mapping).

                You can optionally set `min_date` and `max_date` to bound acceptable values.

                Parameter value type: `datetime`.
            """,
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new DateShape.",
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
                name="min_date",
                type="Optional[datetime]",
                docstring=(
                    "Metadata describing which the earliest allowed date. "
                    "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                ),
            ),
            types_utils.ValueSpec(
                name="max_date",
                type="Optional[datetime]",
                docstring=(
                    "Metadata describing which the latest allowed date. "
                    "Must be a timezone-aware UTC datetime using the ZoneInfo class."
                ),
            ),
        ]

    @staticmethod
    def _validate_native_value(value: datetime, *_):  # type: ignore
        types_utils.validate_type(value, datetime)


class UnionItem(types_utils.ContractsLanguageDunderMixin):
    def __init__(self, *, key: str, display_name: str):
        self.key = key
        self.display_name = display_name
        self._validate_attributes()

    def _validate_attributes(self):
        if not self.key:
            raise exceptions.StrongTypingError("UnionItem init arg 'key' must be populated")
        if not self.display_name:
            raise exceptions.StrongTypingError(
                "UnionItem init arg 'display_name' must be populated"
            )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="UnionItem",
            docstring=f"Specifies a permissible value inside a [UnionShape]({_common_docs_path}classes/#UnionShape).",
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new UnionItem.",
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
                name="key",
                type="str",
                docstring=("The string value by which this choice is programmatically accessible."),
            ),
            types_utils.ValueSpec(
                name="display_name",
                type="str",
                docstring=(
                    "The name of the option as could be shown on a front-end user interface."
                ),
            ),
        ]


class UnionItemValue(types_utils.ContractsLanguageDunderMixin):
    def __init__(self, key: str, _from_proto: Optional[bool] = False):
        self.key = key
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        if not self.key:
            raise exceptions.StrongTypingError("UnionItemValue init arg 'key' must be populated")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="UnionItemValue",
            docstring=(
                f"A wrapper for the key of a [UnionItem]({_common_docs_path}classes/#UnionItem). "
                f"Used as the value type for [UnionShape]({_common_docs_path}classes/#UnionShape) "
                f"parameter (see "
                f"[ParameterTimeseries]({_common_docs_path}classes/#ParameterTimeseries) and "
                f"[DerivedParameterHookResult]({_common_docs_path}classes/#DerivedParameterHookResult))."
            ),
            public_attributes=cls._public_attributes(),  # noqa: SLF001
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a UnionItemValue used to represent a [UnionItem]"
                f"({_common_docs_path}classes/#UnionItem) key.",
                args=cls._public_attributes(language_code),  # noqa: SLF001
            ),
            public_methods=[],
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="key",
                type="str",
                docstring=f"""
                The string value by which this choice is programmatically accessible.
                This key value should exist as a [UnionItem]({_common_docs_path}classes/#UnionItem)
                key within the [UnionShape]({_common_docs_path}classes/#UnionShape) items.
                """,
            )
        ]

    def _validate_native_value(self):
        types_utils.validate_type(self.key, str, prefix="key")


class UnionShape(Shape):
    def __init__(self, *, items: list[UnionItem]):
        self.items = items
        try:
            self._validate_attributes()
        except exceptions.StrongTypingError as ex:
            raise exceptions.StrongTypingError(f"{self.__class__.__name__} __init__ {ex.args[0]}")

    def _validate_attributes(self):
        iterator = types_utils.get_iterator(self.items, "UnionItem", "items", check_empty=True)
        seen_items = set()
        for item in iterator:
            types_utils.validate_type(item, UnionItem)
            if item.key in seen_items:
                raise exceptions.InvalidSmartContractError(
                    f"Parameter contains duplicate UnionItem {item.key}"
                )
            seen_items.add(item.key)

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="UnionShape",
            docstring="""
                Specifies a choice of multiple values.

                Note: This only applies to Smart Contract Parameters. For the Core API Parameters
                constraint equivalent, see [Parameter shape to constraint mapping](/vault_core_overview/whats_new_in_vc5/overview#parameter_shape_to_constraint_mapping).

                Parameter value type: `UnionItemValue`.
            """,
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new UnionShape.",
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
                name="items", type="List[UnionItem]", docstring="The allowed values."
            )
        ]

    @staticmethod
    def _validate_native_value(value: UnionItemValue, keys: list[str]):  # type: ignore
        types_utils.validate_type(value, UnionItemValue)
        value._validate_native_value()  # noqa: SLF001
        if value.key not in keys:
            raise exceptions.InvalidSmartContractError(
                f'UnionItemValue with key "{value.key}" not allowed in this UnionShape'
            )


class OptionalValue(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        value: Optional[
            Union[
                Decimal,
                str,
                datetime,
                UnionItemValue,
                int,
            ]
        ] = None,
        _from_proto: Optional[bool] = False,
    ):
        self.value = value
        if not _from_proto:
            self._validate_attributes()

    def _validate_attributes(self):
        types = (Decimal, str, datetime, UnionItemValue, int)
        type_names = ["Decimal", "str", "datetime", "UnionItemValue", "int"]
        types_utils.validate_type(
            self.value,
            types,
            hint=f"Union[{', '.join(type_names)}]",
            is_optional=True,
            prefix="OptionalValue.value",
        )

        if isinstance(self.value, datetime):
            validate_timezone_is_utc(
                self.value,
                "value",
                "OptionalValue",
            )
        if isinstance(self.value, UnionItemValue):
            self.value._validate_attributes()  # noqa: SLF001

    def is_set(self):
        return self.value is not None

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="OptionalValue",
            docstring="Specifies an optional Parameter value",
            public_attributes=[
                types_utils.ValueSpec(
                    name="value", type="Any", docstring="The value, if specified."
                )
            ],
            constructor=types_utils.ConstructorSpec(
                docstring="",
                args=[
                    types_utils.ValueSpec(
                        name="value",
                        type="Optional[Union[Decimal, str, datetime, UnionItemValue, int]]",
                        docstring=(
                            "The optional parameter value. If using a `datetime` it "
                            "must be a timezone-aware UTC datetime using the ZoneInfo class."
                        ),
                    )
                ],
            ),
            public_methods=[
                types_utils.MethodSpec(
                    name="is_set",
                    docstring="Returns True if the value is set, otherwise False.",
                    args=[],
                    return_value=types_utils.ValueSpec(
                        name=None,
                        type="bool",
                        docstring="True if the value is set, otherwise False.",
                    ),
                )
            ],
        )


class OptionalShape(Shape):
    def __init__(
        self,
        *,
        shape: Union[
            AccountIdShape, DateShape, DenominationShape, NumberShape, StringShape, UnionShape
        ],
    ):
        self.shape = shape
        self._validate_attributes()

    def _validate_attributes(self):
        # Validate the shape arg up-front to provide a user friendly error message
        if isclass(self.shape) and issubclass(self.shape, Shape):
            raise exceptions.StrongTypingError(
                f"OptionalShape init arg 'shape' must be an instance of {self.shape.__name__} class"
            )
        types_utils.validate_type(
            self.shape,
            (AccountIdShape, DateShape, DenominationShape, NumberShape, StringShape, UnionShape),
            prefix="shape",
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="OptionalShape",
            docstring="""
                Specifies that the enclosed Shape is optional.

                Note: This only applies to Smart Contract Parameters.

                Parameter value type: `OptionalValue`.
            """,
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new OptionalShape.",
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
                name="shape",
                type="Union[AccountIdShape, DateShape, DenominationShape, NumberShape, "
                "StringShape, UnionShape]",
                docstring="The optional inner Shape.",
            ),
        ]

    @staticmethod
    def _validate_native_value(value: OptionalValue, *_):  # type: ignore
        types_utils.validate_type(value, OptionalValue)
        value._validate_attributes()  # noqa: SLF001


class Parameter(types_utils.ContractsLanguageDunderMixin):
    def __init__(
        self,
        *,
        name: str,
        shape: Union[
            AccountIdShape,
            DateShape,
            DenominationShape,
            NumberShape,
            OptionalShape,
            StringShape,
            UnionShape,
        ],
        level: ParameterLevel,
        derived: Optional[bool] = False,
        display_name: Optional[str] = "",
        description: Optional[str] = "",
        default_value: Optional[
            Union[Decimal, str, datetime, OptionalValue, UnionItemValue, int]
        ] = None,
        update_permission: Optional[ParameterUpdatePermission] = None,
    ):
        self.name = name
        self.shape = shape
        self.level = level
        self.derived = derived
        self.display_name = display_name
        self.description = description
        self.default_value = default_value
        self.update_permission = update_permission
        self._validate_attributes()

    def _validate_attribute_types(self):
        # Validate up-front that the shape is an instance of Shape class for user friendly error
        if isclass(self.shape) and issubclass(self.shape, Shape):
            raise exceptions.StrongTypingError(
                f"Parameter init arg 'shape' for parameter '{self.name}' must be an "
                f"instance of the {self.shape.__name__} class"
            )

        shape_types = (
            AccountIdShape,
            DateShape,
            DenominationShape,
            NumberShape,
            OptionalShape,
            StringShape,
            UnionShape,
        )
        default_value_types = (Decimal, str, datetime, OptionalValue, UnionItemValue, int)

        try:
            types_utils.validate_type(self.name, str, check_empty=True, prefix="name")
            types_utils.validate_type(self.shape, shape_types, hint="", prefix="shape")
            types_utils.validate_type(self.level, ParameterLevel, prefix="level")
            types_utils.validate_type(self.derived, bool, prefix="derived", is_optional=True)
            types_utils.validate_type(
                self.display_name, str, prefix="display_name", is_optional=True
            )
            types_utils.validate_type(self.description, str, prefix="description", is_optional=True)
            types_utils.validate_type(
                self.default_value, default_value_types, prefix="default_value", is_optional=True
            )
            types_utils.validate_type(
                self.update_permission,
                ParameterUpdatePermission,
                prefix="update_permission",
                hint="ParameterUpdatePermission",
                is_optional=True,
            )
        except (exceptions.StrongTypingError, exceptions.InvalidSmartContractError) as ex:
            raise type(ex)("Parameter attribute " + str(ex.args[0]))

    def _validate_attributes(self):
        self._validate_attribute_types()

        optional = isinstance(self.shape, OptionalShape)
        if (
            self.level == ParameterLevel.INSTANCE
            and self.default_value is None
            and not optional
            and not self.derived
        ):
            raise exceptions.InvalidSmartContractError(
                "Instance Parameters with non optional shapes must have a default value: "
                f"{self.name}"
            )
        if not optional and isinstance(self.default_value, OptionalValue):
            raise exceptions.InvalidSmartContractError(
                f"Non optional shapes must have a non optional default value: {self.name}"
            )
        if self.derived and self.level != ParameterLevel.INSTANCE:
            raise exceptions.InvalidSmartContractError(
                f"Derived Parameters can only be INSTANCE level: {self.name}"
            )
        if self.derived and (self.default_value or self.update_permission):
            raise exceptions.InvalidSmartContractError(
                f"Derived Parameters cannot have a default value or update permissions: {self.name}"
            )
        if isinstance(self.default_value, datetime):
            validate_timezone_is_utc(
                self.default_value,
                "default_value",
                "Parameter",
            )
        if self.default_value is not None:
            actual_shape = self.shape
            default_value = self.default_value
            if optional:
                # First validate default_value is OptionalValue
                # Then validate OptionalValue.value against OptionalShape.shape
                actual_shape._validate_native_value(default_value)  # noqa: SLF001
                actual_shape = actual_shape.shape
                default_value = self.default_value.value

            if isinstance(actual_shape, UnionShape):
                actual_shape._validate_native_value(  # noqa: SLF001
                    default_value, [i.key for i in actual_shape.items]
                )
            else:
                actual_shape._validate_native_value(default_value)  # noqa: SLF001

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="Parameter",
            docstring="A contract parameter.",
            constructor=types_utils.ConstructorSpec(
                docstring="Constructs a new Parameter.",
                args=cls._public_attributes(language_code),  # noqa SLF001
            ),
            public_attributes=cls._public_attributes(language_code),  # noqa SLF001
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
                docstring="""
                    The name of the Parameter. This is how the Parameter is referred to
                    programmatically by the Smart Contract when it fetches the Parameter
                    value from the ParameterTimeseries.
                """,
            ),
            types_utils.ValueSpec(
                name="shape",
                type=(
                    "Union[AccountIdShape, DateShape, DenominationShape, NumberShape, "
                    "OptionalShape, StringShape, UnionShape]"
                ),
                docstring="The shape of the parameter.",
            ),
            types_utils.ValueSpec(
                name="level", type="ParameterLevel", docstring="The level of the Parameter."
            ),
            types_utils.ValueSpec(
                name="derived",
                type="Optional[bool]",
                docstring="""
                    Whether this parameter is derived or not.
                    Only applicable to INSTANCE level Parameter objects.
                """,
            ),
            types_utils.ValueSpec(
                name="display_name",
                type="Optional[str]",
                docstring="""The display name of the Parameter. This may be used in a front-end
                    user interface.""",
            ),
            types_utils.ValueSpec(
                name="description",
                type="Optional[str]",
                docstring="""
                    The description of the Parameter. This may be used in a front-end
                    user interface to show a user the meaning of the Parameter.
                """,
            ),
            types_utils.ValueSpec(
                name="default_value",
                type=f"Optional[{_parameter_value_type_str}]",
                docstring="""
                    The default value of the Parameter. This is only applicable to INSTANCE level
                    Parameters, and will only be used if an Account Migration
                    converts an Account to a Product Version that introduces
                    this Parameter. It will not be used as a default if an Account is created on a
                    Product Version which uses this Parameter.
                """,
            ),
            types_utils.ValueSpec(
                name="update_permission",
                type="Optional[ParameterUpdatePermission]",
                docstring="""
                    Whether the user is allowed to update the Parameter or not.
                    Must be provided for INSTANCE level Parameter objects.
                    Is not supported for DERIVED/TEMPLATE level parameters.
                """,
            ),
        ]
