from datetime import datetime, timezone
import unittest

from ..exceptions import InvalidSmartContractError
from ..timezone_utils import validate_datetime_is_timezone_aware


class TimezoneUtilsTestCase(unittest.TestCase):
    def test_timezone_unaware_datetime_validation_raises_error(self):
        timezone_unaware_datetime = datetime(year=2022, month=12, day=25, hour=10, minute=5)

        with self.assertRaises(InvalidSmartContractError) as e:
            validate_datetime_is_timezone_aware(
                timezone_unaware_datetime, "start_datetime", "ScheduledEvent"
            )
            self.assertEqual("'start_datetime' of ScheduledEvent is not timezone aware.", str(e))

    def test_timezone_aware_datetime_validation(self):
        timezone_aware_datetime = datetime(
            year=2022, month=12, day=25, hour=10, minute=5, tzinfo=timezone.utc
        )
        validate_datetime_is_timezone_aware(
            timezone_aware_datetime, "start_datetime", "ScheduledEvent"
        )
