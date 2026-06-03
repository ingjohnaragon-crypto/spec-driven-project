from decimal import Decimal
from unittest import TestCase

from ..types.attribute_data_types import AttributeDateTimeType, AttributeDecimalType
from ..types.attributes import Attribute

from .....utils.feature_flags import (
    ACCOUNT_ATTRIBUTE_HOOK,
    skip_if_not_enabled,
)

from .....utils import exceptions




class TestPublicCommonV400Attributes(TestCase):
    # Attribute

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_constructor_valid(self):
        Attribute(name="attribute", data_type=AttributeDecimalType())

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_constructor_raises_name_invalid(self):
        with self.assertRaises(exceptions.InvalidSmartContractError) as e:
            Attribute(name=" ", data_type=AttributeDateTimeType())
        expected = "'name' must be a non-empty string"

        self.assertEqual(expected, str(e.exception))

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_constructor_raises_name_none(self):
        with self.assertRaises(exceptions.StrongTypingError) as e:
            Attribute(name=None, data_type=AttributeDateTimeType())
        expected = "'name' expected str, got None"

        self.assertEqual(expected, str(e.exception))

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_constructor_raises_type_invalid(self):
        with self.assertRaises(exceptions.StrongTypingError) as e:
            Attribute(name="attribute", data_type=Decimal)
        expected = "'data_type' expected Union[AttributeDecimalType, AttributeDateTimeType, AttributeStringType], got '<class 'decimal.Decimal'>'"
        self.assertEqual(expected, str(e.exception))

    @skip_if_not_enabled(ACCOUNT_ATTRIBUTE_HOOK)
    def test_attribute_constructor_type_valid_constructor_raises_not_called(self):
        with self.assertRaises(exceptions.StrongTypingError) as e:
            Attribute(name="attribute", data_type=AttributeDecimalType)
        expected_prefix = "'data_type' expected Union[AttributeDecimalType, AttributeDateTimeType, AttributeStringType], got '<class "
        self.assertIn(expected_prefix, str(e.exception))

    
