from ._util import _DateUtil, _Query, _DictWrapper, \
    _DatabaseObjectWithFragments, _DatabaseObjectWithFragmentsParser


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


class Measurement(_DatabaseObjectWithFragments):

    __parser = _DatabaseObjectWithFragmentsParser(
        to_json_mapping={'id': 'id',
                         'type': 'type'},
        no_fragments_list=['self', 'time', 'source'])

    def __init__(self, c8y=None, type=None, source=None, time=None):
        """ Create a new Measurement.

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
        obj = cls.__parser.from_json(measurement_json, Measurement())
        obj.source = measurement_json['source']['id']
        obj.time = measurement_json['time']
        return obj

    def to_json(self):
        measurement_json = self.__parser.to_full_json(self)
        measurement_json['time'] = self.time if self.time else _DateUtil.to_timestring(_DateUtil.now())
        measurement_json['source'] = {'id': self.source}
        return measurement_json

    # the __getattr__ function is overwritten to return a wrapper that doesn't signal updates
    # (because Measurements are not updated, can only be created from scratch)
    def __getattr__(self, item):
        return _DictWrapper(self.fragments[item], on_update=None)

    @property
    def datetime(self):
        if self.time:
            return _DateUtil.to_datetime(self.time)
        else:
            return None

    def create(self):
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.post('/measurement/measurements', self.to_json())

    def delete(self):
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.delete('/measurement/measurements/' + self.id)


class Measurements(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'measurement/measurements')

    def get(self, measurement_id):
        measurement = Measurement.from_json(self._get_object(measurement_id))
        measurement.c8y = self.c8y  # inject c8y connection into instance
        return measurement

    def select(self, type=None, source=None, fragment=None,
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """Lazy implementation."""
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        page_number = 1
        num_results = 1
        while True:
            try:
                results = [Measurement.from_json(x) for x in self._get_page(base_query, page_number)]
                if not results:
                    break
                for result in results:
                    result.c8y = self.c8y  # inject c8y connection into instance
                    if limit and num_results > limit:
                        raise StopIteration
                    num_results = num_results + 1
                    yield result
            except StopIteration:
                break
            page_number = page_number + 1

    def get_all(self, type=None, source=None, fragment=None,
                before=None, after=None, min_age=None, max_age=None, reverse=False,
                limit=None, page_size=1000):
        """Will get everything and return as a single result."""
        return [x for x in self.select(type=type, source=source, fragment=fragment,
                                       before=before, after=after, min_age=min_age, max_age=max_age,
                                       reverse=reverse, limit=limit, page_size=page_size)]

    def get_last(self, type=None, source=None, fragment=None, before=None, min_age=None):
        """Will just get the last available measurement."""
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, min_age=min_age, reverse=True, block_size=1)
        m = Measurement.from_json(self._get_page(base_query, "1")['measurements'][0])
        m.c8y = self.c8y  # inject c8y connection into instance
        return m

    def create(self, *measurements):
        self._create(lambda m: m.to_json(), *measurements)

