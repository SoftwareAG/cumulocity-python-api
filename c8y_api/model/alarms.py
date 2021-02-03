# Copyright (c) 2021 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._util import _Query, _UpdatableProperty, \
    _DatabaseObjectWithFragments, _DatabaseObjectWithFragmentsParser


class Alarm(_DatabaseObjectWithFragments):
    """
    Represent an instance of an Alarm object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Alarms API. Use this class to create new or update Alarm objects.

    See also: https://cumulocity.com/guides/reference/alarms/#alarm
    """

    __RESOURCE = '/alarm/alarms/'

    __parser = _DatabaseObjectWithFragmentsParser({
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

    def __init__(self, c8y=None, type=None, time=None, source=None, text=None, status=None, severity=None):
        super().__init__(c8y=c8y)
        self.type = type
        self.time = time
        self.source = source
        self.text = text
        self.creation_time = None
        self._u_status = status
        self._u_severity = severity
        self.count = 0
        self.first_occurrence = None
        # trigger update status of defined updatable fields
        if status:
            self.status = status
        if severity:
            self.severity = severity

    status = _UpdatableProperty('_u_status')
    severity = _UpdatableProperty('_u_severity')

    @classmethod
    def from_json(cls, json_obj):
        obj = cls.__parser.from_json(json_obj, Alarm())
        obj.source = json_obj['source']['id']
        obj.id = json_obj['id']
        return obj

    def to_json(self):
        obj_json = self.__parser.to_full_json(self)
        if self.source:
            obj_json['source'] = {'id': self.source}
        return obj_json

    def to_diff_json(self):
        obj_json = self.__parser.to_diff_json(self)
        return obj_json

    def create(self):
        """Create a new representation of this object within the database.

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
        """Write changes to the database.

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
        """Apply changes made to this object to another object in the database.

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
        """Delete this object within the database.

        For this to function, the object ID must be defined. This is
        always the case if the instance was built by the API.

        See also functions Alarms.delete and Alarms.delete_by
        """
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete(self.__RESOURCE + self.id)


class Alarms(_Query):

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
        """Execute a query and iterate over the results.

        See also function get_all which collects all results as a list..
        """
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            status=None, severity=None, resolved=None,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        page_number = 1
        num_results = 1
        while True:
            try:
                results = [Alarm.from_json(x) for x in self._get_page(base_query, page_number)]
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

    def get_all(self, type=None, source=None, fragment=None, # noqa (type)
                status=None, severity=None, resolved=None,
                before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """Execute a query and return all results as a list.

        See also function select which does not return a list but an Iterable.
        """
        return [x for x in self.select(type=type, source=source, fragment=fragment,
                                       status=None, severity=None, resolved=None,
                                       before=before, after=after, min_age=min_age, max_age=max_age, reverse=reverse,
                                       limit=limit, page_size=page_size)]

    def create(self, *alarms):
        """Create alarm objects within the database.

        :param alarms:  collection of Alarm instances
        :returns:  None
        """
        super()._create(Alarm.to_json, *alarms)

    def update(self, *alarms):
        super()._update(Alarm.to_diff_json, *alarms)

    def apply_to(self, alarm, *alarm_ids):
        """"""
        super()._apply_to(Alarm.to_diff_json, alarm, *alarm_ids)

    # function delete is defined in super class

    def delete_by(self, type=None, source=None, fragment=None,  # noqa (type)
                  status=None, severity=None, resolved=None,
                  before=None, after=None, min_age=None, max_age=None):
        # build a base query
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            status=None, severity=None, resolved=None,
                                            before=before, after=after, min_age=min_age, max_age=max_age)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)
