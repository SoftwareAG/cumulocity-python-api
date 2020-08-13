from datetime import datetime
from urllib.parse import urlencode
from c8y_api import __c8y, get, post, put, delete


class _DictWrapper:

    def __init__(self, dictionary, on_update=None):
        self.__dict__['items'] = dictionary
        self.__dict__['on_update'] = on_update

    def has(self, name):
        return name in self.items

    def __getattr__(self, name):
        print('get ' + name)
        item = self.items[name]
        return item if not isinstance(item, dict) else _DictWrapper(item, self.on_update)

    def __setattr__(self, name, value):
        print('set ' + name)
        if self.on_update:
            self.on_update()
        self.items[name] = value


class Fragment:

    def __init__(self, name, **kwargs):
        self.name = name
        self.items = kwargs

    @staticmethod
    def _from_json(name, body_json):
        f = Fragment(name)
        f.items = body_json
        return f

    def __getattr__(self, name):
        item = self.items[name]
        return item if not isinstance(item, dict) else _DictWrapper(item)

    def has(self, element_name):
        return element_name in self.items

    def add_element(self, name, element):
        self.items[name] = element
        return self


class __DatabaseObject:

    def __init__(self):
        # the object id can only be set manually, e.g. when building an instance from json
        self.id = None
        self._updated_fragments = None
        self._updated_fields = None
        self.fragments = {}

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

    # Thoughts regarding a direct assignment of fragments:
    # This would require to overload __setattr__ which makes everything VERY complicated. E.g. it would bypass
    # the property assignment and therefore everything needs to be handled within. It is also already called
    # during the constructor so fields may even not be defined yet.
    # def __setattr__(self, item, value):
    #     # check if it is a fragment
    #     if 'fragments' in self.__dict__:
    #         if item in self.fragments:
    #             self.fragments[item] = value
    #             self._signal_updated_fragment(item)
    #     object.__setattr__(self, item, value)
    #     self._signal_updated_field(item)

    def __getattr__(self, item):
        """Directly access a specific fragment."""
        # A fragment is a simple dictionary. By wrapping it into the _DictWrapper class
        # it is ensured that the same access behaviour is ensured on all levels.
        # All updated anywhere within the dictionary tree will be reported as an update
        # to this instance.
        # If the element is not a dictionary, it can be returned directly
        return item if not isinstance(self.fragments[item], dict) else _DictWrapper(self.fragments[item], lambda: self._signal_updated_fragment(item))

    def has(self, fragment_name):
        """Check whether a specific fragment is defined."""
        return fragment_name in self.fragments

    def flag_update(self, name):
        self._signal_updated_fragment(name)

    def get_updates(self):
        return list(self._updated_fields) + list(self._updated_fragments)

    def _signal_updated_field(self, name):
        if not self._updated_fields:
            self._updated_fields = {name}
        else:
            self._updated_fields.add(name)

    def _signal_updated_fragment(self, name):
        if not self._updated_fragments:
            self._updated_fragments = {name}
        else:
            self._updated_fragments.add(name)

    @staticmethod
    def _parse_fragments(object_json, builtin_fragments):
        return  {name: body for name, body in object_json.items() if name not in builtin_fragments}


class ManagedObject(__DatabaseObject):

    """

    Updates to both fields and fragments are tracked automatically and will

        mo.owner = 'admin@cumulocity.com'
        mo.c8y_CustomFragment.region = 'EMEA'
        mo.add_fragment('c8y_CustomValue', value=12, uom='units')

    Note: This does not work if a fragment is actually a field, not a structure own it's own.
    A direct assignment to such a value fragment, like

        mo.c8y_CustomReferences = [1, 2, 3]

    is currently not supported nicely as it will not be recognised as an update. A manual update flagging is
    required:

        mo.c8y_CustomReferences = [1, 2, 3]
        mo.flag_update('c8y_CustomReferences')
    """


    # todo: del mo.c8y_IsDevice  - how does this need to be written to DB? With a POST on the ID?

    __BUILTIN_FRAGMENTS = ['id', 'self', 'type', 'name', 'owner',
                           'creationTime', 'lastUpdated',
                           'childDevices', 'childAssets', 'childAdditions',
                           'deviceParents', 'assetParents', 'additionParents']

    def __init__(self, type=None, name=None, owner=None):
        """Create a new ManagedObject from scratch."""
        super().__init__()
        # a direct update to the property backends is necessary to bypass
        # the update notification; everything specified within the constructor is
        # not considered to be an update
        self.__type = type
        self.__name = name
        self.__owner = owner
        self.__creation_time = None
        self.__creation_datetime = None
        self.__update_time = None
        self.__update_datetime = None
        self.child_devices = []
        self.child_assets = []
        self.child_additions = []
        self.parent_devices = []
        self.parent_assets = []
        self.parent_additions = []
        self.is_device = False

    @staticmethod
    def _from_json(object_json):
        type = object_json['type'] if 'type' in object_json else None
        name = object_json['name'] if 'name' in object_json else None
        owner = object_json['owner']
        mo = ManagedObject(type=type, name=name, owner=owner)
        mo.id = object_json['id']
        mo.__creation_time = object_json['creationTime']
        mo.__update_time = object_json['lastUpdated']
        # todo: references look different
        mo.child_devices = object_json['childDevices']['references']
        mo.child_assets = object_json['childAssets']['references']
        mo.child_additions = object_json['childAdditions']['references']
        mo.parent_devices = object_json['deviceParents']['references']
        mo.parent_assets = object_json['assetParents']['references']
        mo.parent_additions = object_json['additionParents']['references']
        mo.fragments = ManagedObject._parse_fragments(object_json, ManagedObject.__BUILTIN_FRAGMENTS)
        return mo

    def _to_full_json(self):
        object_json = {}
        if self.__type:
            object_json['type'] = self.__type
        if self.__name:
            object_json['name'] = self.__name
        if self.__owner:
            object_json['owner'] = self.__owner
        # todo: references
        for name, fragment in self.fragments.items():
            object_json[name] = fragment
        return object_json

    def _to_diff_json_(self):
        object_json = {}
        if self._updated_fields:
            for name in self._updated_fields:
                object_json[name] = self.__dict__[name]
        # todo: references
        if self._updated_fragments:
            for name in self._updated_fragments:
                object_json[name] = self.fragments[name]
        return object_json

    @property
    def type(self):
        return self.__type if self.__type else ''

    @type.setter
    def type(self, value):
        self.__type = value
        self._signal_updated_field('type')

    @property
    def name(self):
        return self.__name if self.__name else ''

    @name.setter
    def name(self, value):
        self.__name = value
        self._signal_updated_field('name')

    @property
    def owner(self):
        return self.__owner

    @owner.setter
    def owner(self, value):
        self.__owner = value
        self._signal_updated_field('owner')

    @property
    def creation_time(self):
        if not self.__creation_time:
            if not self.__creation_datetime:
                return None
            self.__creation_time = self.__creation_datetime.isoformat(timespec='milliseconds')
        return self.__creation_datetime

    @property
    def creation_datetime(self):
        if not self.__creation_datetime:
            if not self.__creation_time:
                return None
            self.__creation_datetime = datetime.fromisoformat(self.__creation_time)
        return self.__creation_datetime

    @property
    def update_time(self):
        if not self.__update_time:
            if not self.__update_datetime:
                return None
            self.__update_time = self.__update_datetime.isoformat(timespec='milliseconds')
        return self.__update_datetime

    @property
    def update_datetime(self):
        if not self.__update_datetime:
            if not self.__update_time:
                return None
            self.__update_datetime = datetime.fromisoformat(self.__update_time)
        return self.__update_datetime

    def store(self):
        """Will write the object to the database as a new instance."""
        post('/inventory/managedObjects', self._to_full_json())

    def update(self, id=None):
        """
        Write updated fields and fragments to database.

        The id argument is optional if it is set within the object. The same update can be written to multiple
        different objects if the id argument is used.
        """
        put('/inventory/managedObjects/' + str(id if id else self.id), self._to_diff_json_())

    def delete(self):
        """Will delete the object within the database."""
        delete('/inventory/managedObjects/' + str(self.id))


class Device(ManagedObject):

    def __init__(self, type=None, name=None, owner=None):
        super().__init__(type, name, owner)
        self.is_device = True

    def _to_full_json(self):
        object_json = super()._to_full_json()
        object_json['c8y_IsDevice'] = {}
        return object_json


class Measurement(__DatabaseObject):

    __BUILTIN_FRAGMENTS = ['type', 'id', 'source', 'time', 'self']

    def __init__(self, type, source, time=None):
        super().__init__(type)
        self.id = ''
        self.type = type
        self.source = source
        self.__datetime = time if isinstance(time, datetime) else None
        self.__time = time if isinstance(time, str) else None
        self.fragments = None

    @staticmethod
    def _from_json(measurement_json):
        type = measurement_json['type']
        source = measurement_json['source']['id']
        time = measurement_json['time']
        m = Measurement(type, source, time)
        m.id = measurement_json['id']
        m.fragments = Measurement._parse_fragments(measurement_json, Measurement.__BUILTIN_FRAGMENTS)
        return m

    # the __getattr__ function is overwritten to return a wrapper that doesn't signal updates
    # (because Measurements are not updated, can only be created from scratch)
    def __getattr__(self, item):
        return _DictWrapper(self.fragments[item], on_update=None)

    @property
    def datetime(self):
        if not self.__datetime:
            if not self.__time:
                self.now()
            self.__datetime = datetime.fromisoformat(self.__time)
        return self.__datetime

    @property
    def time(self):
        if not self.__time:
            if not self.__datetime:
                self.now()
            self.__time = self.__datetime.isoformat(timespec='milliseconds')
        return self.__time

    def now(self):
        self.__datetime = datetime.now()
        self.__time = self.__datetime.isoformat(timespec='milliseconds')

    def store(self):
        if not self.__time:
            self.now()
        body_json = {
            'type': self.type,
            'source': {'id': self.source},
            'time': self.__time}
        body_json.update({name: body for name, body in self.fragments.items()})
        post('/measurement/measurements', body_json)

    def delete(self):
        delete('/measurement/measurements/' + self.id)


class _C8Y_API:

    @staticmethod
    def __map_params(type=None, name=None, fragment=None, source=None,
                     before=None, after=None, reverse=None, page_size=None, **kwargs):
        params = {k: v for k, v in {'type': type, 'source': source, 'fragmentType': fragment,
                                    'dateFrom': after, 'dateTo': before, 'reverse': str(reverse),
                                    'pageSize': page_size}.items() if v}
        params.update(**kwargs)
        return params

    @staticmethod
    def _build_base_query(base, **kwargs):
        params = _C8Y_API.__map_params(**kwargs)
        return base + '?' + urlencode(params) + '&currentPage='


class ManagedObjects(_C8Y_API):

    @staticmethod
    def get(id):
        object_json = get('/inventory/managedObjects/' + str(id))
        return ManagedObject._from_json(object_json)

    @staticmethod
    def get_all(type="", source="", fragment="", before="", after="", reverse=False, page_size=1000):
        pass

    @staticmethod
    def select(type="", source="", fragment="", before="", after="", reverse=False, page_size=1000):
        """Lazy implementation."""
        base_query = ManagedObjects.__build_base_query(type=type, source=source, fragment=fragment,
                                                       before=before, after=after,
                                                       reverse=reverse, page_size=page_size)
        page_number = 1
        while True:
            results = [ManagedObject._from_json(x) for x in ManagedObjects.__get_page(base_query, page_number)]
            if not results:
                break
            for result in results:
                yield result
            page_number = page_number + 1

    @staticmethod
    def store(*managed_objects):
        pass

    @staticmethod
    def __build_base_query(**kwargs):
        return _C8Y_API._build_base_query('/inventory/managedObjects', **kwargs)

    @staticmethod
    def __get_page(base_query, page):
        result = get(base_query + str(page))
        return result['managedObjects']


class Measurements(_C8Y_API):

    @staticmethod
    def get(id=''):
        pass

    @staticmethod
    def select(type="", source="", fragment="", before="", after="", reverse=False, page_size=1000):
        """Lazy implementation."""
        base_query = Measurements.__build_base_query(type=type, source=source, fragment=fragment,
                                                     before=before, after=after,
                                                     reverse=reverse, block_size=page_size)
        page_number = 1
        while True:
            results = [Measurement._from_json(x) for x in Measurements.__get_page(base_query, page_number)]
            if not results:
                break
            for result in results:
                yield result
            page_number = page_number + 1

    @staticmethod
    def get_all(type="", source="", fragment="", before="", after="", reverse=False, block_size=1000):
        """Will get everything and return as a single result."""
        return [x for x in Measurements.select(type, source, fragment, before, after, reverse, block_size)]

    @staticmethod
    def get_last(type="", source="", fragment=""):
        """Will just get the last available measurement."""
        query = Measurements.__build_base_query(type=type, source=source, fragment=fragment, reverse=True, block_size=1)
        return Measurement._from_json(get(query + "0")['measurements'][0])

    @staticmethod
    def store(*measurements):
        if len(measurements) == 1 and isinstance(measurements[0], list):
            Measurements.store(*measurements)
        else:
            for m in measurements:
                m.store()

    @staticmethod
    def __build_base_query(type="", source="", fragment="", before="", after="", reverse=False, block_size=1000):
        # todo: before and after could be actual dates, not strings
        # prepare map of parameters (ignore None ones) to append
        params = {k: v for k, v in {'type': type, 'source': source, 'fragmentType': fragment,
                                    'dateFrom': after, 'dateTo': before, 'reverse': str(reverse),
                                    'pageSize': block_size}.items() if v}
        assert params  # there needs to be at least 1 param for the next line to make sense
        return '/measurement/measurements?' + urlencode(params) + '&currentPage='

    @staticmethod
    def __get_page(base_query, page):
        result = get(base_query + str(page))
        return result['measurements']

