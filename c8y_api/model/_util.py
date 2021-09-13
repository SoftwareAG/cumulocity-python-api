# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from datetime import datetime, timedelta, timezone
from dateutil import parser


class _DateUtil(object):

    @staticmethod
    def now_timestring() -> str:
        return _DateUtil.to_timestring(_DateUtil.now())

    @staticmethod
    def to_timestring(dt: datetime):
        return dt.isoformat(timespec='milliseconds')

    @staticmethod
    def to_datetime(string):
        return parser.parse(string)

    @staticmethod
    def now():
        return datetime.now(timezone.utc)

    @staticmethod
    def ensure_timestring(time):
        if isinstance(time, datetime):
            if not time.tzinfo:
                raise ValueError("A specified datetime needs to be timezone aware.")
            return _DateUtil.to_timestring(time)
        return time  # assuming it is a timestring

    @staticmethod
    def ensure_timedelta(time):
        if not isinstance(time, timedelta):
            raise ValueError("A specified duration needs to be a timedelta object.")
        return time
