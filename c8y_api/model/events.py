# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._util import _Query, _UpdatableProperty, _NotUpdatableProperty, \
    _DatabaseObjectWithFragments, _DatabaseObjectWithFragmentsParser


class Event(_DatabaseObjectWithFragments):

    __parser = _DatabaseObjectWithFragmentsParser({
        'id': 'id',
        'type': 'type',
        'time': 'time',
        '_u_text': 'text',
        # 'source': 'source/id'
        'creation_time': 'creationTime'},
        ['self', 'source'])

    def __init__(self, c8y=None, type=None, time=None, source=None, text=None):
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
    def from_json(cls, json_obj):
        obj = cls.__parser.from_json(json_obj, Event())
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
        """

        :return Event:  A fresh Event instance representing what was created
            within the database. This instance can be used to get at the ID
            of the new Event object.
        :see also
        """
        self._assert_c8y()
        result_json = self.c8y.post('/event/events', self.to_json())
        result = Event.from_json(result_json)
        result.c8y = self.c8y
        return result

    def update(self):
        self._assert_c8y()
        self._assert_id()
        result_json = self.c8y.put('/event/events/' + self.id, self.to_diff_json())
        result = Event.from_json(result_json)
        result.c8y = self.c8y
        return result

    def apply_to(self, other_id):
        """Apply the changed made to this object to another object in the database.



        :param
        """
        self._assert_c8y()
        # if no field was updated, apparently the entire object should
        # be applied, so we signal updates ourselves by touching all updatable fields
        # put diff json to another object (by ID)
        result_json = self.c8y.put('/event/events/' + other_id, self.to_diff_json())
        result = Event.from_json(result_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete('/event/events/' + self.id)


class Events(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, '/event/events')

    def get(self, event_id):
        event_object = Event.from_json(self._get_object(event_id))
        event_object.c8y = self.c8y  # inject c8y connection into instance
        return event_object

    def select(self, type=None, source=None, fragment=None, # noqa (type)
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after, min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        page_number = 1
        num_results = 1
        while True:
            try:
                results = [Event.from_json(x) for x in self._get_page(base_query, page_number)]
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
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        return [x for x in self.select(type=type, source=source, fragment=fragment,
                                       before=before, after=after, min_age=min_age, max_age=max_age, reverse=reverse,
                                       limit=limit, page_size=page_size)]

    def create(self, *events):
        """Create event objects within the database.

        :param events:  collection of Event instances
        :returns:  None
        """
        for event in events:
            self.c8y.post('/event/events', event.to_json())

    def update(self, *events):
        for event in events:
            self.c8y.put('/event/events/' + event.id, event.to_diff_json())

    def apply_to(self, event, *event_ids):
        """"""
        diff_json = event.to_diff_json()
        for eid in event_ids:
            self.c8y.put('/event/events/' + eid, diff_json)

    def delete(self, *events):
        """Delete one or more events.

        The events can be specified as instances of Event (then, the id field
        needs to be defined) or simply as ID (integers or strings).
        :param events:  events objects within Cumulocity specified as Event
            instances or by ID
        :returns:  None
        """
        try:
            event_ids = [e.id for e in events]
        except AttributeError:
            event_ids = events
        for eid in event_ids:
            self.c8y.delete('/event/events/' + eid)

    def delete_by(self, type=None, source=None, fragment=None,  # noqa (type)
                  before=None, after=None, min_age=None, max_age=None):
        # build a base query
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after, min_age=min_age, max_age=max_age)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)
