from unittest import TestCase
from unittest.mock import Mock, call, patch

from ..types.periods import Period

from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)

from .....utils import exceptions

from ..types import periods
from ..types.enums import DateFailover

from .....utils.exceptions import (
    StrongTypingError,
    InvalidSmartContractError,
)



from .....utils.feature_flags import (
    BALANCES_DISCRETE_INTERVAL_FETCHER,
    
    skip_if_not_enabled,
)


class TestPublicCommonV400DateFailover(TestCase):
    def test_date_failover_enum(self):
        self.assertEqual(DateFailover.FIRST_VALID_DAY_BEFORE.value, 1)
        self.assertEqual(DateFailover.FIRST_VALID_DAY_AFTER.value, 2)

    def test_date_failover_raises_with_unknown(self):
        with self.assertRaises(ValueError) as e:
            DateFailover(0)
        self.assertEqual(str(e.exception), "0 is not a valid DateFailover")





class TestPublicCommonV400Period(TestCase):
    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_repr(self):
        period = Period(days=1)
        self.assertTrue(issubclass(Period, ContractsLanguageDunderMixin))
        self.assertIn("Period", repr(period))

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_equality(self):
        period = Period(months=2, date_failover=DateFailover.FIRST_VALID_DAY_BEFORE)
        another_period = Period(months=2, date_failover=DateFailover.FIRST_VALID_DAY_BEFORE)
        self.assertEqual(period, another_period)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_inequality(self):
        period = Period(months=2, date_failover=DateFailover.FIRST_VALID_DAY_BEFORE)
        another_period = Period(months=2, date_failover=DateFailover.FIRST_VALID_DAY_AFTER)
        self.assertNotEqual(period, another_period)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_days(self):
        period = Period(days=5)
        self.assertEqual(period.days, 5)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_days_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            Period(days="2")
        self.assertEqual(
            str(e.exception),
            "'Period.days' expected int if populated, got '2' of type str",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_days_raises_with_non_positive_integer(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Period(days=-2)
        self.assertEqual(
            str(e.exception),
            "Attribute Period.days must be greater than 0, got value -2.",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_months(self):
        period = Period(months=1, date_failover=DateFailover.FIRST_VALID_DAY_AFTER)
        self.assertEqual(period.months, 1)
        self.assertEqual(period.date_failover, DateFailover.FIRST_VALID_DAY_AFTER)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_months_raises_with_invalid_argument_type(self):
        with self.assertRaises(StrongTypingError) as e:
            Period(months="2")
        self.assertEqual(
            str(e.exception),
            "'Period.months' expected int if populated, got '2' of type str",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_months_raises_with_non_positive_integer(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Period(months=0, date_failover=DateFailover.FIRST_VALID_DAY_BEFORE)
        self.assertEqual(
            str(e.exception),
            "Attribute Period.months must be greater than 0, got value 0.",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_months_date_failover_defaults_when_not_populated(self):
        period = Period(months=2)
        self.assertEqual(period.months, 2)
        self.assertEqual(period.date_failover, DateFailover.FIRST_VALID_DAY_BEFORE)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_with_months_raises_with_invalid_argument_type_date_failover(self):
        with self.assertRaises(StrongTypingError) as e:
            Period(months=1, date_failover="abc")
        self.assertEqual(
            str(e.exception),
            "'Period.date_failover' expected DateFailover if populated, got 'abc' of type str",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_raises_when_both_days_and_date_failover_populated(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Period(days=1, date_failover=DateFailover.FIRST_VALID_DAY_BEFORE)
        self.assertEqual(
            str(e.exception),
            "Attribute Period.date_failover cannot be populated with Period.days.",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_raises_when_both_days_and_months_populated(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Period(days=1, months=1, date_failover=DateFailover.FIRST_VALID_DAY_BEFORE)
        self.assertEqual(
            str(e.exception),
            "Exactly one of Period.days or Period.months must be populated.",
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_period_raises_when_both_days_and_months_not_populated(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Period()
        self.assertEqual(
            str(e.exception),
            "Exactly one of Period.days or Period.months must be populated.",
        )
