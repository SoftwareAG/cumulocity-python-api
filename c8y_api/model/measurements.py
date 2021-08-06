# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api._base_api import CumulocityRestApi

from c8y_api.model._base import CumulocityResource, ComplexObject
from c8y_api.model._parser import ComplexObjectParser
from c8y_api.model._updatable import _DictWrapper
from c8y_api.model._util import _DateUtil


class Value(dict):
    def __init__(self, value, unit):
        super().__init__(value=value, unit=unit)


class Grams(Value):
    def __init__(self, value):
        super().__init__(value, 'g')


class Kilograms(Value):
    def __init__(self, value):
        super().__init__(value, 'kg')


class Kelvin(Value):
    def __init__(self, value):
        super().__init__(value, '°K')


class Celsius(Value):
    def __init__(self, value):
        super().__init__(value, '°C')


class Meters(Value):
    def __init__(self, value):
        super().__init__(value, 'm')


class Centimeters(Value):
    def __init__(self, value):
        super().__init__(value, 'cm')


class Liters(Value):
    def __init__(self, value):
        super().__init__(value, 'l')


class CubicMeters(Value):
    def __init__(self, value):
        super().__init__(value, 'm3')


class Count(Value):
    def __init__(self, value):
        super().__init__(value, '#')


class Measurement(ComplexObject):
    """ Represents an instance of a measurement object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Measurements API. Use this class to create new or update existing
    measurements.

    See also: https://cumulocity.com/guides/reference/measurements/#measurement
    """

    __RESOURCE = '/measurement/measurements/'

    __parser = ComplexObjectParser(
        to_json_mapping={'id': 'id',
                         'type': 'type',
                         'time': 'time'},
        no_fragments_list=['self', 'time', 'source'])

    def __init__(self, c8y=None, type=None, source=None, time=None):  # noqa (type)
        """ Create a new Measurement object.

        :param c8y:  Cumulocity connection reference; needs to be set for the
            direct manipulation (create, delete) to function
        :param type:   Measurement type
        :param source:  Device ID which this measurement is for
        :param time:   Datetime string or Python datetime object. A given
            datetime string needs to be in standard ISO format incl. timezone:
            YYYY-MM-DD'T'HH:MM:SS.SSSZ as it is retured by the Cumulocity REST
            API. A given datetime object needs to be timezone aware.
            For manual construction it is recommended to specify a datetime
            object as the formatting of a timestring is never checked for
            performance reasons.
        :returns:  Measurement object
        """
        super().__init__(c8y)
        self.id = None
        self.type = type
        self.source = source
        # The time can either be set as string (e.g. when read from JSON) or
        # as a datetime object. It will be converted to string immediately
        # as there is no scenario where a manually created object won't be
        # written to Cumulocity anyways
        self.time = _DateUtil.ensure_timestring(time)

    @classmethod
    def from_json(cls, measurement_json):
        """ Build a new Measurement instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        :param measurement_json:  JSON object (nested dictionary)
            representing a measurement within Cumulocity
        :returns:  Measurement object
        """
        obj = cls.__parser.from_json(measurement_json, Measurement())
        obj.source = measurement_json['source']['id']
        return obj

    def to_json(self):
        """ Convert the instance to JSON.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        :returns:  JSON object (nested dictionary)
        """
        measurement_json = self.__parser.to_full_json(self)
        if not self.time:
            measurement_json['time'] = _DateUtil.to_timestring(_DateUtil.now())
        measurement_json['source'] = {'id': self.source}
        return measurement_json

    # the __getattr__ function is overwritten to return a wrapper that doesn't signal updates
    # (because Measurements are not updated, can only be created from scratch)
    def __getattr__(self, item):
        return _DictWrapper(self.fragments[item], on_update=None)

    @property
    def datetime(self):
        """ Convert the measurement's time to a Python datetime object.

        :returns:  Standard Python datetime object
        """
        if self.time:
            return _DateUtil.to_datetime(self.time)
        return None

    def create(self):
        """ Store the Measurement within the database.

        :returns:  A fresh Measurement object representing what was
            created within the database (including the ID).
        """
        self._assert_c8y()
        result_json = self.c8y.post(self.__RESOURCE, self.to_json())
        result = Measurement.from_json(result_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        """ Delete the Measurement within the database.

        :returns: None
        """
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete(self.__RESOURCE + self.id)


class Measurements(CumulocityResource):
    """ A wrapper for the standard Measurements API.

    This class can be used for get, search for, create, update and
    delete measurements within the Cumulocity database.

    See also: https://cumulocity.com/guides/reference/measurements/#measurement
    """

    def __init__(self, c8y: CumulocityRestApi):
        super().__init__(c8y, 'measurement/measurements')

    def get(self, measurement_id):
        """ Read a specific measurement from the database.

        :param measurement_id:  database ID of a measurement (int or str)
        :returns:  Measurement object
        """
        measurement = Measurement.from_json(self._get_object(measurement_id))
        measurement.c8y = self.c8y  # inject c8y connection into instance
        return measurement

    def select(self, type=None, source=None,  # noqa (type)
               fragment=None, value=None, series=None,
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """ Query the database for measurements and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Alarm type
        :param source:  Database ID of a source device
        :param fragment:  Name of a present custom/standard fragment
        :param value:  Name/type of a present value fragment
        :param series:  Name of a present series within a value fragment
        :param before:  Datetime object or ISO date/time string. Only
            measurements assigned to a time before this date are returned.
        :param after:  Datetime object or ISO date/time string. Only
            measurements assigned to a time after this date are returned.
        :param min_age:  Timedelta object. Only measurements of at least
            this age are returned.
        :param max_age:  Timedelta object. Only measurements with at most
            this age are returned.

        :param reverse:  Invert the order of results, starting with the
            most recent one.
        :param limit:  Limit the number of results to this number.
        :param page_size:  Define the number of measurements which are read (and
            parsed in one chunk). This is a performance related setting.

        :returns:  Iterable of Measurement objects
        """
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            valueFragmentType=value, valueFragmentSeries=series,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        return super()._iterate(base_query, limit, Measurement.from_json)

    def get_all(self, type=None, source=None,  # noqa (type)
                fragment=None,  value=None, series=None,
                before=None, after=None, min_age=None, max_age=None, reverse=False,
                limit=None, page_size=1000):
        """ Query the database for measurements and return the results
        as list.

        This function is a greedy version of the select function. All
        available results are read immediately and returned as list.

        :returns:  List of Measurement objects
        """
        return list(self.select(type=type, source=source,
                                fragment=fragment, value=value, series=series,
                                before=before, after=after, min_age=min_age, max_age=max_age,
                                reverse=reverse, limit=limit, page_size=page_size))

    def get_last(self, type=None, source=None, fragment=None, value=None, series=None,  # noqa (type)
                 before=None, min_age=None):
        """ Query the database and return the last matching measurement.

        This function is a special variant of the select function. Only
        the last matching result is returned.

        :returns:  Measurement object
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

        :param type:  Measurement type
        :param source:  Database ID of a source device
        :param fragment:  Name of a present custom/standard fragment
        :param value:  Name/type of a present value fragment
        :param series:  Name of a present series within a value fragment
        :param before:  Datetime object or ISO date/time string. Only
            measurements assigned to a time before this date are returned.
        :param after:  Datetime object or ISO date/time string. Only
            measurements assigned to a time after this date are returned.
        :param min_age:  Timedelta object. Only measurements of at least
            this age are returned.
        :param max_age:  Timedelta object. Only measurements with at most
            this age are returned.

        :returns: None
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

        :param measurements:  Collection of Measurement objects.
        :returns:  None
        """
        self._create_bulk(Measurement.to_json, 'measurements', self.c8y.CONTENT_MEASUREMENT_COLLECTION, *measurements)
