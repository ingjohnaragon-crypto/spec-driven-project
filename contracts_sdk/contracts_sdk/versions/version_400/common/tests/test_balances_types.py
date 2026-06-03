from unittest import TestCase
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)

from ..types import (
    AddressDetails,
    Balance,
    BalanceCoordinate,
    BalanceDefaultDict,
    BalancesObservation,
    DateTimeView,
    DEFAULT_ADDRESS,
    DEFAULT_ASSET,
    Phase,
    
)

from .....utils.exceptions import (
    StrongTypingError,
    InvalidSmartContractError,
)

from .....utils.feature_flags import (
    
    skip_if_not_enabled,
    BOOKING_BALANCES,
)


class PublicCommonV400BalancesTypesTestCase(TestCase):
    # AddressDetails

    def test_address_details(self):
        address_details = AddressDetails(
            account_address="DEFAULT", description="Some desc", tags=["one", "two"]
        )

        self.assertEqual("DEFAULT", address_details.account_address)
        self.assertEqual("Some desc", address_details.description)
        self.assertEqual(["one", "two"], address_details.tags)

    def test_address_details_repr(self):
        address_details = AddressDetails(
            account_address="DEFAULT", description="Some desc", tags=["one", "two"]
        )
        expected = (
            "AddressDetails(account_address='DEFAULT', "
            + "description='Some desc', tags=['one', 'two'])"
        )
        self.assertEqual(expected, repr(address_details))

    def test_address_details_equality(self):
        default = AddressDetails(
            account_address="DEFAULT", description="Default address", tags=["default"]
        )
        other_default = AddressDetails(
            account_address="DEFAULT", description="Default address", tags=["default"]
        )
        self.assertEqual(default, other_default)

    def test_address_details_unequal_tags(self):
        default = AddressDetails(
            account_address="DEFAULT", description="Default address", tags=["default"]
        )
        other_default = AddressDetails(
            account_address="DEFAULT", description="Default address", tags=["default1"]
        )
        self.assertNotEqual(default, other_default)

    def test_address_details_raises_with_no_address(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            AddressDetails(account_address=None, description="Some desc", tags=["one", "two"])
        self.assertEqual("AddressDetails 'account_address' must be populated", str(ex.exception))

    def test_address_details_raises_with_no_description(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            AddressDetails(account_address="DEFAULT", description=None, tags=["one", "two"])
        self.assertEqual("AddressDetails 'description' must be populated", str(ex.exception))

    def test_address_details_raises_with_no_tags(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            AddressDetails(account_address="DEFAULT", description="Some desc", tags=None)
        self.assertEqual("AddressDetails 'tags' must be populated", str(ex.exception))

    def test_address_details_raises_with_invalid_tags(self):
        with self.assertRaises(StrongTypingError) as ex:
            AddressDetails(account_address="DEFAULT", description="Some desc", tags=False)
        self.assertEqual("'tags' expected list, got 'False' of type bool", str(ex.exception))

    def test_address_details_skips_validation(self):
        address = AddressDetails(
            account_address="foo", description=None, tags=None, _from_proto=True
        )
        self.assertEqual("foo", address.account_address)

    # Balance

    def test_balance_equality(self):
        balance = Balance(credit=Decimal(42))
        other_balance = Balance(credit=Decimal(42))
        self.assertEqual(balance, other_balance)

    def test_balance_repr(self):
        balance = Balance(credit=Decimal(40), debit=Decimal(10), net=-Decimal(30))
        expected = "Balance(credit=Decimal('40'), debit=Decimal('10'), net=Decimal('-30'))"
        self.assertEqual(expected, repr(balance))

    def test_balance_unequal_credit(self):
        balance = Balance(credit=Decimal(42))
        other_balance = Balance(credit=Decimal(11))
        self.assertNotEqual(balance, other_balance)

    def test_balance_aggregation_add(self):
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(10), debit=Decimal(20), net=-Decimal(10))
        aggregated_balance = balance_1 + balance_2
        self.assertEqual(30, aggregated_balance.credit)
        self.assertEqual(40, aggregated_balance.debit)
        self.assertEqual(-10, aggregated_balance.net)

    def test_balance_aggregation_iadd(self):
        aggregated_balance = Balance()
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(10), debit=Decimal(20), net=-Decimal(10))
        aggregated_balance += balance_1
        aggregated_balance += balance_2
        self.assertEqual(30, aggregated_balance.credit)
        self.assertEqual(40, aggregated_balance.debit)
        self.assertEqual(-10, aggregated_balance.net)

    def test_balance_aggregation_radd(self):
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_3 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        aggregated_balance = sum([balance_1, balance_2, balance_3], Balance())
        self.assertEqual(
            Balance(credit=Decimal(60), debit=Decimal(60), net=Decimal(0)), aggregated_balance
        )

    def test_balance_credit(self):
        balance = Balance(credit=Decimal(100))
        self.assertEqual(balance.credit, Decimal(100))
        self.assertEqual(balance.net, 0)
        self.assertEqual(balance.debit, 0)

    def test_balance_net(self):
        balance = Balance(net=Decimal(120))
        self.assertEqual(balance.credit, 0)
        self.assertEqual(balance.net, Decimal(120))
        self.assertEqual(balance.debit, 0)

    def test_balance_debit(self):
        balance = Balance(debit=Decimal(19.99))
        self.assertEqual(balance.credit, 0)
        self.assertEqual(balance.net, 0)
        self.assertEqual(balance.debit, Decimal(19.99))

    # BalanceCoordinate

    def test_balance_coordinate_equality(self):
        balance_coordinate = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        other_balance_coordinate = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )

        self.assertEqual(balance_coordinate, other_balance_coordinate)
        self.assertEqual(
            balance_coordinate, (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_OUT)
        )

    def test_balance_coordinate_unequal_phase(self):
        balance_coordinate = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.PENDING_OUT,
        )
        other_balance_coordinate = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.COMMITTED,
        )

        self.assertNotEqual(balance_coordinate, other_balance_coordinate)

    # BalanceDefaultDict

    def test_balance_default_dict_repr(self):
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(10), debit=Decimal(20), net=Decimal(-10))
        address = "DEFAULT"
        asset = "COMMERCIAL_BANK_MONEY"
        denomination = "GBP"
        balance_key_committed = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.COMMITTED
        )
        balance_key_out = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.PENDING_OUT
        )
        balance_key_in = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.PENDING_IN
        )

        balance_dict = BalanceDefaultDict()
        balance_dict[balance_key_committed] = balance_1
        balance_dict[balance_key_out] = balance_1 + balance_2
        balance_dict[balance_key_in] = balance_2

        expected_balance_dict = (
            "{'BalanceCoordinate(account_address=DEFAULT, asset=COMMERCIAL_BANK_MONEY, "
            "denomination=GBP, phase=Phase.COMMITTED)': 'Balance(credit=20, debit=20, net=0)', "
            "'BalanceCoordinate(account_address=DEFAULT, asset=COMMERCIAL_BANK_MONEY, "
            "denomination=GBP, phase=Phase.PENDING_OUT)': 'Balance(credit=30, debit=40, net=-10)', "
            "'BalanceCoordinate(account_address=DEFAULT, asset=COMMERCIAL_BANK_MONEY, "
            "denomination=GBP, phase=Phase.PENDING_IN)': 'Balance(credit=10, debit=20, net=-10)'}"
        )
        self.assertEqual(repr(balance_dict), expected_balance_dict)

    def test_balance_default_dict_equality(self):
        balance_default_dict = BalanceDefaultDict(
            default_dict=lambda *_: Balance(),
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(5.50)
                )
            },
        )
        # Default dict doesn't affect equality
        other_balance_default_dict = BalanceDefaultDict(
            default_dict=lambda *_: Balance(credit=Decimal(4.2)),
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(5.50)
                )
            },
        )

        self.assertEqual(balance_default_dict, other_balance_default_dict)

    def test_balance_default_dict_unequal_mapping(self):
        balance_default_dict = BalanceDefaultDict(
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(1)
                )
            }
        )
        other_balance_default_dict = BalanceDefaultDict(
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(5.50)
                )
            }
        )

        self.assertNotEqual(balance_default_dict, other_balance_default_dict)

    def test_balance_default_dict_aggregation_add(self):
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(10), debit=Decimal(20), net=-Decimal(10))
        address = "DEFAULT"
        asset = "COMMERCIAL_BANK_MONEY"
        denomination = "GBP"
        balance_key_committed = BalanceCoordinate(
            account_address=address,
            asset=asset,
            denomination=denomination,
            phase=Phase.COMMITTED,
        )
        balance_key_out = BalanceCoordinate(
            account_address=address,
            asset=asset,
            denomination=denomination,
            phase=Phase.PENDING_OUT,
        )
        balance_key_in = BalanceCoordinate(
            account_address=address,
            asset=asset,
            denomination=denomination,
            phase=Phase.PENDING_IN,
        )

        balance_default_dict_1 = BalanceDefaultDict()
        balance_default_dict_1[balance_key_committed] = balance_1
        balance_default_dict_1[balance_key_out] = balance_1

        balance_default_dict_2 = BalanceDefaultDict()
        balance_default_dict_2[balance_key_out] = balance_2
        balance_default_dict_2[balance_key_in] = balance_2

        aggregated_balance_default_dict = balance_default_dict_1 + balance_default_dict_2

        expected_aggregated_balance_default_dict = BalanceDefaultDict()
        expected_aggregated_balance_default_dict[balance_key_committed] = balance_1
        expected_aggregated_balance_default_dict[balance_key_out] = balance_1
        expected_aggregated_balance_default_dict[balance_key_out] = balance_1 + balance_2
        expected_aggregated_balance_default_dict[balance_key_in] = balance_2

        self.assertEqual(
            expected_aggregated_balance_default_dict[balance_key_committed].net,
            aggregated_balance_default_dict[balance_key_committed].net,
        )

        self.assertEqual(
            expected_aggregated_balance_default_dict[balance_key_out].net,
            aggregated_balance_default_dict[balance_key_out].net,
        )

        self.assertEqual(
            expected_aggregated_balance_default_dict[balance_key_in].net,
            aggregated_balance_default_dict[balance_key_in].net,
        )

    def test_balance_default_dict_aggregation_iadd(self):
        aggregated_balance_default_dict = BalanceDefaultDict(lambda *_: Balance())
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(10), debit=Decimal(20), net=-Decimal(10))
        address = "DEFAULT"
        asset = "COMMERCIAL_BANK_MONEY"
        denomination = "GBP"
        balance_key_committed = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.COMMITTED
        )
        balance_key_out = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.PENDING_OUT
        )
        balance_key_in = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.PENDING_IN
        )

        balance_default_dict_1 = BalanceDefaultDict()
        balance_default_dict_1[balance_key_committed] = balance_1
        balance_default_dict_1[balance_key_out] = balance_1

        balance_default_dict_2 = BalanceDefaultDict()
        balance_default_dict_2[balance_key_out] = balance_2
        balance_default_dict_2[balance_key_in] = balance_2

        aggregated_balance_default_dict += balance_default_dict_1
        aggregated_balance_default_dict += balance_default_dict_2

        expected_aggregated_balance_default_dict = BalanceDefaultDict()
        expected_aggregated_balance_default_dict[balance_key_committed] = balance_1
        expected_aggregated_balance_default_dict[balance_key_out] = balance_1 + balance_2
        expected_aggregated_balance_default_dict[balance_key_in] = balance_2

        self.assertDictEqual(
            expected_aggregated_balance_default_dict, aggregated_balance_default_dict
        )

    def test_balance_default_dict_aggregation_radd(self):
        balance_1 = Balance(credit=Decimal(20), debit=Decimal(20), net=Decimal(0))
        balance_2 = Balance(credit=Decimal(10), debit=Decimal(20), net=-Decimal(10))
        address = "DEFAULT"
        asset = "COMMERCIAL_BANK_MONEY"
        denomination = "GBP"
        balance_key_committed = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.COMMITTED
        )
        balance_key_out = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.PENDING_OUT
        )
        balance_key_in = BalanceCoordinate(
            account_address=address, asset=asset, denomination=denomination, phase=Phase.PENDING_IN
        )

        balance_default_dict_1 = BalanceDefaultDict()
        balance_default_dict_1[balance_key_committed] = balance_1
        balance_default_dict_1[balance_key_out] = balance_1

        balance_default_dict_2 = BalanceDefaultDict()
        balance_default_dict_2[balance_key_out] = balance_2
        balance_default_dict_2[balance_key_in] = balance_2

        aggregated_balance_default_dict = sum(
            [balance_default_dict_1, balance_default_dict_2],
            BalanceDefaultDict(lambda *_: Balance()),
        )

        expected_aggregated_balance_default_dict = BalanceDefaultDict()
        expected_aggregated_balance_default_dict[balance_key_committed] = balance_1
        expected_aggregated_balance_default_dict[balance_key_out] = balance_1 + balance_2
        expected_aggregated_balance_default_dict[balance_key_in] = balance_2

        self.assertDictEqual(
            expected_aggregated_balance_default_dict, aggregated_balance_default_dict
        )

    # BalancesObservation

    def test_balances_observation(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        balance_key_1 = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="USD",
            phase=Phase.COMMITTED,
        )
        balance_dict = BalanceDefaultDict()
        balance_dict[balance_key_1] = Balance(net=Decimal("20"), credit=Decimal("20"))
        balances_observation = BalancesObservation(
            value_datetime=value_datetime, balances=balance_dict
        )
        self.assertEqual(balance_dict, balances_observation.balances)
        self.assertEqual(value_datetime, balances_observation.value_datetime)

    def test_balances_observation_repr(self):
        balance_key_1 = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="USD",
            phase=Phase.COMMITTED,
        )
        balance_dict = BalanceDefaultDict()
        balance_dict[balance_key_1] = Balance(net=Decimal("20"), credit=Decimal("20"))
        balances_observation = BalancesObservation(
            value_datetime=datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC")),
            balances=balance_dict,
            at_datetime=datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC")),
            datetime_view=DateTimeView.VALUE_DATETIME,
        )
        self.assertTrue(issubclass(BalancesObservation, ContractsLanguageDunderMixin))
        self.assertIn("BalancesObservation", repr(balances_observation))

    def test_balances_observation_equality(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        balance_default_dict = BalanceDefaultDict(
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(5.50)
                )
            }
        )
        other_balance_default_dict = BalanceDefaultDict(
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(5.50)
                )
            }
        )

        balances_observation = BalancesObservation(
            value_datetime=value_datetime, balances=balance_default_dict
        )
        other_balances_observation = BalancesObservation(
            value_datetime=value_datetime, balances=other_balance_default_dict
        )

        self.assertEqual(balances_observation, other_balances_observation)

    def test_balances_observation_unequal_balances(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        balance_default_dict = BalanceDefaultDict(
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(5.50)
                )
            }
        )
        other_balance_default_dict = BalanceDefaultDict(
            mapping={
                (DEFAULT_ADDRESS, DEFAULT_ASSET, "GBP", Phase.PENDING_IN): Balance(
                    credit=Decimal(1)
                )
            }
        )

        balances_observation = BalancesObservation(
            value_datetime=value_datetime, balances=balance_default_dict
        )
        other_balances_observation = BalancesObservation(
            value_datetime=value_datetime, balances=other_balance_default_dict
        )

        self.assertNotEqual(balances_observation, other_balances_observation)

    def test_balances_observation_raises_with_wrong_balances_type(self):
        with self.assertRaises(StrongTypingError) as e:
            BalancesObservation(balances=None)
        self.assertEqual(
            str(e.exception),
            "'BalancesObservation.balances' expected BalanceDefaultDict, got None",
        )

    def test_balances_observation_raises_with_naive_datetime(self):
        value_datetime = datetime(year=2020, month=2, day=20)
        balance_dict = BalanceDefaultDict()
        with self.assertRaises(InvalidSmartContractError) as e:
            BalancesObservation(value_datetime=value_datetime, balances=balance_dict)
        self.assertEqual(
            str(e.exception),
            "'value_datetime' of BalancesObservation is not timezone aware.",
        )

    def test_balances_observation_raises_with_non_utc_timezone(self):
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("US/Pacific"))
        balance_dict = BalanceDefaultDict()
        with self.assertRaises(InvalidSmartContractError) as e:
            BalancesObservation(value_datetime=value_datetime, balances=balance_dict)
        self.assertEqual(
            str(e.exception),
            "'value_datetime' of BalancesObservation must have timezone UTC, currently "
            "US/Pacific.",
        )

    def test_balances_observation_raises_with_non_zoneinfo_timezone(self):
        value_datetime = datetime.fromtimestamp(1, timezone.utc)
        balance_dict = BalanceDefaultDict()
        with self.assertRaises(InvalidSmartContractError) as e:
            BalancesObservation(value_datetime=value_datetime, balances=balance_dict)
        self.assertEqual(
            "'value_datetime' of BalancesObservation must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(e.exception),
        )

    def test_balances_observation_no_value_datetime_and_empty_balances(self):
        balance_dict = BalanceDefaultDict()
        balances_observation = BalancesObservation(value_datetime=None, balances=balance_dict)
        self.assertEqual(None, balances_observation.value_datetime)
        self.assertEqual(balance_dict, balances_observation.balances)

    @skip_if_not_enabled(BOOKING_BALANCES)
    def test_balances_observation_with_at_datetime_and_datetime_view(self):
        balance_key_1 = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="USD",
            phase=Phase.COMMITTED,
        )
        balance_dict = BalanceDefaultDict()
        balance_dict[balance_key_1] = Balance(net=Decimal("20"), credit=Decimal("20"))
        value_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        at_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        datetime_view = DateTimeView.VALUE_DATETIME
        balances_observation = BalancesObservation(
            balances=balance_dict,
            value_datetime=value_datetime,
            at_datetime=at_datetime,
            datetime_view=datetime_view,
        )
        self.assertEqual(balance_dict, balances_observation.balances)
        self.assertEqual(value_datetime, balances_observation.value_datetime)
        self.assertEqual(at_datetime, balances_observation.at_datetime)
        self.assertEqual(datetime_view.VALUE_DATETIME, balances_observation.datetime_view)

    @skip_if_not_enabled(BOOKING_BALANCES)
    def test_balances_observation_with_at_datetime_and_datetime_view_equality(self):
        at_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        other_at_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        datetime_view = DateTimeView.VALUE_DATETIME
        other_datetime_view = DateTimeView.VALUE_DATETIME
        balances_observation = BalancesObservation(
            balances=BalanceDefaultDict(),
            at_datetime=at_datetime,
            datetime_view=datetime_view,
        )
        other_balances_observation = BalancesObservation(
            balances=BalanceDefaultDict(),
            at_datetime=other_at_datetime,
            datetime_view=other_datetime_view,
        )
        self.assertEqual(balances_observation, other_balances_observation)

    @skip_if_not_enabled(BOOKING_BALANCES)
    def test_balances_observation_at_datetime_inequality(self):
        at_datetime = datetime(year=2020, month=2, day=20, tzinfo=ZoneInfo("UTC"))
        other_at_datetime = datetime(year=2020, month=2, day=21, tzinfo=ZoneInfo("UTC"))
        balances_observation = BalancesObservation(
            balances=BalanceDefaultDict(),
            at_datetime=at_datetime,
        )
        other_balances_observation = BalancesObservation(
            balances=BalanceDefaultDict(),
            at_datetime=other_at_datetime,
        )
        self.assertNotEqual(balances_observation, other_balances_observation)

    @skip_if_not_enabled(BOOKING_BALANCES)
    def test_balances_observation_datetime_view_inequality(self):
        datetime_view = DateTimeView.BOOKING_DATETIME
        other_datetime_view = DateTimeView.VALUE_DATETIME
        balances_observation = BalancesObservation(
            balances=BalanceDefaultDict(), datetime_view=datetime_view
        )
        other_balances_observation = BalancesObservation(
            balances=BalanceDefaultDict(),
            datetime_view=other_datetime_view,
        )
        self.assertNotEqual(balances_observation, other_balances_observation)



