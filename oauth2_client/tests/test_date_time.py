"""
Test cases for datetime utils.
"""
from datetime import datetime
from unittest import TestCase

import pytz
from pytz import timezone

from oauth2_client.utils.date_time import datetime_to_float, float_to_datetime


class TestDateTime(TestCase):
    """
    Test cases for datetime utils.
    """

    def test_datetime_to_float_timezone_aware(self):
        """
        2h into the epoch in CET is 1h into the epoch in UTC.
        Return a timezone-aware object.
        """
        cet_tz = timezone('CET')
        dt = datetime(1970, 1, 1, 2, 0, 0, 123000, tzinfo=cet_tz)
        expected_ts = 3600.123  # 123000 microseconds = 123 milliseconds
        actual_ts = datetime_to_float(dt)
        self.assertAlmostEqual(expected_ts, actual_ts)

    def test_datetime_to_float_timezone_aware_zero(self):
        """
        The epoch start in UTC sure equals ts=0.
        Return a timezone-aware object.
        """
        dt = datetime(1970, 1, 1, 0, 0, tzinfo=pytz.UTC)
        expected_ts = 0
        actual_ts = datetime_to_float(dt)
        self.assertAlmostEqual(expected_ts, actual_ts)

    def test_datetime_to_float_timezone_naive(self):
        """
        2h after the epoch begins.
        Return a timezone-naive object.
        """
        dt = datetime(1970, 1, 1, 2, 0)
        expected_ts = 3600 * 2
        actual_ts = datetime_to_float(dt)
        self.assertAlmostEqual(expected_ts, actual_ts)

    def test_float_to_datetime_naive(self):
        """
        Without timezone: ts=3600 is 1h after the epoch start.
        Return a timezone-naive object, assumed to be UTC.
        """
        input_ts = 3600
        expected_dt = datetime(1970, 1, 1, 1, 0, 0)  # 1h after epoch starts
        actual_dt = float_to_datetime(input_ts)
        self.assertEqual(expected_dt, actual_dt)

    def test_float_to_datetime_tz(self):
        """
        Epoch starts at 1am CET (midnight UTC). So 1h from that time is 2am CET, 1am UTC.
        Returns timezone-aware object.
        """
        cet_tz = timezone('CET')
        input_ts = 3600
        expected_dt_cet = datetime(1970, 1, 1, 2, 0, 0, tzinfo=cet_tz)
        expected_dt_utc = datetime(1970, 1, 1, 1, 0, 0, tzinfo=pytz.UTC)
        actual_dt = float_to_datetime(input_ts, tzinfo=cet_tz)
        self.assertEqual(expected_dt_cet, actual_dt)
        self.assertEqual(expected_dt_utc, actual_dt.astimezone(pytz.UTC))
