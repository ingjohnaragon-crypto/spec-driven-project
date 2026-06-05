from datetime import datetime, timezone
from decimal import Decimal
from unittest import TestCase
from zoneinfo import ZoneInfo

from ..types import (
    
    Balance,
    BalanceCoordinate,
    BalanceDefaultDict,
    BalanceTimeseries,
    BalanceDiscreteTimeseries,
    CalendarEvent,
    CalendarTimeseries,
    DEFAULT_ADDRESS,
    DEFAULT_ASSET,
    FlagTimeseries,
    FlagValueTimeseries,
    ParameterTimeseries,
    ParameterValueTimeseries,
    Phase,
    TimeseriesItem,
)
from .....utils.exceptions import (
    InvalidSmartContractError,
)

from ..types.timeseries import DiscreteTimeseries

from ..types.timeseries import Timeseries

from .....utils.feature_flags import (
    skip_if_not_enabled,
    CALENDAR_FETCHERS,
    BALANCES_DISCRETE_INTERVAL_FETCHER,
)


class TestPublicCommonV400TimeseriesItem(TestCase):
    def test_timeseries_item_repr(self):
        item = TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "Value"))
        expected = (
            "TimeseriesItem(at_datetime=datetime.datetime(2020, 1, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value='Value')"
        )
        self.assertEqual(expected, repr(item))

    def test_timeseries_item_equality(self):
        item = TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "Value"))
        other_item = TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "Value"))
        self.assertEqual(item, other_item)

    def test_timeseries_item_unequal_at_datetime(self):
        item = TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "Value"))
        other_item = TimeseriesItem((datetime(1900, 1, 1, tzinfo=ZoneInfo("UTC")), "Value"))
        self.assertNotEqual(item, other_item)

    def test_timeseries_item_raises_with_native_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            TimeseriesItem((datetime(2020, 1, 1), "Value"))
        self.assertEqual(
            "'at_datetime' of TimeseriesItem is not timezone aware.",
            str(e.exception),
        )

    def test_timeseries_item_raises_with_non_utc_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("US/Pacific")), "Value"))
        self.assertEqual(
            "'at_datetime' of TimeseriesItem must have timezone UTC, currently US/Pacific.",
            str(e.exception),
        )

    def test_timeseries_item_raises_with_non_zoneinfo_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            TimeseriesItem((datetime.fromtimestamp(1, timezone.utc), "Value"))
        self.assertEqual(
            "'at_datetime' of TimeseriesItem must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )


class TestPublicCommonV400Timeseries(TestCase):
    test_timeseries = Timeseries([(datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "Value")])

    def test_timeseries_at_raises_with_native_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.test_timeseries.at(at_datetime=datetime(2020, 1, 15, 11, 20, 0))
        self.assertEqual(
            "'at_datetime' of Timeseries.at() is not timezone aware.",
            str(e.exception),
        )

    def test_timeseries_at_raises_with_non_utc_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.test_timeseries.at(
                at_datetime=datetime(2020, 1, 15, 11, 20, 0, tzinfo=ZoneInfo("US/Pacific"))
            )
        self.assertEqual(
            "'at_datetime' of Timeseries.at() must have timezone UTC, currently US/Pacific.",
            str(e.exception),
        )

    def test_timeseries_at_raises_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.test_timeseries.at(at_datetime=datetime.fromtimestamp(1, timezone.utc))
        self.assertEqual(
            "'at_datetime' of Timeseries.at() must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    def test_timeseries_before_raises_with_native_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.test_timeseries.before(at_datetime=datetime(2020, 1, 15, 11, 20, 0))
        self.assertEqual(
            "'at_datetime' of Timeseries.before() is not timezone aware.",
            str(e.exception),
        )

    def test_timeseries_before_raises_with_non_utc_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.test_timeseries.before(
                at_datetime=datetime(2020, 1, 15, 11, 20, 0, tzinfo=ZoneInfo("US/Pacific"))
            )
        self.assertEqual(
            "'at_datetime' of Timeseries.before() must have timezone UTC, currently US/Pacific.",
            str(e.exception),
        )

    def test_timeseries_before_raises_with_non_zoneinfo_timezone(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.test_timeseries.before(at_datetime=datetime.fromtimestamp(1, timezone.utc))
        self.assertEqual(
            "'at_datetime' of Timeseries.before() must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    def test_timeseries_raises_with_native_datetime_in_item(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Timeseries(
                [
                    (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), "Value1"),
                    (datetime(2020, 1, 1), "Value2"),
                ]
            )
        self.assertEqual(
            "'at_datetime' of TimeseriesItem is not timezone aware.",
            str(e.exception),
        )

    def test_timeseries_raises_with_non_utc_datetime_in_item(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Timeseries(
                [
                    (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), "Value1"),
                    (datetime(2020, 1, 1, tzinfo=ZoneInfo("US/Pacific")), "Value2"),
                ]
            )
        self.assertEqual(
            "'at_datetime' of TimeseriesItem must have timezone UTC, currently US/Pacific.",
            str(e.exception),
        )

    def test_timeseries_raises_with_non_zoneinfo_datetime_in_item(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            Timeseries(
                [
                    (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), "Value1"),
                    (datetime.fromtimestamp(1, timezone.utc), "Value2"),
                ]
            )
        self.assertEqual(
            "'at_datetime' of TimeseriesItem must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )


class TestPublicCommonV400BalanceTimeseries(TestCase):
    def test_balance_timeseries(self):
        key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_IN,
        )
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.99))})
        refund = BalanceDefaultDict(mapping={key_in: Balance(debit=Decimal(5.50))})
        balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund),
            ]
        )
        self.assertEqual(
            balances.at(at_datetime=datetime(2020, 1, 15, 11, 20, 0, tzinfo=ZoneInfo("UTC"))),
            purchase,
        )

    def test_balance_timeseries_repr(self):
        key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_IN,
        )
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.00))})
        refund = BalanceDefaultDict(mapping={key_in: Balance(debit=Decimal(5.50))})
        balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund),
            ]
        )
        expected = (
            "[TimeseriesItem("
            + "at_datetime=datetime.datetime(2020, 1, 15, 11, 19, tzinfo=zoneinfo.ZoneInfo(key='UTC')), "
            + "value={"
            + "BalanceCoordinate("
            + "account_address='DEFAULT', "
            + "asset='COMMERCIAL_BANK_MONEY', "
            + "denomination='GBP', "
            + "phase=Phase.PENDING_OUT): Balance(credit=Decimal('99'), debit=Decimal('0'), net=Decimal('0'))"
            + "}), "
            + "TimeseriesItem("
            + "at_datetime=datetime.datetime(2020, 1, 15, 12, 25, tzinfo=zoneinfo.ZoneInfo(key='UTC')), "
            + "value={"
            + "BalanceCoordinate("
            + "account_address='DEFAULT', "
            + "asset='COMMERCIAL_BANK_MONEY', "
            + "denomination='GBP', "
            + "phase=Phase.PENDING_IN): Balance(credit=Decimal('0'), debit=Decimal('5.5'), net=Decimal('0'))"
            + "})"
            + "]"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(balances))

    def test_balance_timeseries_equality(self):
        key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_IN,
        )
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.99))})
        refund = BalanceDefaultDict(mapping={key_in: Balance(debit=Decimal(5.50))})
        balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund),
            ]
        )

        other_key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        other_key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_IN,
        )
        other_purchase = BalanceDefaultDict(mapping={other_key_out: Balance(credit=Decimal(99.99))})
        other_refund = BalanceDefaultDict(mapping={other_key_in: Balance(debit=Decimal(5.50))})
        other_balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), other_purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), other_refund),
            ]
        )

        self.assertEqual(balances, other_balances)

    def test_balance_timeseries_unequal_balance(self):
        key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_IN,
        )
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.99))})
        refund = BalanceDefaultDict(mapping={key_in: Balance(debit=Decimal(5.50))})
        balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund),
            ]
        )

        other_key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        other_key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        other_purchase = BalanceDefaultDict(mapping={other_key_out: Balance(credit=Decimal(99.99))})
        other_refund = BalanceDefaultDict(mapping={other_key_in: Balance(debit=Decimal(5.50))})
        other_balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), other_purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), other_refund),
            ]
        )

        self.assertNotEqual(balances, other_balances)

    def test_balance_timeseries_return_missing_balance(self):
        balance_time = datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC"))
        purchase = (balance_time, Balance(credit=Decimal("99.99")))
        balances = BalanceTimeseries([purchase])
        self.assertEqual(balances.at(at_datetime=balance_time), purchase[1])
        self.assertEqual(
            balances.before(at_datetime=balance_time),
            Balance(credit=Decimal("0"), debit=Decimal("0"), net=Decimal("0")),
        )

    def test_balance_timeseries_return_on_empty(self):
        balances = BalanceTimeseries()
        self.assertEqual(
            balances.latest(), Balance(credit=Decimal("0"), debit=Decimal("0"), net=Decimal("0"))
        )

    def test_balance_default_dict_default_factory_happy_path(self):
        balance_default_dict = BalanceDefaultDict()
        valid_type_balance_key = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        self.assertEqual(balance_default_dict[valid_type_balance_key], Balance())

    def test_balance_defaultdict_bypass_type_checking_on_init(self):
        key = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        purchase = BalanceDefaultDict(mapping={key: "not_a_balance"}, _from_proto=True)
        self.assertEqual(purchase[key], "not_a_balance")

    def test_balance_timeseries_bypass_type_checking(self):
        key_out = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        key_in = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_IN,
        )
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.99))})
        refund = BalanceDefaultDict(mapping={key_in: Balance(debit=Decimal(5.50))})
        not_a_balance = "not_a_balance"
        BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund),
                (datetime(2020, 1, 15, 12, 31, 0, tzinfo=ZoneInfo("UTC")), not_a_balance),
            ],
        )

    def test_balance_timeseries_all_method(self):
        key_out = (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_OUT)
        key_in = (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN)
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.99))})
        refund = BalanceDefaultDict(mapping={key_in: Balance(debit=Decimal(5.50))})
        balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
                (datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund),
            ]
        )

        self.assertIsInstance(
            balances.all(),
            BalanceTimeseries,
            "BalanceTimeseries.all() must be of type BalanceTimeseries",
        )
        self.assertEqual(len(balances.all()), 2)
        self.assertEqual(
            balances.all()[0],
            TimeseriesItem((datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase)),
        )
        self.assertEqual(
            balances.all()[1],
            TimeseriesItem((datetime(2020, 1, 15, 12, 25, 0, tzinfo=ZoneInfo("UTC")), refund)),
        )

    def test_balance_timeseries_all_get_attributes(self):
        key_out = (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_OUT)
        purchase = BalanceDefaultDict(mapping={key_out: Balance(credit=Decimal(99.99))})
        balances = BalanceTimeseries(
            [
                (datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC")), purchase),
            ]
        )
        self.assertEqual(len(balances.all()), 1)

        timeseries_item = balances.all()[0]
        self.assertEqual(
            timeseries_item.at_datetime, datetime(2020, 1, 15, 11, 19, 0, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(timeseries_item.value, purchase)


class TestPublicCommonV400FlagTimeseries(TestCase):
    def test_flag_timeseries_empty(self):
        flags = FlagTimeseries()
        self.assertFalse(flags.at(at_datetime=datetime(2020, 3, 25, tzinfo=ZoneInfo("UTC"))))

    def test_flag_timeseries(self):
        flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertTrue(flags.at(at_datetime=datetime(2020, 3, 25, 13, 45, tzinfo=ZoneInfo("UTC"))))
        self.assertFalse(
            flags.at(at_datetime=datetime(2020, 3, 25, 23, 15, tzinfo=ZoneInfo("UTC")))
        )

    def test_flag_timeseries_repr(self):
        flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        expected = (
            "[TimeseriesItem(at_datetime=datetime.datetime(2020, 3, 25, 10, 30, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value=True), "
            + "TimeseriesItem(at_datetime=datetime.datetime(2020, 3, 25, 22, 30, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value=False)]"
        )
        self.assertEqual(expected, repr(flags))

    def test_flag_timeseries_equality(self):
        flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        other_flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertEqual(flags, other_flags)

    def test_flag_timeseries_unequal_datetime(self):
        flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        other_flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2023, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertNotEqual(flags, other_flags)

    def test_flag_timeseries_all_method(self):
        flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertIsInstance(
            flags.all(), FlagTimeseries, "FlagTimeseries.all() must be of type FlagTimeseries"
        )
        self.assertEqual(len(flags.all()), 2)
        self.assertEqual(
            flags.all()[0],
            TimeseriesItem((datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True)),
        )
        self.assertEqual(
            flags.all()[1],
            TimeseriesItem((datetime(2020, 3, 25, 22, 30, tzinfo=ZoneInfo("UTC")), False)),
        )

    def test_flag_timeseries_all_get_attributes(self):
        flags = FlagTimeseries(
            [
                (datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC")), True),
            ]
        )
        self.assertEqual(len(flags.all()), 1)

        timeseries_item = flags.all()[0]
        self.assertEqual(
            timeseries_item.at_datetime, datetime(2020, 3, 25, 10, 30, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(timeseries_item.value, True)


class TestPublicCommonV400FlagValueTimeseries(TestCase):
    def test_flag_value_timeseries(self):
        flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertEqual(
            True,
            flags_value_timeseries.at(at_datetime=datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))),
        )
        self.assertEqual(
            False,
            flags_value_timeseries.at(at_datetime=datetime(2020, 2, 10, tzinfo=ZoneInfo("UTC"))),
        )

    def test_flag_value_timeseries_repr(self):
        flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        expected = (
            "[TimeseriesItem(at_datetime=datetime.datetime(2020, 1, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value=True), "
            + "TimeseriesItem(at_datetime=datetime.datetime(2020, 2, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value=False)]"
        )
        self.assertEqual(expected, repr(flags_value_timeseries))

    def test_flag_value_timeseries_equality(self):
        flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        other_flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertEqual(flags_value_timeseries, other_flags_value_timeseries)

    def test_flag_value_timeseries_unequal_datetime(self):
        flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        other_flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2023, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertNotEqual(flags_value_timeseries, other_flags_value_timeseries)

    def test_flag_value_timeseries_all_method(self):
        flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False),
            ]
        )
        self.assertIsInstance(
            flags_value_timeseries.all(),
            FlagValueTimeseries,
            "FlagValueTimeseries.all() must be of type FlagValueTimeseries",
        )
        self.assertEqual(len(flags_value_timeseries.all()), 2)
        self.assertEqual(
            flags_value_timeseries.all()[0],
            TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True)),
        )
        self.assertEqual(
            flags_value_timeseries.all()[1],
            TimeseriesItem((datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), False)),
        )

    def test_flag_value_timeseries_all_get_attributes(self):
        flags_value_timeseries = FlagValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), True),
            ]
        )
        self.assertEqual(len(flags_value_timeseries.all()), 1)

        timeseries_item = flags_value_timeseries.all()[0]
        self.assertEqual(timeseries_item.at_datetime, datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(timeseries_item.value, True)

    def test_flag_value_timeseries_empty_returns_false(self):
        flags_value_timeseries = FlagValueTimeseries()
        some_datetime = datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))
        self.assertFalse(flags_value_timeseries.at(at_datetime=some_datetime))
        self.assertFalse(flags_value_timeseries.before(at_datetime=some_datetime))
        self.assertFalse(flags_value_timeseries.latest())

    def test_flag_value_timeseries_at_method(self):
        flag_value_timeseries = FlagValueTimeseries(
            [
                (datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
                (datetime(day=10, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), False),
                (datetime(day=20, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
            ]
        )
        self.assertTrue(
            flag_value_timeseries.at(
                at_datetime=datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC"))
            )
        )
        self.assertFalse(
            flag_value_timeseries.at(
                at_datetime=datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")),
                inclusive=False,
            )
        ),
        self.assertTrue(
            flag_value_timeseries.at(
                at_datetime=datetime(day=9, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")),
            )
        ),
        self.assertTrue(
            flag_value_timeseries.at(
                at_datetime=datetime(day=9, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")),
                inclusive=False,
            )
        ),
        self.assertFalse(
            flag_value_timeseries.at(
                at_datetime=datetime(day=10, month=1, year=2020, tzinfo=ZoneInfo(key="UTC"))
            )
        )
        self.assertFalse(
            flag_value_timeseries.at(
                at_datetime=datetime(day=15, month=1, year=2020, tzinfo=ZoneInfo(key="UTC"))
            )
        )
        self.assertTrue(
            flag_value_timeseries.at(
                at_datetime=datetime(day=20, month=1, year=3000, tzinfo=ZoneInfo(key="UTC"))
            )
        )

    def test_flag_value_timeseries_before_method(self):
        flag_value_timeseries = FlagValueTimeseries(
            [
                (datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
                (datetime(day=10, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), False),
                (datetime(day=20, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
            ]
        )
        self.assertFalse(
            flag_value_timeseries.before(
                at_datetime=datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC"))
            )
        )
        self.assertTrue(
            flag_value_timeseries.before(
                at_datetime=datetime(day=9, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")),
            )
        ),
        self.assertFalse(
            flag_value_timeseries.before(
                at_datetime=datetime(day=15, month=1, year=2020, tzinfo=ZoneInfo(key="UTC"))
            )
        )
        self.assertTrue(
            flag_value_timeseries.before(
                at_datetime=datetime(day=20, month=1, year=3000, tzinfo=ZoneInfo(key="UTC"))
            )
        ),
        self.assertTrue(
            flag_value_timeseries.before(
                at_datetime=datetime(day=26, month=1, year=3000, tzinfo=ZoneInfo(key="UTC"))
            )
        )

    def test_flag_value_timeseries_latest_method(self):
        flag_value_timeseries = FlagValueTimeseries(
            [
                (datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
                (datetime(day=10, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), False),
                (datetime(day=20, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
            ]
        )

        self.assertTrue(flag_value_timeseries.latest())

    def test_flag_value_timeseries_from_proto_attribute_true(self):
        flag_value_timeseries = FlagValueTimeseries(
            [
                (datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
            ],
            _from_proto=True,
        )
        self.assertTrue(flag_value_timeseries._from_proto)  # noqa: SLF001

    def test_flag_value_timeseries_from_proto_attribute_false(self):
        flag_value_timeseries = FlagValueTimeseries(
            [
                (datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
            ],
            _from_proto=False,
        )
        self.assertFalse(flag_value_timeseries._from_proto)  # noqa: SLF001

    def test_flag_value_timeseries_from_proto_attribute_default_is_false(self):
        flag_value_timeseries = FlagValueTimeseries(
            [
                (datetime(day=1, month=1, year=2020, tzinfo=ZoneInfo(key="UTC")), True),
            ]
        )
        self.assertFalse(flag_value_timeseries._from_proto)  # noqa: SLF001


class TestPublicCommonV400ParameterTimeseries(TestCase):
    def test_parameter_timeseries(self):
        parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertEqual(
            "First value", parameters.at(at_datetime=datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC")))
        )
        self.assertEqual(
            "Second value", parameters.at(at_datetime=datetime(2020, 2, 10, tzinfo=ZoneInfo("UTC")))
        )

    def test_parameter_timeseries_repr(self):
        parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        expected = (
            "[TimeseriesItem(at_datetime=datetime.datetime(2020, 1, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value='First value'), "
            + "TimeseriesItem(at_datetime=datetime.datetime(2020, 2, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value='Second value')]"
        )
        self.assertEqual(expected, repr(parameters))

    def test_parameter_timeseries_equality(self):
        parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        other_parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertEqual(parameters, other_parameters)

    def test_parameter_timeseries_unequal_datetime(self):
        parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        other_parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2023, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertNotEqual(parameters, other_parameters)

    def test_parameter_timeseries_all_method(self):
        parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertIsInstance(
            parameters.all(),
            ParameterTimeseries,
            "ParameterTimeseries.all() must be of type ParameterTimeseries",
        )
        self.assertEqual(len(parameters.all()), 2)
        self.assertEqual(
            parameters.all()[0],
            TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value")),
        )
        self.assertEqual(
            parameters.all()[1],
            TimeseriesItem((datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value")),
        )

    def test_parameter_timeseries_all_get_attributes(self):
        parameters = ParameterTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
            ]
        )
        self.assertEqual(len(parameters.all()), 1)

        timeseries_item = parameters.all()[0]
        self.assertEqual(timeseries_item.at_datetime, datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(timeseries_item.value, "First value")

    def test_parameter_timeseries_empty_returns_none(self):
        parameters = ParameterTimeseries()
        some_datetime = datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))
        self.assertIsNone(parameters.at(at_datetime=some_datetime))
        self.assertIsNone(parameters.before(at_datetime=some_datetime))
        self.assertIsNone(parameters.latest())


class TestPublicCommonV400ParameterValueTimeseries(TestCase):
    def test_parameter_value_timeseries(self):
        parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertEqual(
            "First value", parameters.at(at_datetime=datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC")))
        )
        self.assertEqual(
            "Second value", parameters.at(at_datetime=datetime(2020, 2, 10, tzinfo=ZoneInfo("UTC")))
        )

    def test_parameter_value_timeseries_repr(self):
        parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        expected = (
            "[TimeseriesItem(at_datetime=datetime.datetime(2020, 1, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value='First value'), "
            + "TimeseriesItem(at_datetime=datetime.datetime(2020, 2, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), value='Second value')]"
        )
        self.assertEqual(expected, repr(parameters))

    def test_parameter_value_timeseries_equality(self):
        parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        other_parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertEqual(parameters, other_parameters)

    def test_parameter_value_timeseries_unequal_datetime(self):
        parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        other_parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2023, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertNotEqual(parameters, other_parameters)

    def test_parameter_value_timeseries_all_method(self):
        parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
                (datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value"),
            ]
        )
        self.assertIsInstance(
            parameters.all(),
            ParameterValueTimeseries,
            "ParameterValueTimeseries.all() must be of type ParameterValueTimeseries",
        )
        self.assertEqual(len(parameters.all()), 2)
        self.assertEqual(
            parameters.all()[0],
            TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value")),
        )
        self.assertEqual(
            parameters.all()[1],
            TimeseriesItem((datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), "Second value")),
        )

    def test_parameter_value_timeseries_all_get_attributes(self):
        parameters = ParameterValueTimeseries(
            [
                (datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), "First value"),
            ]
        )
        self.assertEqual(len(parameters.all()), 1)

        timeseries_item = parameters.all()[0]
        self.assertEqual(timeseries_item.at_datetime, datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(timeseries_item.value, "First value")

    def test_parameter_value_timeseries_empty_returns_none(self):
        parameters = ParameterValueTimeseries()
        some_datetime = datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))
        self.assertIsNone(parameters.at(at_datetime=some_datetime))
        self.assertIsNone(parameters.before(at_datetime=some_datetime))
        self.assertIsNone(parameters.latest())


class TestPublicCommonV400CalendarTimeseries(TestCase):
    calendar_event_1 = CalendarEvent(
        id="id",
        calendar_id="CALENDAR_1",
        start_datetime=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
        end_datetime=datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
    )
    calendar_event_2 = CalendarEvent(
        id="id",
        calendar_id="CALENDAR_1",
        start_datetime=datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
        end_datetime=datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
    )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries(self):
        calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1],
                ),
                (
                    datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, self.calendar_event_2],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [],
                ),
            ],
        )
        self.assertEqual(
            [self.calendar_event_1],
            calendars.at(at_datetime=datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))),
        )
        self.assertEqual(
            [self.calendar_event_1, self.calendar_event_2],
            calendars.at(at_datetime=datetime(2020, 1, 20, tzinfo=ZoneInfo("UTC"))),
        )
        self.assertEqual([], calendars.at(at_datetime=datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC"))))
        self.assertEqual(
            [],
            calendars.at(at_datetime=datetime(2020, 2, 2, tzinfo=ZoneInfo("UTC")), inclusive=False),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries_base_class(self):
        self.assertTrue(issubclass(CalendarTimeseries, Timeseries))

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries_equality(self):
        calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1],
                ),
                (
                    datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, self.calendar_event_2],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [],
                ),
            ],
        )
        other_calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1],
                ),
                (
                    datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, self.calendar_event_2],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [],
                ),
            ],
        )
        self.assertEqual(calendars, other_calendars)

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries_unequal_datetime(self):
        different_event = CalendarEvent(
            id="id",
            calendar_id="CALENDAR_1",
            start_datetime=datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2020, 2, 10, tzinfo=ZoneInfo("UTC")),
        )
        calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1],
                ),
                (
                    datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, self.calendar_event_2],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [],
                ),
            ],
        )
        other_calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, different_event],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [different_event],
                ),
                (
                    datetime(2020, 2, 10, tzinfo=ZoneInfo("UTC")),
                    [different_event],
                ),
            ],
        )
        self.assertNotEqual(calendars, other_calendars)

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries_all_method(self):
        calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1],
                ),
                (
                    datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, self.calendar_event_2],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [],
                ),
            ],
        )
        self.assertIsInstance(
            calendars.all(),
            CalendarTimeseries,
            "CalendarTimeseries.all() must be of type CalendarTimeseries",
        )
        self.assertEqual(len(calendars.all()), 3)
        self.assertEqual(
            calendars.all()[0],
            TimeseriesItem((datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")), [self.calendar_event_1])),
        )
        self.assertEqual(
            calendars.all()[1],
            TimeseriesItem(
                (
                    datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1, self.calendar_event_2],
                )
            ),
        )
        self.assertEqual(
            calendars.all()[2],
            TimeseriesItem((datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")), [])),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries_all_get_attributes(self):
        calendars = CalendarTimeseries(
            [
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    [self.calendar_event_1],
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    [],
                ),
            ],
        )
        self.assertEqual(len(calendars.all()), 2)

        timeseries_item = calendars.all()[0]
        self.assertEqual(timeseries_item.at_datetime, datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(timeseries_item.value, [self.calendar_event_1])

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_calendar_timeseries_empty_returns_empty_list(self):
        # Note: an empty list should never happen in real Vault as we would expect at least one
        # timeseries entry for any valid calendar_id for the start of the interval (which could have
        # no calendar events)
        calendars = CalendarTimeseries()
        some_datetime = datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))
        self.assertEqual([], calendars.at(at_datetime=some_datetime))
        self.assertEqual([], calendars.before(at_datetime=some_datetime))
        self.assertEqual([], calendars.latest())


class TestPublicCommonV400CalendarTimeseriesHelpers(TestCase):
    def setUp(self):
        self.T0 = datetime(2000, 1, 1, 0, tzinfo=ZoneInfo("UTC"))
        self.T1 = datetime(2000, 1, 1, 1, tzinfo=ZoneInfo("UTC"))
        self.T2 = datetime(2000, 1, 1, 2, tzinfo=ZoneInfo("UTC"))
        self.T3 = datetime(2000, 1, 1, 3, tzinfo=ZoneInfo("UTC"))
        self.T4 = datetime(2000, 1, 1, 4, tzinfo=ZoneInfo("UTC"))
        self.T5 = datetime(2000, 1, 1, 5, tzinfo=ZoneInfo("UTC"))
        self.T6 = datetime(2000, 1, 1, 6, tzinfo=ZoneInfo("UTC"))
        self.T7 = datetime(2000, 1, 1, 7, tzinfo=ZoneInfo("UTC"))
        self.T8 = datetime(2000, 1, 1, 8, tzinfo=ZoneInfo("UTC"))

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_no_calendar_events(self):
        """
        Time        <--0------1------2-->
        Interval        |------------|

        Output:
        T0, []
        """
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [],
            interval_start=self.T0,
            interval_end=self.T2,
        )
        # no calendar events returns timeseries with empty list for start datetime
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [(self.T0, [])],
            ),
        )
        self.assertEqual(timeseries.at(at_datetime=self.T1), [])

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_single_calendar_event(self):
        """
        Time        <--1------2-->
        Interval       |------|
        CE1            [------)

        Output:
        T1, [CE1]
        T2, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T2,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1], self.T1, self.T2
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE1]),
                    (self.T2, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_two_calendar_events(self):
        """
        Time        <--1------2------3-->
        Interval       |-------------|
        CE1            [------)
        CE2                   [------)

        Output:
        T1, [CE1]
        T2, [CE2]
        T3, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T2,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T2,
            end_datetime=self.T3,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2], self.T1, self.T3
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE1]),
                    (self.T2, [CE2]),
                    (self.T3, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_two_calendar_events_overlapping(self):
        """
        Time        <--1------2------3------4-->
        Interval       |--------------------|
        CE1            [-------------)
        CE2                   [-------------)

        Output:
        T1, [CE1]
        T2, [CE1, CE2]
        T3, [CE2]
        T4, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T2,
            end_datetime=self.T4,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2], CE1.start_datetime, self.T4
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE1]),
                    (self.T2, [CE1, CE2]),
                    (self.T3, [CE2]),
                    (self.T4, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_three_calendar_events_multiple_overlaps(self):
        """
        Time        <--1------2------3------4------5------6-->
        Interval       |----------------------------------|
        CE1            [-------------)
        CE2                   [-------------)
        CE3                                        [------)
        CE4                                       [------)

        Output:
        T1, [CE1]
        T2, [CE1, CE2]
        T3, [CE2]
        T4, []
        T5, [CE3, CE4]
        T6, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T2,
            end_datetime=self.T4,
        )
        CE3 = CalendarEvent(
            id="CE3",
            calendar_id="calendar_id",
            start_datetime=self.T5,
            end_datetime=self.T6,
        )
        CE4 = CalendarEvent(
            id="CE4",
            calendar_id="calendar_id",
            start_datetime=self.T5,
            end_datetime=self.T6,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2, CE3, CE4],
            self.T1,
            self.T6,
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE1]),
                    (self.T2, [CE1, CE2]),
                    (self.T3, [CE2]),
                    (self.T4, []),
                    (self.T5, [CE3, CE4]),
                    (self.T6, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_single_calendar_event_interval_start_before_event_start(
        self,
    ):
        """
        Time        <--0------1------2-->
        Interval       |-------------|
        CE1                   [------)

        Output:
        T0, []
        T1, [CE1]
        T2, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T2,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1], interval_start=self.T0, interval_end=self.T2
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T0, []),
                    (self.T1, [CE1]),
                    (self.T2, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_single_event_with_interval_start_equal_to_event_start(
        self,
    ):
        """
        Time        <--0------1-->
        Interval       |------|
        CE1            [------)

        Output:
        T0, [CE1]
        T1, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T0,
            end_datetime=self.T1,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1], interval_start=self.T0, interval_end=self.T1
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T0, [CE1]),
                    (self.T1, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_three_events_and_interval_start_with_same_start_and_end(
        self,
    ):
        """
        Time        <--0------1-->
        Interval       |------|
        CE1            [------)
        CE2            [------)
        CE3            [------)

        Output:
        T0, [CE1, CE2, CE3]
        T1, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T0,
            end_datetime=self.T1,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T0,
            end_datetime=self.T1,
        )
        CE3 = CalendarEvent(
            id="CE3",
            calendar_id="calendar_id",
            start_datetime=self.T0,
            end_datetime=self.T1,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE2, CE1, CE3], interval_start=self.T0, interval_end=self.T1
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T0, [CE1, CE2, CE3]),
                    (self.T1, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_one_event_with_interval_start_after_event_start(self):
        """
        Expect that first datetime key of the timeseries is set to interval start.

        Time        <--1------2------3-->
        Interval              |------|
        CE1            [-------------)

        Output:
        T0, [CE1]
        T1, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1], interval_start=self.T2, interval_end=self.T3
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T2, [CE1]),
                    (self.T3, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_one_event_with_interval_end_before_event_end(self):
        """
        Time        <--1------2------3-->
        Interval       |------|
        CE1            [-------------)

        Output:
        T1, [CE1]
        T2, [CE1]
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1], interval_start=self.T1, interval_end=self.T2
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE1]),
                    (self.T2, [CE1]),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_one_event_with_interval_end_after_event_end(self):
        """
        Time        <--1------2------3-->
        Interval       |-------------|
        CE1            [------)

        Output:
        T1, [CE1]
        T2, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T2,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1], interval_start=self.T1, interval_end=self.T3
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE1]),
                    (self.T2, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_two_events_with_interval_start_after_event_start(self):
        """
        Expect that first datetime key of the timeseries is set to interval start.

        Time        <--1------2------3------4-->
        Interval                     |------|
        CE1            [--------------------)
        CE2                   [-------------)

        Output:
        T0, [CE1, CE2]
        T1, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T4,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T2,
            end_datetime=self.T4,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2], interval_start=self.T3, interval_end=self.T4
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T3, [CE1, CE2]),
                    (self.T4, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_two_events_with_interval_end_before_event_end(self):
        """
        Expect that last datetime key of the timeseries is set to interval end.

        Time        <--1------2------3------4-->
        Interval       |------|
        CE1            [--------------------)
        CE2            [-------------)

        Output (ordered by end_datetime):
        T1, [CE2, CE1]
        T2, [CE2, CE1]
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T4,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2], interval_start=self.T1, interval_end=self.T2
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE2, CE1]),
                    (self.T2, [CE2, CE1]),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_two_events_with_interval_end_after_event_end(self):
        """
        Expect that last datetime key of the timeseries is set to interval end.

        Time        <--1------2------3------4-->
        Interval       |--------------------|
        CE1            [-------------)
        CE2            [------)

        Output (ordered by end_datetime):
        T1, [CE2, CE1]
        T2, [CE1]
        T3, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T2,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2], interval_start=self.T1, interval_end=self.T4
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T1, [CE2, CE1]),
                    (self.T2, [CE1]),
                    (self.T3, []),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_from_calendar_events_two_events_with_interval_start_and_end_outside_range(
        self,
    ):
        """
        Time        <--1------2------3------4-->
        Interval       |--------------------|
        CE1            [--------------------)
        CE2            [-------------)

        Output (ordered by end_datetime):
        T2, [CE2, CE1]
        T3, [CE1]
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T4,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T3,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2],
            interval_start=self.T2,
            interval_end=self.T3,
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T2, [CE2, CE1]),
                    (self.T3, [CE1]),
                ],
            ),
        )

    @skip_if_not_enabled(CALENDAR_FETCHERS)
    def test_timeseries_complex_example(
        self,
    ):
        """
        Time        <--0------1------2------3------4------5------6------7------8-->
        Interval       |-------------------------------------------------------|
        CE1                   [--------------------)
        CE2                          [--------------------)
        CE3                                 [-------------)
        CE4                                               [--------------------)
        CE5                                               [-------------)

        Output (ordered by end_datetime):
        T0, []
        T1, [CE1]
        T2, [CE1, CE2]
        T3, [CE1, CE2, CE3]
        T4, [CE2, CE3]
        T5, [CE5, CE4]
        T7, [CE4]
        T8, []
        """
        CE1 = CalendarEvent(
            id="CE1",
            calendar_id="calendar_id",
            start_datetime=self.T1,
            end_datetime=self.T4,
        )
        CE2 = CalendarEvent(
            id="CE2",
            calendar_id="calendar_id",
            start_datetime=self.T2,
            end_datetime=self.T5,
        )
        CE3 = CalendarEvent(
            id="CE3",
            calendar_id="calendar_id",
            start_datetime=self.T3,
            end_datetime=self.T5,
        )
        CE4 = CalendarEvent(
            id="CE4",
            calendar_id="calendar_id",
            start_datetime=self.T5,
            end_datetime=self.T8,
        )
        CE5 = CalendarEvent(
            id="CE5",
            calendar_id="calendar_id",
            start_datetime=self.T5,
            end_datetime=self.T7,
        )
        timeseries = CalendarTimeseries._from_calendar_events(  # noqa: SLF001
            [CE1, CE2, CE3, CE4, CE5],
            interval_start=self.T0,
            interval_end=self.T8,
        )
        self.assertEqual(
            timeseries,
            CalendarTimeseries(
                [
                    (self.T0, []),
                    (self.T1, [CE1]),
                    (self.T2, [CE1, CE2]),
                    (self.T3, [CE1, CE2, CE3]),
                    (self.T4, [CE2, CE3]),
                    (self.T5, [CE5, CE4]),
                    (self.T7, [CE4]),
                    (self.T8, []),
                ],
            ),
        )


class TestPublicCommonV400DiscreteTimeseries(TestCase):
    empty_iterable: list[tuple[datetime, str]] = []
    empty_discrete_timeseries = DiscreteTimeseries(iterable=empty_iterable)

    datetime_1 = datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC"))
    datetime_2 = datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC"))
    datetime_3 = datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC"))
    datetime_4 = datetime(2020, 4, 1, tzinfo=ZoneInfo("UTC"))
    discrete_timeseries = DiscreteTimeseries(
        iterable=[
            (datetime_1, "value_1"),
            (datetime_2, "value_2"),
            (datetime_3, "value_3"),
            (datetime_4, "value_4"),
        ]
    )

    def test_discrete_timeseries_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            DiscreteTimeseries(iterable=[(datetime(2020, 1, 15), "value_1")])
        self.assertEqual(str(e.exception), "'at_datetime' of TimeseriesItem is not timezone aware.")

    def test_discrete_timeseries_get_when_datetime_exists_in_timeseries(self):
        expected_result = TimeseriesItem(item=(self.datetime_2, "value_2"))
        actual_result = self.discrete_timeseries.get(at_datetime=self.datetime_2)
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_get_when_datetime_not_in_timeseries(self):
        result = self.discrete_timeseries.get(
            at_datetime=datetime(2020, 2, 10, tzinfo=ZoneInfo("UTC"))
        )
        self.assertIsNone(result)

    def test_discrete_timeseries_get_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.discrete_timeseries.get(at_datetime=datetime(2020, 2, 10))
        self.assertEqual(
            str(e.exception), "'at_datetime' of DiscreteTimeseries.get() is not timezone aware."
        )

    def test_discrete_timeseries_before_no_previous_entry(self):
        result = self.discrete_timeseries.before(at_datetime=self.datetime_1)
        self.assertIsNone(result)

    def test_discrete_timeseries_before_returns_previous_entry_datetime_not_in_timeseries(self):
        expected_result = TimeseriesItem(item=(self.datetime_1, "value_1"))
        actual_result = self.discrete_timeseries.before(
            at_datetime=datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_before_returns_previous_entry_datetime_in_timeseries(self):
        expected_result = TimeseriesItem(item=(self.datetime_1, "value_1"))
        actual_result = self.discrete_timeseries.before(at_datetime=self.datetime_2)
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_before_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.discrete_timeseries.before(at_datetime=datetime(2020, 2, 10))
        self.assertEqual(
            str(e.exception), "'at_datetime' of DiscreteTimeseries.before() is not timezone aware."
        )

    def test_discrete_timeseries_after_no_next_entry(self):
        result = self.discrete_timeseries.after(at_datetime=self.datetime_4)
        self.assertIsNone(result)

    def test_discrete_timeseries_after_returns_next_entry_datetime_not_in_timeseries(self):
        expected_result = TimeseriesItem(item=(self.datetime_2, "value_2"))
        actual_result = self.discrete_timeseries.after(
            at_datetime=datetime(2020, 1, 10, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_after_returns_next_entry_datetime_in_timeseries(self):
        expected_result = TimeseriesItem(item=(self.datetime_3, "value_3"))
        actual_result = self.discrete_timeseries.after(at_datetime=self.datetime_2)
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_after_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.discrete_timeseries.after(at_datetime=datetime(2020, 2, 10))
        self.assertEqual(
            str(e.exception), "'at_datetime' of DiscreteTimeseries.after() is not timezone aware."
        )

    def test_discrete_timeseries_latest_returns_last_item(self):
        expected_result = TimeseriesItem(item=(self.datetime_4, "value_4"))
        actual_result = self.discrete_timeseries.latest()
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_latest_returns_none_with_empty_timeseries(self):
        result = self.empty_discrete_timeseries.latest()
        self.assertIsNone(result)

    def test_discrete_timeseries_all_returns_list_of_timeseries_items(self):
        expected_result = [
            TimeseriesItem(item=(self.datetime_1, "value_1")),
            TimeseriesItem(item=(self.datetime_2, "value_2")),
            TimeseriesItem(item=(self.datetime_3, "value_3")),
            TimeseriesItem(item=(self.datetime_4, "value_4")),
        ]
        actual_result = self.discrete_timeseries.all()
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_all_returns_empty_list_for_empty_timeseries(self):
        expected_result = []
        actual_result = self.empty_discrete_timeseries.all()
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_between_default_inclusivity(self):
        expected_result = DiscreteTimeseries(
            iterable=[
                (self.datetime_2, "value_2"),
                (self.datetime_3, "value_3"),
            ]
        )
        actual_result = self.discrete_timeseries.between(
            start_datetime=self.datetime_2, end_datetime=self.datetime_3
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_between_inclusive_start_exclusive_end(self):
        expected_result = DiscreteTimeseries(
            iterable=[
                (self.datetime_1, "value_1"),
                (self.datetime_2, "value_2"),
                (self.datetime_3, "value_3"),
            ]
        )
        actual_result = self.discrete_timeseries.between(
            start_datetime=self.datetime_1,
            end_datetime=self.datetime_4,
            inclusive_end_datetime=False,
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_between_exclusive_start_inclusive_end(self):
        expected_result = DiscreteTimeseries(
            iterable=[
                (self.datetime_2, "value_2"),
                (self.datetime_3, "value_3"),
                (self.datetime_4, "value_4"),
            ]
        )
        actual_result = self.discrete_timeseries.between(
            start_datetime=self.datetime_1,
            end_datetime=self.datetime_4,
            inclusive_start_datetime=False,
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_between_exclusive_start_exclusive_end(self):
        expected_result = DiscreteTimeseries(
            iterable=[
                (self.datetime_2, "value_2"),
                (self.datetime_3, "value_3"),
            ]
        )
        actual_result = self.discrete_timeseries.between(
            start_datetime=self.datetime_1,
            end_datetime=self.datetime_4,
            inclusive_start_datetime=False,
            inclusive_end_datetime=False,
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_between_empty_timeseries(self):
        expected_result = DiscreteTimeseries(iterable=self.empty_iterable)
        actual_result = self.empty_discrete_timeseries.between(
            start_datetime=self.datetime_2, end_datetime=self.datetime_3
        )
        self.assertEqual(expected_result, actual_result)

    def test_discrete_timeseries_between_raises_with_naive_start_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.discrete_timeseries.between(
                start_datetime=datetime(2020, 2, 10), end_datetime=self.datetime_4
            )
        self.assertEqual(
            str(e.exception),
            "'start_datetime' of DiscreteTimeseries.between() is not timezone aware.",
        )

    def test_discrete_timeseries_between_raises_with_naive_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            self.discrete_timeseries.between(
                start_datetime=self.datetime_1, end_datetime=datetime(2020, 2, 10)
            )
        self.assertEqual(
            str(e.exception),
            "'end_datetime' of DiscreteTimeseries.between() is not timezone aware.",
        )





class TestPublicCommonV400BalanceDiscreteTimeseries(TestCase):
    datetime_1 = datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC"))
    datetime_2 = datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC"))
    datetime_3 = datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC"))
    balance_discrete_timeseries = BalanceDiscreteTimeseries(
        iterable=[
            (datetime_1, Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0))),
            (datetime_2, Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))),
            (datetime_3, Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0))),
        ]
    )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_inherits_from_discrete_timeseries(self):
        """To cover the edge cases around the get, before, after and latest methods."""
        self.assertTrue(issubclass(BalanceDiscreteTimeseries, DiscreteTimeseries))

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_timeseries_raises_with_naive_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as e:
            BalanceDiscreteTimeseries(iterable=[(datetime(2020, 1, 15), Balance(1, 1, 0))])
        self.assertEqual(str(e.exception), "'at_datetime' of TimeseriesItem is not timezone aware.")

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries(self):
        self.assertEqual(3, len(self.balance_discrete_timeseries))
        self.assertEqual(
            self.balance_discrete_timeseries[0],
            TimeseriesItem(
                item=(
                    self.datetime_1,
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                )
            ),
        )
        self.assertEqual(
            self.balance_discrete_timeseries[1],
            TimeseriesItem(
                item=(
                    self.datetime_2,
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                )
            ),
        )
        self.assertEqual(
            self.balance_discrete_timeseries[2],
            TimeseriesItem(
                item=(
                    self.datetime_3,
                    Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
                )
            ),
        )

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_get(self):
        b2 = self.balance_discrete_timeseries.get(at_datetime=self.datetime_2)
        expected = TimeseriesItem(
            item=(self.datetime_2, Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)))
        )
        self.assertEqual(expected, b2)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_get_datetime_that_does_not_exist(self):
        dt = datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC"))
        b_none = self.balance_discrete_timeseries.get(at_datetime=dt)
        self.assertIsNone(b_none)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_latest(self):
        b_latest = self.balance_discrete_timeseries.latest()
        expected = TimeseriesItem(
            item=(
                self.datetime_3,
                Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
            )
        )
        self.assertEqual(expected, b_latest)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_before(self):
        b_before = self.balance_discrete_timeseries.before(at_datetime=self.datetime_2)
        expected = TimeseriesItem(
            item=(
                self.datetime_1,
                Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
            ),
        )
        self.assertEqual(expected, b_before)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_before_first_datetime(self):
        dt = datetime(2000, 1, 1, tzinfo=ZoneInfo("UTC"))
        b_none = self.balance_discrete_timeseries.before(at_datetime=dt)
        self.assertIsNone(b_none)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_after(self):
        b_after = self.balance_discrete_timeseries.after(at_datetime=self.datetime_2)
        expected = TimeseriesItem(
            item=(
                self.datetime_3,
                Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
            ),
        )
        self.assertEqual(expected, b_after)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_equality(self):
        balance_discrete_timeseries_1 = BalanceDiscreteTimeseries(
            iterable=[
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                ),
                (
                    datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
                ),
            ]
        )
        balance_discrete_timeseries_2 = BalanceDiscreteTimeseries(
            iterable=[
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                ),
                (
                    datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
                ),
            ]
        )
        self.assertEqual(balance_discrete_timeseries_1, balance_discrete_timeseries_2)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_unequal_datetimes(self):
        balance_discrete_timeseries_1 = BalanceDiscreteTimeseries(
            iterable=[
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                ),
                (
                    datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),  # datetime T2
                    Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
                ),
            ]
        )
        balance_discrete_timeseries_2 = BalanceDiscreteTimeseries(
            iterable=[
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                ),
                (
                    datetime(2020, 4, 1, tzinfo=ZoneInfo("UTC")),  # different datetime T4
                    Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
                ),
            ]
        )
        self.assertNotEqual(balance_discrete_timeseries_1, balance_discrete_timeseries_2)

    @skip_if_not_enabled(BALANCES_DISCRETE_INTERVAL_FETCHER)
    def test_balance_discrete_timeseries_unequal_balances(self):
        balance_discrete_timeseries_1 = BalanceDiscreteTimeseries(
            iterable=[
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                ),
                (
                    datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),  # datetime T2
                    Balance(credit=Decimal(30), debit=Decimal(30), net=Decimal(0)),
                ),
            ]
        )
        balance_discrete_timeseries_2 = BalanceDiscreteTimeseries(
            iterable=[
                (
                    datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(10), debit=Decimal(10), net=Decimal(0)),
                ),
                (
                    datetime(2020, 2, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0)),
                ),
                (
                    datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
                    Balance(
                        credit=Decimal(40), debit=Decimal(40), net=Decimal(0)
                    ),  # different credit & debit
                ),
            ]
        )
        self.assertNotEqual(balance_discrete_timeseries_1, balance_discrete_timeseries_2)
