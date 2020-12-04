# Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

from datetime import datetime, timedelta, timezone
from dateutil import parser
from copy import copy
from urllib.parse import urlencode


class _DictWrapper(object):

    def __init__(self, dictionary, on_update=None):
        self.__dict__['items'] = dictionary
        self.__dict__['on_update'] = on_update

    def has(self, name):
        return name in self.items

    def __getattr__(self, name):
        item = self.items[name]
        return item if not isinstance(item, dict) else _DictWrapper(item, self.on_update)

    def __setattr__(self, name, value):
        if self.on_update:
            self.on_update()
        self.items[name] = value


class _DateUtil(object):

    @staticmethod
    def to_timestring(dt: datetime):
        return dt.isoformat(timespec='milliseconds')

    @staticmethod
    def to_datetime(string):
        return parser.parse(string)

    @staticmethod
    def now():
        return datetime.now(timezone.utc)

    @staticmethod
    def ensure_timestring(time):
        if isinstance(time, datetime):
            if not time.tzinfo:
                raise ValueError("A specified datetime needs to be timezone aware.")
            return _DateUtil.to_timestring(time)
        return time  # assuming it is a timestring

    @staticmethod
    def ensure_timedelta(time):
        if not isinstance(time, timedelta):
            raise ValueError("A specified duration needs to be a timedelta object.")
        return time


class _WithUpdatableAttributes(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._updated_fields = None

    def get_updates(self):
        return list(self._updated_fields)

    def _signal_updated_field(self, name):
        if not self._updated_fields:
            self._updated_fields = {name}
        else:
            self._updated_fields.add(name)
        if '+full_json+' in self.__dict__:
            del self.__dict__['+full_json+']
        if '+diff_json+' in self.__dict__:
            del self.__dict__['+diff_json+']


class _DatabaseObject(_WithUpdatableAttributes):

    def __init__(self, c8y=None):
        super().__init__()
        # the object id can only be set manually, e.g. when building an instance from json
        self.c8y = c8y
        self.id = None

    def _assert_c8y(self):
        if not self.c8y:
            raise ValueError("Cumulocity connection reference must be set to allow direct database access.")

    def _assert_id(self):
        if not self.id:
            raise ValueError("The object ID must be set to allow direct object access.")


class _WithUpdatableFragments(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # the object id can only be set manually, e.g. when building an instance from json
        self._updated_fields = None  # todo: why is this necessary to have?
        self._updated_fragments = None
        self.fragments = {}

    def add_attribute(self, name, value):
        self.fragments[name] = value
        self._signal_updated_fragment(name)

    def add_fragment(self, name, **kwargs):
        """Append a custom fragment to the object."""
        self.fragments[name] = kwargs
        self._signal_updated_fragment(name)
        return self

    def add_fragments(self, *fragments):
        """Bulk append a collection of fragments."""
        # fragments might be given as a list, not argument vector
        if len(fragments) == 1 and isinstance(fragments[0], list):
            return self.add_fragments(*fragments[0])
        for f in fragments:
            self.fragments[f.name] = f.items
            self._signal_updated_fragment(f.name)
        return self

    def __getattr__(self, name):
        """Directly access a specific fragment."""
        # A fragment is a simple dictionary. By wrapping it into the _DictWrapper class
        # it is ensured that the same access behaviour is ensured on all levels.
        # All updated anywhere within the dictionary tree will be reported as an update
        # to this instance.
        # If the element is not a dictionary, it can be returned directly
        item = self.fragments[name]
        return item if not isinstance(item, dict) else \
            _DictWrapper(self.fragments[name], lambda: self._signal_updated_fragment(name))

    def has(self, fragment_name):
        """Check whether a specific fragment is defined."""
        return fragment_name in self.fragments

    def get_updates(self):
        return list(self._updated_fields) + list(self._updated_fragments)

    def _signal_updated_fragment(self, name):
        if not self._updated_fragments:
            self._updated_fragments = {name}
        else:
            self._updated_fragments.add(name)
        if '+full_json+' in self.__dict__:
            del self.__dict__['+full_json+']
        if '+diff_json+' in self.__dict__:
            del self.__dict__['+diff_json+']


class _DatabaseObjectWithFragments(_WithUpdatableFragments, _DatabaseObject):

    def __init__(self, c8y=None):
        super().__init__(c8y)


class _DatabaseObjectParser(object):

    def __init__(self, mapping):
        self.__to_json = mapping
        self.__to_python = {v: k for k, v in mapping.items()}
        self.__full_json_repr = None
        self.__diff_json_repr = None

    def from_json(self, obj_json, new_obj):
        for json_key, field_name in self.__to_python.items():
            if json_key in obj_json:
                new_obj.__dict__[field_name] = obj_json[json_key]
        return new_obj

    def to_full_json(self, obj, ignore_list=None):
        repr_key = '+full_json+'+str(ignore_list)+'+'
        if not ignore_list:
            ignore_list = []
        if repr_key not in obj.__dict__:
            obj_json = {}
            for name, value in obj.__dict__.items():
                if name not in ignore_list:
                    if value and name in self.__to_json:
                        obj_json[self.__to_json[name]] = value
            obj.__dict__[repr_key] = obj_json
        return obj.__dict__[repr_key]

    def to_diff_json(self, obj):
        """Convert a database object to a JSON representation considering only updated fields.

        Updated fields need to be signaled via the _signal_updated_field method. The signaled
        name is extracted from the object fields. For this to function the field name needs to
        be identical to the signaled name.

        The formatted JSON string is stored within the object reference for performance reasons.
        """
        if '+diff_json+' not in obj.__dict__:
            obj_json = {}
            if obj._updated_fields:
                for name in obj._updated_fields:
                    obj_json[self.__to_json[name]] = obj.__dict__[name]
            obj.__dict__['+diff_json+'] = obj_json
        return obj.__dict__['+diff_json+']


class _DatabaseObjectWithFragmentsParser(_DatabaseObjectParser):

    def __init__(self, to_json_mapping, no_fragments_list):
        super().__init__(to_json_mapping)
        self.__ignore_set = set(no_fragments_list + list(to_json_mapping.values()))

    def from_json(self, obj_json, new_obj):
        new_obj = super().from_json(obj_json, new_obj)
        new_obj.fragments = self.__parse_fragments(obj_json)
        return new_obj

    def to_full_json(self, obj, ignore_list=None):
        obj_json = super().to_full_json(obj, ignore_list)
        obj_json.update(self.__format_fragments(obj))
        return obj_json

    def to_diff_json(self, obj):
        obj_json = super().to_diff_json(obj)
        obj_json.update(self.__format_updated_fragments(obj))
        return obj_json

    def __parse_fragments(self, obj_json):
        return {name: body for name, body in obj_json.items() if name not in self.__ignore_set}

    @staticmethod
    def __format_fragments(obj):
        return {name: fragment for name, fragment in obj.fragments.items()}

    @staticmethod
    def __format_updated_fragments(obj):
        if not obj._updated_fragments:
            return {}
        return {name: fragment for name, fragment in obj.fragments.items() if name in obj._updated_fragments}


class _UpdatableProperty(object):

    def __init__(self, name=None):
        self.name = name

    def __get__(self, obj, _):
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        obj._signal_updated_field(self.name)
        obj.__dict__[self.name] = value

    def __delete__(self, obj):
        obj._signal_updated_field(self.name)
        obj.__dict__[self.name] = None


class _UpdatableThingProperty(object):

    def __init__(self, prop_name, orig_name):
        self.prop_name = prop_name
        self.orig_name = orig_name
        self._updatable = None

    def __get__(self, obj, _):
        print('get ' + self.prop_name)
        if not self._updatable:
            def on_update(n1, n2):
                if not obj.__dict__[n1]:  # has not been preserved
                    obj.__dict__[n2] = copy(obj.__dict__[n1])
            self._updatable = _UpdatableThing(obj.__dict__[self.prop_name],
                                              lambda: on_update(self.prop_name, self.orig_name))
        return self._updatable

    def __set__(self, obj, value):
        if not obj.__dict__[self.orig_name]:  # has not been preserved
            obj.__dict__[self.orig_name] = copy(obj.__dict__[self.prop_name])
        obj.__dict__[self.prop_name] = value

    @staticmethod
    def _preserve_original_set(obj, name, orig_name):
        if not obj.__dict__[orig_name]:
            obj.__dict__[orig_name] = set(obj.__dict__[name])


class _UpdatableSetProperty(object):

    def __init__(self, prop_name, orig_name):
        self.prop_name = prop_name
        self.orig_name = orig_name

    def __get__(self, obj, _):
        self._preserve_original(obj)
        return obj.__dict__[self.prop_name]

    def __set__(self, obj, value):
        assert isinstance(value, set)
        self._preserve_original(obj)
        obj.__dict__[self.prop_name] = value

    def __delete__(self, obj):
        self._preserve_original(obj)
        obj.__dict__[self.prop_name] = None

    def _preserve_original(self, obj):
        if not obj.__dict__[self.orig_name]:
            obj.__dict__[self.orig_name] = set(obj.__dict__[self.prop_name])


class _UpdatableSet(set):

    def __init__(self, data=None):
        super().__init__(data)
        self.is_updated = False

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):  # it's a function
            def func(*args, **kwargs):
                return attr(*args, **kwargs)
            self.is_updated = True
            return func
        else:
            return attr


class _UpdatableThing:

    def __init__(self, thing, on_access):
        self.on_access = on_access
        self.thing = thing

    def __getattribute__(self, name):
        print('getattr ' + name)
        attr = object.__getattribute__(object.__getattribute__(self, 'thing'), name)
        if hasattr(attr, '__call__'):  # it's a function
            def func(*args, **kwargs):
                return attr(*args, **kwargs)
            object.__getattribute__(self, 'on_access')()
            return func
        else:
            return attr


class _Query(object):  # todo: better name

    def __init__(self, c8y, resource: str):
        self.c8y = c8y
        self.resource = _Query.__prepare_resource(resource)
        self.object_name = self.resource.split('/')[-1]

    @staticmethod
    def __prepare_resource(resource: str):
        """Ensure that the resource string starts with a slash and ends without."""
        return '/' + resource.strip('/')

    @staticmethod
    def __prepare_query_parameters(type=None, name=None, fragment=None, source=None,
                                   before=None, after=None, min_age=None, max_age=None,
                                   reverse=None, page_size=None, **kwargs):
        # min_age/max_age should be timedelta objects that can be used for
        # alternative calculation of the before/after parameters
        if min_age:
            if before:
                raise ValueError("Only one of 'min_age' and 'before' query parameters must be used.")
            min_age = _DateUtil.ensure_timedelta(min_age)
            before = _DateUtil.now() - min_age
        if max_age:
            if after:
                raise ValueError("Only one of 'max_age' and 'after' query parameters must be used.")
            max_age = _DateUtil.ensure_timedelta(max_age)
            after = _DateUtil.now() - max_age

        # before/after can also be datetime objects,
        # if so they need to be timezone aware
        before = _DateUtil.ensure_timestring(before)
        after = _DateUtil.ensure_timestring(after)

        params = {k: v for k, v in {'type': type, 'name': name,
                                    'source': source, 'fragmentType': fragment,
                                    'dateFrom': after, 'dateTo': before, 'revert': str(reverse),
                                    'pageSize': page_size}.items() if v}
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return params

    def _build_object_path(self, object_id):
        return self.resource + '/' + str(object_id)

    def _build_base_query(self, **kwargs):
        params = _Query.__prepare_query_parameters(**kwargs)
        return self.resource + '?' + urlencode(params) + '&currentPage='

    def _get_object(self, object_id):
        return self.c8y.get(self._build_object_path(object_id))

    def _get_page(self, base_query, page_number):
        result_json = self.c8y.get(base_query + str(page_number))
        return result_json[self.object_name]

    def _create(self, jsonify_func, *objects):
        for o in objects:
            self.c8y.post(self.resource, jsonify_func(o))

    def delete(self, *object_ids):
        for object_id in object_ids:
            self.c8y.delete(self.resource + '/' + str(object_id))
