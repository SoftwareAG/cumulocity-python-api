# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
import re
from datetime import datetime, timedelta, timezone
from dateutil import parser
from re import sub


class _StringUtil(object):

    TO_PASCAL_PATTERN = re.compile(r'_([a-z])')

    @staticmethod
    def to_pascal_case(name: str):
        """Convert a given snake case (default Python style) name to pascal case (default for names in Cumulocity)"""
        parts = list(filter(None, name.split('_')))
        if len(parts) == 1:
            return name
        return parts[0] + "".join([x.title() for x in parts[1:]])


class _QueryUtil(object):

    @staticmethod
    def encode_odata_query_value(value):
        """Encode value strings according to OData query rules.
        http://docs.oasis-open.org/odata/odata/v4.01/odata-v4.01-part2-url-conventions.html#sec_URLParsing
        http://docs.oasis-open.org/odata/odata/v4.01/cs01/abnf/odata-abnf-construction-rules.txt """
        # single quotes escaped through single quote
        return sub('\'', '\'\'', value)


class _DateUtil(object):

    @staticmethod
    def now_timestring() -> str:
        """Provide an ISO timestring for the current time."""
        return _DateUtil.to_timestring(_DateUtil.now())

    @staticmethod
    def to_timestring(dt: datetime):
        """Format a datetime as ISO timestring."""
        return dt.isoformat(timespec='milliseconds')

    @staticmethod
    def to_datetime(string):
        """Parse an ISO timestring as datetime object."""
        return parser.parse(string)

    @staticmethod
    def now():
        """Provide the current time as datetime object."""
        return datetime.now(timezone.utc)

    @staticmethod
    def ensure_timestring(time):
        """Ensure that a given timestring reflects a proper, timezone aware date/time.
        A static string 'now' will be converted to the current datetime in UTC."""
        if isinstance(time, datetime):
            if not time.tzinfo:
                raise ValueError("A specified datetime needs to be timezone aware.")
            return _DateUtil.to_timestring(time)
        if time == 'now':
            return _DateUtil.now_timestring()
        return time  # assuming it is a timestring

    @staticmethod
    def ensure_timedelta(time):
        """Ensure that a given object is a timedelta object."""
        if not isinstance(time, timedelta):
            raise ValueError("A specified duration needs to be a timedelta object.")
        return time
