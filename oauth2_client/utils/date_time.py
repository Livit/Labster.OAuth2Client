"""
Datetime related utilities.
"""
from datetime import datetime

import pytz


def datetime_to_float(d):
    """
    Convert a datetime object to a floating point timestamp.
    Return a number of seconds elapsed from the UTC epoch.
    Compatible with both Python 2 and 3.

    If the input object is timezone-aware, the result includes timezone
    difference between UTC and the timezone.

    If the input object is timezone-naive, it's treated as UTC.
    NOTE: This behaviour is different from the standard's library
    `datetime.timestamp()`, that assumes local timezone.

    For example, 2h into the epoch in CET is 1h into the epoch in UTC
    (CET = UTC + 1h), so:

        >> cet_tz = timezone('CET')
        >> dt = datetime(1970, 1, 1, 2, 0, 0, tzinfo=cet_tz)
        >> datetime_to_float(dt)
        3600.0

    In case of a timezone-naive object, we treat the input as UTC, so:

        >> dt = datetime(1970, 1, 1, 2, 0)
        >> ts_expected = 3600 * 2
        >> datetime_to_float(dt)
        7200.0

    See tests for more examples.

    Args:
        d (datetime): timezone-aware or not

    Returns:
        float: e.g. 123456.123, always counting from UTC
    """
    epoch = datetime.fromtimestamp(0, tz=pytz.UTC)
    if not d.tzinfo:
        epoch = epoch.replace(tzinfo=None)

    total_seconds = (d - epoch).total_seconds()
    return total_seconds


def float_to_datetime(timestamp, tzinfo=None):
    """
    Convert a timestamp to a datetime instance.
    Compatible with both Python 2 and 3.

    If tzinfo is passed, interpret the timestamp in the given timezone.

    If tzinfo isn't passed, interpret the timestamp as UTC.
    NOTE: this behaviour is different from the standard's library
    `datetime.fromtimestamp()`, that assumes local timezone.

    For example, epoch starts at 1am CET (midnight UTC, as CET = UTC + 1h).
    So 1h from that time is 2am CET.

        >> cet_tz = timezone('CET')
        >> float_to_datetime(3600, tzinfo=cet_tz)
        datetime.datetime(1970, 1, 1, 2, 0, tzinfo=<DstTzInfo 'CET' CET+1:00:00 STD>)

    Without timezone, 3600s from the epoch start is just 1h into the epoch:

        >> float_to_datetime(3600)
        datetime.datetime(1970, 1, 1, 1, 0)

    See tests for more examples.

    Args:
        timestamp (float): e.g. 123456.123, seconds from the epoch, can include
            milliseconds
        tzinfo (timezone): optional timezone object

    Returns:
        datetime: if no timezone given - a timezone-naive datetime.
                  Otherwise - a datetime object in the given timezone.
    """
    _tz = tzinfo if tzinfo else pytz.UTC
    dt = datetime.fromtimestamp(timestamp, tz=_tz)

    if not tzinfo:
        dt = dt.replace(tzinfo=None)
    return dt
