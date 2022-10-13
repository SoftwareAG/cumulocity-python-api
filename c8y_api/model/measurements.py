# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

from typing import Type, List, Generator

from c8y_api._base_api import CumulocityRestApi

from c8y_api.model._base import CumulocityResource, ComplexObject
from c8y_api.model._parser import ComplexObjectParser
from c8y_api.model._base import _DictWrapper
from c8y_api.model._util import _DateUtil


class Value(dict):
    """Generic datapoint."""
    def __init__(self, value, unit):
        super().__init__(value=value, unit=unit)


class Grams(Value):
    """Weight datapoint (Grams)."""
    def __init__(self, value):
        super().__init__(value, 'g')


class Kilograms(Value):
    """Weight datapoint (Kilograms)."""
    def __init__(self, value):
        super().__init__(value, 'kg')


class Kelvin(Value):
    """Temperature datapoint (Kelvin)."""
    def __init__(self, value):
        super().__init__(value, '°K')


class Celsius(Value):
    """Temperature datapoint (Celsius)."""
    def __init__(self, value):
        super().__init__(value, '°C')


class Meters(Value):
    """Length datapoint (Meters)."""
    def __init__(self, value):
        super().__init__(value, 'm')


class Centimeters(Value):
    """Length datapoint (Centimeters)."""
    def __init__(self, value):
        super().__init__(value, 'cm')


class Millimeters(Value):
    """Length datapoint (Millimeters)."""
    def __init__(self, value):
        super().__init__(value, 'mm')


class Liters(Value):
    """Volume datapoint (Liters)."""
    def __init__(self, value):
        super().__init__(value, 'l')


class CubicMeters(Value):
    """Volume datapoint (Cubic Meters)."""
    def __init__(self, value):
        super().__init__(value, 'm3')


class Count(Value):
    """Discrete number datapoint (number/count)."""
    def __init__(self, value):
        super().__init__(value, '#')


class Measurement(ComplexObject):
    """ Represents an instance of a measurement object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Measurements API. Use this class to create new or update existing
    measurements.

    See also: https://cumulocity.com/guides/reference/measurements/#measurement
    """

    # these need to be defined like this for the abstract super functions
    _resource = '/measurement/measurements'
    _parser = ComplexObjectParser({'type': 'type', 'time': 'time'}, ['source'])
    # _accept
    # _not_updatable

    def __init__(self, c8y=None, type=None, source=None, time=None, **kwargs):
        """ Create a new Measurement object.

        Params:
            c8y(CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            type(str):  Measurement type
            source(str):  Device ID which this measurement is for
            time(str|datetime):  Datetime string or Python datetime object. A
                given datetime string needs to be in standard ISO format incl.
                timezone: YYYY-MM-DD'T'HH:MM:SS.SSSZ as it is retured by the
                Cumulocity REST API. A given datetime object needs to be
                timezone aware. For manual construction it is recommended to
                specify a datetime object as the formatting of a timestring
                is never checked for performance reasons.
            kwargs:  All additional named arguments are interpreted as
                custom fragments e.g. for data points.

        Returns:
            Measurement object
        """
        super().__init__(c8y, **kwargs)
        self.type = type
        self.source = source
        # The time can either be set as string (e.g. when read from JSON) or
        # as a datetime object. It will be converted to string immediately
        # as there is no scenario where a manually created object won't be
        # written to Cumulocity anyways
        self.time = _DateUtil.ensure_timestring(time)

    @classmethod
    def from_json(cls, json) -> Measurement:
        """ Build a new Measurement instance from Cumulocity JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        Params:
            measurement_json(dict):  JSON object (nested dictionary)
                representing a measurement within Cumulocity

        Returns:
            Measurement object
        """
        obj = cls._from_json(json, Measurement())
        obj.source = json['source']['id']
        return obj

    def to_json(self, only_updated=False) -> dict:
        """ Convert the instance to JSON.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        Note: Measurements cannot be updated, hence this function does not
        feature an only_updated argument.

        Returns:
            JSON object (nested dictionary)
        """
        if only_updated:
            raise NotImplementedError('The Measurement class does not support incremental updates.')
        measurement_json = super().to_json()
        measurement_json['source'] = {'id': self.source}
        if not self.time:
            measurement_json['time'] = _DateUtil.to_timestring(_DateUtil.now())
        return measurement_json

    # the __getitem__ function is overwritten to return a wrapper that doesn't signal updates
    # (because Measurements are not updated, can only be created from scratch)
    def __getitem__(self, item):
        return _DictWrapper(self.fragments[item], on_update=None)

    @property
    def datetime(self) -> Type[datetime] | None:
        """ Convert the measurement's time to a Python datetime object.

        Returns:
            (datetime): The measurement's time
        """
        if self.time:
            return _DateUtil.to_datetime(self.time)
        return None

    def create(self) -> Measurement:
        """ Store the Measurement within the database.

        Returns:  A fresh Measurement object representing what was
            created within the database (including the ID).
        """
        return self._create()

    def update(self) -> Measurement:
        """Not implemented for Measurements."""
        raise NotImplementedError('Measurements cannot be updated within Cumuylocity.')

    def delete(self):
        """Delete the Measurement within the database."""
        self._delete()


class Measurements(CumulocityResource):
    """ A wrapper for the standard Measurements API.

    This class can be used for get, search for, create, update and
    delete measurements within the Cumulocity database.

    See also: https://cumulocity.com/guides/reference/measurements/#measurement
    """

    def __init__(self, c8y: CumulocityRestApi):
        super().__init__(c8y, 'measurement/measurements')

    def get(self, measurement_id: str | int) -> Measurement:
        """ Read a specific measurement from the database.

        params:
            measurement_id (str|int):  database ID of a measurement

        Returns:
            Measurement object

        Raises:
            KeyError: If the ID cannot be resolved.
        """
        measurement = Measurement.from_json(self._get_object(measurement_id))
        measurement.c8y = self.c8y  # inject c8y connection into instance
        return measurement

    def select(self, type=None, source=None,  # noqa (type)
               fragment=None, value=None, series=None,
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000) -> Generator[Measurement]:
        """ Query the database for measurements and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        Params:
            type (str):  Alarm type
            source (str):  Database ID of a source device
            fragment (str):  Name of a present custom/standard fragment
            value (str):  Name/type of a present value fragment
            series (str):  Name of a present series within a value fragment
            before (datetime|str):  Datetime object or ISO date/time string.
                Only measurements assigned to a time before this date are
                returned.
            after (datetime|str):  Datetime object or ISO date/time string.
                Only measurements assigned to a time after this date are
                returned.
            min_age (timedelta):  Timedelta object. Only measurements of
                at least this age are returned.
            max_age (timedelta):  Timedelta object. Only measurements with
                at most this age are returned.
            reverse (bool):  Invert the order of results, starting with the
                most recent one.
            limit (int):  Limit the number of results to this number.
            page_size (int):  Define the number of measurements which are
                read (and parsed in one chunk). This is a performance
                related setting.

        Returns:
            Generator[Measurement]: Iterable of matching Measurement objects
        """
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            valueFragmentType=value, valueFragmentSeries=series,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        return super()._iterate(base_query, limit, Measurement.from_json)

    def get_all(self, type=None, source=None,  # noqa (type)
                fragment=None,  value=None, series=None,
                before=None, after=None, min_age=None, max_age=None, reverse=False,
                limit=None, page_size=1000) -> List[Measurement]:
        """ Query the database for measurements and return the results
        as list.

        This function is a greedy version of the select function. All
        available results are read immediately and returned as list.

        Returns:
            List of matching Measurement objects
        """
        return list(self.select(type=type, source=source,
                                fragment=fragment, value=value, series=series,
                                before=before, after=after, min_age=min_age, max_age=max_age,
                                reverse=reverse, limit=limit, page_size=page_size))

    def get_last(self, type=None, source=None, fragment=None, value=None, series=None,  # noqa (type)
                 before=None, min_age=None) -> Measurement:
        """ Query the database and return the last matching measurement.

        This function is a special variant of the select function. Only
        the last matching result is returned.

        Returns:
            Last matching Measurement object
        """
        # at least one date qualifier is required for this query to function,
        # so we enforce the 'after' filter if nothing else is specified
        after = None
        if not before and not min_age:
            after = '1970-01-01'
        base_query = self._build_base_query(type=type, source=source,
                                            fragment=fragment, value=value, series=series, after=after,
                                            before=before, min_age=min_age, reverse=True, page_size=1)
        m = Measurement.from_json(self._get_page(base_query, "1")[0])
        m.c8y = self.c8y  # inject c8y connection into instance
        return m

    def delete_by(self, type=None, source=None,  # noqa (type)
                fragment=None, value=None, series=None,
                before=None, after=None, min_age=None, max_age=None):
        """ Query the database and delete matching measurements.

         All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        Params: See 'select' function
        """
        base_query = self._build_base_query(type=type, source=source,
                                            fragment=fragment, value=value, series=series,
                                            before=before, after=after, min_age=min_age, max_age=max_age)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)

    # delete function is defined in super class

    def create(self, *measurements):
        """ Bulk create a collection of measurements within the database.

        Params:
            measurements (Iterable): Iterable collection of Measurement objects.
        """
        self._create_bulk(Measurement.to_json, 'measurements', self.c8y.CONTENT_MEASUREMENT_COLLECTION, *measurements)
