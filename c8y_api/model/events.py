# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# Alarm and Event are similar by design, hence
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Generator, List

from c8y_api._base_api import CumulocityRestApi
from c8y_api.model._base import CumulocityResource, SimpleObject, ComplexObject
from c8y_api.model._parser import ComplexObjectParser
from c8y_api.model._util import _DateUtil


class Event(ComplexObject):
    """Represent an instance of an event object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Events API. Use this class to create new or update Event objects.

    See also: https://cumulocity.com/api/#tag/Events
    """

    _resource = '/event/events'
    # _accept can remain default
    _parser = ComplexObjectParser({
        'type': 'type',
        'time': 'time',
        '_u_text': 'text',
        'creation_time': 'creationTime',
        'updated_time': 'lastUpdated',
        }, ['source'])

    def __init__(self, c8y: CumulocityRestApi = None, type: str = None, time: str | datetime = None,
                 source: str = None, text: str = None, **kwargs):  # noqa (type)
        """Create a new Event object.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            type (str):  Event type
            time (str|datetime):  Date/time of the event. Can be provided as
                timezone-aware datetime object or formatted string (in
                standard ISO format incl. timezone: YYYY-MM-DD'T'HH:MM:SS.SSSZ
                as it is returned by the Cumulocity REST API).
                Use 'now' to set  to current datetime in UTC.
            source (str):  ID of the device which this event is raised by
            text (str):  Event test/description
            kwargs:  Additional arguments are treated as custom fragments
        """
        super().__init__(c8y=c8y, **kwargs)
        self.type = type
        self.time = _DateUtil.ensure_timestring(time)
        self.source = source
        self._u_text = text
        self.creation_time = None
        self.updated_time = None

    text = SimpleObject.UpdatableProperty('_u_text')

    @property
    def datetime(self) -> datetime:
        """Convert the event's time to a Python datetime object.

        Returns:
            Standard Python datetime object
        """
        return super()._to_datetime(self.time)

    @property
    def creation_datetime(self) -> datetime:
        """Convert the event's creation time to a Python datetime object.

        Returns:
            Standard Python datetime object
        """
        return super()._to_datetime(self.creation_time)

    @property
    def updated_datetime(self) -> datetime:
        """Convert the alarm's last updated time to a Python datetime object.

        Returns:
            Standard Python datetime object for the alarm's last updated time.
        """
        return super()._to_datetime(self.updated_time)

    @classmethod
    def from_json(cls, json: dict) -> Event:
        # (no doc update required)
        obj = super()._from_json(json, Event())
        obj.source = json['source']['id']
        return obj

    def to_json(self, only_updated: bool = False) -> dict:
        # (no doc update required)
        # creation time is always excluded
        obj_json = super()._to_json(only_updated, exclude={'creation_time'})
        # source needs to be set manually, but it cannot be updated
        if not only_updated and self.source:
            obj_json['source'] = {'id': self.source}
        return obj_json

    def create(self) -> Event:
        """Create the Event within the database.

        Returns:
            A fresh Event object representing what was
            created within the database (including the ID).
        """
        return super()._create()

    def update(self) -> Event:
        """Update the Event within the database.

        Note: This will only send changed fields to increase performance.

        Returns:
            A fresh Event object representing what the updated
            state within the database (including the ID).
        """
        return super()._update()

    def delete(self):
        """Delete the Event within the database."""
        super()._delete()

    def apply_to(self, other_id: str) -> Event:
        """Apply changes made to this object to another object in the
            database.

        Args:
            other_id (str):  Database ID of the event to update.

        Returns:
            A fresh Event instance representing the updated object
            within the database.

        See also function `Events.apply_to` which doesn't parse the result.
        """
        return super()._apply_to(other_id)


class Events(CumulocityResource):
    """Provides access to the Events API.

    This class can be used for get, search for, create, update and
    delete events within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Events
    """

    def __init__(self, c8y):
        super().__init__(c8y, '/event/events')

    def get(self, event_id: str) -> Event:  # noqa (id)
        """Retrieve a specific object from the database.

        Args:
            event_id (str):  The database ID of the event

        Returns:
            An Event instance representing the object in the database.
        """
        event_object = Event.from_json(self._get_object(event_id))
        event_object.c8y = self.c8y  # inject c8y connection into instance
        return event_object

    def select(self, type: str = None, source: str = None, fragment: str = None,  # noqa (type)
               before: str | datetime = None, after: str | datetime = None,
               created_before: str | datetime = None, created_after: str | datetime = None,
               updated_before: str | datetime = None, updated_after: str | datetime = None,
               min_age: timedelta = None, max_age: timedelta = None,
               reverse: bool = False, limit: int = None, page_size: int = 1000) -> Generator[Event]:
        """Query the database for events and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        Args:
            type (str):  Event type
            source (str):  Database ID of a source device
            fragment (str):  Name of a present custom/standard fragment
            before (str|datetime):  Datetime object or ISO date/time string. Only
                events assigned to a time before this date are returned.
            after (str|datetime):  Datetime object or ISO date/time string. Only
                events assigned to a time after this date are returned.
            created_before (str|datetime):  Datetime object or ISO date/time string.
                Only events changed at a time before this date are returned.
            created_after (str|datetime):  Datetime object or ISO date/time string.
                Only events changed at a time after this date are returned.
            updated_before (str|datetime):  Datetime object or ISO date/time string.
                Only events changed at a time before this date are returned.
            updated_after (str|datetime):  Datetime object or ISO date/time string.
                Only events changed at a time after this date are returned.
            min_age (timedelta): Minimum age for selected events.
            max_age (timedelta): Maximum age for selected events.
            reverse (bool): Invert the order of results, starting with the
                most recent one.
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator for Event objects
        """
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after,
                                            created_before=created_before, created_after=created_after,
                                            updated_before=updated_before, updated_after=updated_after,
                                            min_age=min_age, max_age=max_age,
                                            reverse=reverse, page_size=page_size)
        return super()._iterate(base_query, limit, Event.from_json)

    def get_all(self, type: str = None, source: str = None, fragment: str = None,  # noqa (type)
               before: str | datetime = None, after: str | datetime = None,
               created_before: str | datetime = None, created_after: str | datetime = None,
               updated_before: str | datetime = None, updated_after: str | datetime = None,
               min_age: timedelta = None, max_age: timedelta = None,
               reverse: bool = False, limit: int = None, page_size: int = 1000) -> List[Event]:
        """Query the database for events and return the results as list.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        See `select` for a documentation of arguments.

        Returns:
            List of Event objects
        """
        return list(self.select(type=type, source=source, fragment=fragment,
                                before=before, after=after,
                                created_before=created_before, created_after=created_after,
                                updated_before=updated_before, updated_after=updated_after,
                                min_age=min_age, max_age=max_age,
                                reverse=reverse,
                                limit=limit, page_size=page_size))

    def create(self, *events: Event):
        """Create event objects within the database.

        Note: If not yet defined, this will set the event date to now in
            each of the given event objects.

        Args:
            events (*Event):  Collection of Event instances
        """
        for e in events:
            if not e.time:
                e.time = _DateUtil.to_timestring(datetime.utcnow())
        super()._create(Event.to_full_json, *events)

    def update(self, *events: Event):
        """Write changes to the database.

        Args:
            events (*Event):  Collection of Event instances
        """
        super()._update(Event.to_diff_json, *events)

    def apply_to(self, event: Event, *event_ids: str):
        """Apply changes made to a single instance to other objects in the
        database.

        Args:
            event (Event): Event used as model for the update
            event_ids (*Event):  Collection of ID of the events to update
        """
        super()._apply_to(Event.to_full_json, event, *event_ids)

    # delete function is defined in super class

    def delete_by(self, type: str = None, source: str = None, fragment: str = None,  # noqa (type)
               before: str | datetime = None, after: str | datetime = None,
               min_age: timedelta = None, max_age: timedelta = None):
        """Query the database and delete matching events.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        Args:
            type (str):  Event type
            source (str):  Database ID of a source device
            fragment (str):  Name of a present custom/standard fragment
            before (str|datetime):  Datetime object or ISO date/time string. Only
                events assigned to a time before this date are returned.
            after (str|datetime):  Datetime object or ISO date/time string. Only
                events assigned to a time after this date are returned.
            min_age (timedelta): Minimum age for selected events.
            max_age (timedelta): Maximum age for selected events.
        """
        # build a base query
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after, min_age=min_age, max_age=max_age)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)
