# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._util import _Query, _DatabaseObject, _DatabaseObjectParser


class Event(_DatabaseObject):

    __parser = _DatabaseObjectParser({
        'id': 'id',
        'type': 'type',
        'category': 'category',
        'time': 'time',
        'creation_time': 'creationTime',
        # 'source': 'source/id'
        'text': 'text'})

    def __init__(self, c8y=None, type=None, category=None, time=None, source=None, text=None):
        super().__init__(c8y=c8y)
        self.type = type
        self.category = category
        self.time = time
        self.source = source
        self.text = text
        self.creation_time = None

    @classmethod
    def from_json(cls, json_obj):
        obj = cls.__parser.from_json(json_obj, Event())
        obj.source = json_obj['source']['id']
        obj.id = json_obj['id']
        return obj


class Events(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'event/events')

    def select(self, type=None, category=None, source=None, fragment=None, # noqa (type)
               before=None, after=None, min_age=None, max_age=None, reverse=False,
               limit=None, page_size=1000):
        base_query = self._build_base_query(type=type, category=category, source=source, fragment=fragment,
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
