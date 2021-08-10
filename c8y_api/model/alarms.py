# Copyright (c) 2021 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._base import CumulocityResource, SimpleObject, ComplexObject
from c8y_api.model._parser import ComplexObjectParser
from c8y_api.model._util import _DateUtil


class Alarm(ComplexObject):
    """ Represent an instance of an alarm object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Alarms API. Use this class to create new or update Alarm objects.

    See also: https://cumulocity.com/guides/reference/alarms/#alarm
    """

    __RESOURCE = '/alarm/alarms/'

    __parser = ComplexObjectParser({
        'id': 'id',
        'type': 'type',
        'time': 'time',
        'text': 'text',
        # 'source': 'source/id'   - cannot be parsed automatically
        'creation_time': 'creationTime',
        '_u_status': 'status',
        '_u_severity': 'severity',
        'count': 'count',
        'first_occurrence': 'firstOccurrenceTime'},
        ['self', 'source'])

    def __init__(self, c8y=None, type=None, time=None, source=None,  # noqa (type)
                 text=None, status=None, severity=None):
        """ Create a new Alarm object.

        :param c8y:  Cumulocity connection reference; needs to be set for the
            direct manipulation (create, delete) to function
        :param type:   Alarm type
        :param time:   Datetime string or Python datetime object. A given
            datetime string needs to be in standard ISO format incl. timezone:
            YYYY-MM-DD'T'HH:MM:SS.SSSZ as it is returned by the Cumulocity REST
            API. A given datetime object needs to be timezone aware.
            For manual construction it is recommended to specify a datetime
            object as the formatting of a time string is never checked for
            performance reasons.
        :param source:  Device ID which this alarm is for
        :param text:  Alarm description text
        :param status:  Alarm status
        :param severity:  Alarm severity
        :returns:  Alarm object
        """
        super().__init__(c8y=c8y)
        self.type = type
        self.source = source
        self.text = text
        self.creation_time = None
        self._u_status = status
        self._u_severity = severity
        self.count = 0
        self.first_occurrence = None
        # The time can either be set as string (e.g. when read from JSON) or
        # as a datetime object. It will be converted to string immediately
        # as there is no scenario where a manually created object won't be
        # written to Cumulocity anyways
        self.time = _DateUtil.ensure_timestring(time)
        # trigger update status of defined updatable fields
        if status:
            self.status = status
        if severity:
            self.severity = severity

    status = SimpleObject.UpdatableProperty('_u_status')
    severity = SimpleObject.UpdatableProperty('_u_severity')

    @classmethod
    def from_json(cls, alarm_json):
        """ Build a new Alarm instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        :param alarm_json:  JSON object (nested dictionary)
            representing a alarm within Cumulocity
        :returns:  Alarm object
        """
        obj = cls.__parser.from_json(alarm_json, Alarm())
        obj.source = alarm_json['source']['id']
        obj.id = alarm_json['id']
        return obj

    def to_json(self):
        """ Convert the instance to JSON.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        :returns:  JSON object (nested dictionary)
        """
        obj_json = self.__parser.to_full_json(self)
        if self.source:
            obj_json['source'] = {'id': self.source}
        return obj_json

    def to_diff_json(self):
        """ Convert the changes made to this instance to a JSON representation.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        :returns:  JSON object (nested dictionary)
        """
        obj_json = self.__parser.to_diff_json(self)
        return obj_json

    @property
    def datetime(self):
        """ Convert the alarm's time to a Python datetime object.

        :returns:  Standard Python datetime object
        """
        return super()._to_datetime(self.time)

    def create(self):
        """ Create a new representation of this object within the database.

        This function can be called multiple times to create multiple
        instances of this object with different ID.

        :returns:  A fresh Alarm instance representing the created object
            within the database. This instance can be used to get at the ID
            of the new Alarm object.

        See also function Alarms.create which doesn't parse the result.
        """
        self._assert_c8y()
        result_json = self.c8y.post(self.__RESOURCE, self.to_json())
        result = Alarm.from_json(result_json)
        result.c8y = self.c8y
        return result

    def update(self):
        """ Write changes to the database.

        :returns:  A fresh Alarm instance representing the updated object
            within the database.

        See also function Alarms.update which doesn't parse the result.
        """
        self._assert_c8y()
        self._assert_id()
        result_json = self.c8y.put(self.__RESOURCE + self.id, self.to_diff_json())
        result = Alarm.from_json(result_json)
        result.c8y = self.c8y
        return result

    def apply_to(self, other_id):
        """ Apply changes made to this object to another object in the database.

        :param other_id:  Database ID of the Alarm to update.
        :returns:  A fresh Alarm instance representing the updated object
            within the database.

        See also function Alarms.apply_to which doesn't parse the result.
        """
        self._assert_c8y()
        # if no field was updated, apparently the entire object should
        # be applied, so we signal updates ourselves by touching all updatable fields
        # put diff json to another object (by ID)
        result_json = self.c8y.put(self.__RESOURCE + other_id, self.to_diff_json())
        result = Alarm.from_json(result_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        """ Delete this object within the database.

        An alarm is identified through its type and source. These fields
        must be defined for this to function. This is always the case if
        the instance was built by the API.

        See also functions Alarms.delete and Alarms.delete_by
        """
        self._assert_c8y()
        if not self.type:
            raise ValueError("The alarm type must be set to allow unambiguous identification.")
        if not self.source:
            raise ValueError("The alarm source must be set to allow unambiguous identification.")
        self.c8y.alarms.delete_by(type=self.type, source=self.source)


class Alarms(CumulocityResource):
    """ A wrapper for the standard Alarms API.

    This class can be used for get, search for, create, update and
    delete alarms within the Cumulocity database.

    See also: https://cumulocity.com/guides/reference/alarms/#alarm
    """

    __RESOURCE = '/alarm/alarms/'

    def __init__(self, c8y):
        super().__init__(c8y, self.__RESOURCE)

    def get(self, id):  # noqa (id)
        """Retrieve a specific object from the database.

        :param id:  The database ID of the object
        :returns:  An Alarm instance representing the object in the database.
        """
        obj = Alarm.from_json(self._get_object(id))
        obj.c8y = self.c8y  # inject c8y connection into instance
        return obj

    def select(self, type=None, source=None, fragment=None, # noqa (type)
               status=None, severity=None, resolved=None,
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """ Query the database for alarms and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Alarm type
        :param source:  Database ID of a source device
        :param fragment:  Name of a present custom/standard fragment
        :param status:  Alarm status
        :param severity:  Alarm severity
        :param resolved:  Whether the alarm status is CLEARED
        :param before:  Datetime object or ISO date/time string. Only
            alarms assigned to a time before this date are returned.
        :param after:  Datetime object or ISO date/time string. Only
            alarms assigned to a time after this date are returned.
        :param min_age:  Timedelta object. Only alarms of at least
            this age are returned.
        :param max_age:  Timedelta object. Only alarms with at most
            this age are returned.
        :param reverse:  Invert the order of results, starting with the
            most recent one.
        :param limit:  Limit the number of results to this number.
        :param page_size:  Define the number of alarms which are read (and
            parsed in one chunk). This is a performance related setting.

        :returns:  Iterable of Alarm objects
        """
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            status=status, severity=severity, resolved=resolved,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        return super()._iterate(base_query, limit, Alarm.from_json)

    def get_all(self, type=None, source=None, fragment=None, # noqa (type)
                status=None, severity=None, resolved=None,
                before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """ Query the database for alarms and return the results as list.

        This function is a greedy version of the select function. All
        available results are read immediately and returned as list.

        :returns:  List of Alarm objects
        """
        return list(self.select(type=type, source=source, fragment=fragment,
                                status=status, severity=severity, resolved=resolved,
                                before=before, after=after, min_age=min_age, max_age=max_age, reverse=reverse,
                                limit=limit, page_size=page_size))

    def create(self, *alarms):
        """ Create alarm objects within the database.

        :param alarms:  collection of Alarm instances
        :returns:  None
        """
        super()._create(Alarm.to_json, *alarms)

    def update(self, *alarms):
        """ Write changes to the database.

        :param alarms:  A collection of Alarm objects
        :returns: None

        See also function Alarm.update which parses the result.
        """
        super()._update(Alarm.to_diff_json, *alarms)

    def apply_to(self, alarm, *alarm_ids):
        """ Apply changes made to a single instance to other objects in the database.

        :param alarm:  An Alarm object serving as model for the update
        :param alarm_ids:  A collection of database IDS of alarms
        :returns: None

        See also function Alarm.apply_to which parses the result.
        """
        super()._apply_to(Alarm.to_diff_json, alarm, *alarm_ids)

    def delete(self, *alarms):
        """ Delete alarm objects within the database.

        Note: within Cumulocity alarms are identified by type and source.
        These fields must be defined within the provided objects for this
        operation to function.

        :param alarms:  Collection of Alarm instances.
        :returns:  None
        """
        for a in alarms:
            a.delete()

    def delete_by(self, type=None, source=None, fragment=None,  # noqa (type)
                  status=None, severity=None, resolved=None,
                  before=None, after=None, min_age=None, max_age=None):
        """ Query the database and delete matching alarms.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Alarm type
        :param source:  Database ID of a source device
        :param fragment:  Name of a present custom/standard fragment
        :param status:  Alarm status
        :param severity:  Alarm severity
        :param resolved:  Whether the alarm status is CLEARED
        :param before:  Datetime object or ISO date/time string. Only
            alarms assigned to a time before this date are returned.
        :param after:  Datetime object or ISO date/time string. Only
            alarms assigned to a time after this date are returned.
        :param min_age:  Timedelta object. Only alarms of at least
            this age are returned.
        :param max_age:  Timedelta object. Only alarms with at most
            this age are returned.

        :returns: None
        """
        # build a base query
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            status=status, severity=severity, resolved=resolved,
                                            before=before, after=after, min_age=min_age, max_age=max_age)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)
