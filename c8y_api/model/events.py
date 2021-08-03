# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._base import _Query, _DatabaseObjectWithFragments
from c8y_api.model._parser import _DatabaseObjectWithFragmentsParser
from c8y_api.model._updatable import _UpdatableProperty


class Event(_DatabaseObjectWithFragments):
    """ Represent an instance of an event object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Events API. Use this class to create new or update Event objects.

    See also: https://cumulocity.com/guides/reference/events/#event
    """

    __RESOURCE = '/event/events/'

    __parser = _DatabaseObjectWithFragmentsParser({
        'id': 'id',
        'type': 'type',
        'time': 'time',
        '_u_text': 'text',
        # 'source': 'source/id'
        'creation_time': 'creationTime'},
        ['self', 'source'])

    def __init__(self, c8y=None, type=None, time=None, source=None, text=None):  # noqa (type)
        """ Create a new Event object.

        Custom fragments can be added to the object after creation, using
        the add_fragment function.

        :param c8y:  Cumulocity connection reference; needs to be set for
            the direct manipulation (create, delete) to function.
        :param type:   Event type
        :param time:   Datetime string or Python datetime object. A given
            datetime string needs to be in standard ISO format incl. timezone:
            YYYY-MM-DD'T'HH:MM:SS.SSSZ as it is returned by the Cumulocity
            REST API. A given datetime object needs to be timezone aware.
            For manual construction it is recommended to specify a datetime
            object as the formatting of a time string is never checked for
            performance reasons.
        :param source:  Device ID which this Event is for
        :param text:  Event description text

        :returns:  Event object
        """
        super().__init__(c8y=c8y)
        self.type = type
        self.time = time
        self.source = source
        self._u_text = text
        self.creation_time = None
        # trigger update status of defined updatable fields
        if text:
            self.text = text

    text = _UpdatableProperty('_u_text')

    @classmethod
    def from_json(cls, event_json):
        """ Build a new Event instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        :param event_json:  JSON object (nested dictionary)
            representing a event within Cumulocity
        :returns:  Event object
        """
        obj = cls.__parser.from_json(event_json, Event())
        obj.source = event_json['source']['id']
        obj.id = event_json['id']
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
        """ Convert the changes made to this instance to a JSON
        representation.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        :returns:  JSON object (nested dictionary)
        """
        obj_json = self.__parser.to_diff_json(self)
        return obj_json

    @property
    def datetime(self):
        """ Convert the event's time to a Python datetime object.

        :returns:  Standard Python datetime object
        """
        return super()._to_datetime(self.time)

    def create(self):
        """ Create a new representation of this object within the database.

        This function can be called multiple times to create multiple
        instances of this object with different ID.

        :returns:  A fresh Event instance representing the created object
            within the database. This instance can be used to get at the ID
            of the new Event object.

        See also function Events.create which doesn't parse the result.
        """
        self._assert_c8y()
        result_json = self.c8y.post(self.__RESOURCE, self.to_json())
        result = Event.from_json(result_json)
        result.c8y = self.c8y
        return result

    def update(self):
        """ Write changes to the database.

        :returns:  A fresh Event instance representing the updated object
            within the database.

        See also function Events.update which doesn't parse the result.
        """
        self._assert_c8y()
        self._assert_id()
        result_json = self.c8y.put(self.__RESOURCE + self.id, self.to_diff_json())
        result = Event.from_json(result_json)
        result.c8y = self.c8y
        return result

    def apply_to(self, other_id):
        """ Apply changes made to this object to another object in the
            database.

        :param other_id:  Database ID of the event to update.
        :returns:  A fresh Event instance representing the updated object
            within the database.

        See also function Events.apply_to which doesn't parse the result.
        """
        self._assert_c8y()
        # put diff json to another object (by ID)
        result_json = self.c8y.put(self.__RESOURCE + other_id, self.to_diff_json())
        result = Event.from_json(result_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        """ Delete this object within the database.

        The database ID must be defined for this to function.

        See also functions Events.delete and Events.delete_by
        """
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete(self.__RESOURCE + self.id)


class Events(_Query):
    """ A wrapper for the standard Events API.

    This class can be used for get, search for, create, update and
    delete events within the Cumulocity database.

    See also: https://cumulocity.com/guides/reference/events/#event
    """

    def __init__(self, c8y):
        super().__init__(c8y, '/event/events')

    def get(self, id):  # noqa (id)
        """ Retrieve a specific object from the database.

        :param id:  The database ID of the object
        :returns:  An Event instance representing the object in the database.
        """
        event_object = Event.from_json(self._get_object(id))
        event_object.c8y = self.c8y  # inject c8y connection into instance
        return event_object

    def select(self, type=None, source=None, fragment=None, # noqa (type)
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """ Query the database for events and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Event type
        :param source:  Database ID of a source device
        :param fragment:  Name of a present custom/standard fragment
        :param before:  Datetime object or ISO date/time string. Only
            events assigned to a time before this date are returned.
        :param after:  Datetime object or ISO date/time string. Only
            events assigned to a time after this date are returned.
        :param min_age:  Timedelta object. Only events of at least
            this age are returned.
        :param max_age:  Timedelta object. Only events with at most
            this age are returned.
        :param reverse:  Invert the order of results, starting with the
            most recent one.
        :param limit:  Limit the number of results to this number.
        :param page_size:  Define the number of events which are read (and
            parsed in one chunk). This is a performance related setting.

        :returns:  Iterable of Event objects
        """
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        return super()._iterate(base_query, limit, Event.from_json)

    def get_all(self, type=None, source=None, fragment=None, # noqa (type)
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        """ Query the database for events and return the results as list.

        This function is a greedy version of the select function. All
        available results are read immediately and returned as list.

        :returns:  List of Event objects
        """
        return list(self.select(type=type, source=source, fragment=fragment,
                                before=before, after=after, min_age=min_age, max_age=max_age, reverse=reverse,
                                limit=limit, page_size=page_size))

    def create(self, *events):
        """Create event objects within the database.

        :param events:  collection of Event instances
        :returns:  None
        """
        super()._create(Event.to_json, *events)

    def update(self, *events):
        """ Write changes to the database.

        :param events:  A collection of Event objects
        :returns: None

        See also function Event.update which parses the result.
        """
        super()._update(Event.to_diff_json, *events)

    def apply_to(self, event, *event_ids):
        """ Apply changes made to a single instance to other objects in the
        database.

        :param event:  An Event object serving as model for the update
        :param event_ids:  A collection of database IDS of events
        :returns: None

        See also function Event.apply_to which parses the result.
        """
        super()._apply_to(Event.to_diff_json, event, *event_ids)

    # delete function is defined in super class

    def delete_by(self, type=None, source=None, fragment=None,  # noqa (type)
                  before=None, after=None, min_age=None, max_age=None):
        """ Query the database and delete matching events.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Event type
        :param source:  Database ID of a source device
        :param fragment:  Name of a present custom/standard fragment
        :param before:  Datetime object or ISO date/time string. Only
            events assigned to a time before this date are returned.
        :param after:  Datetime object or ISO date/time string. Only
            events assigned to a time after this date are returned.
        :param min_age:  Timedelta object. Only events of at least
            this age are returned.
        :param max_age:  Timedelta object. Only events with at most
            this age are returned.

        :returns: None
        """
        # build a base query
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after, min_age=min_age, max_age=max_age)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)
