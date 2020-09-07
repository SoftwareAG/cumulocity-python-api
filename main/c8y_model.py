from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from dateutil import parser

from log_util import error


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


class _DatabaseObject(object):

    def __init__(self, c8y=None):
        # the object id can only be set manually, e.g. when building an instance from json
        self.c8y = c8y
        self.id = None
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


class Count(Value):
    def __init__(self, value):
        super().__init__(value, '#')


class Fragment(object):

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


class _DatabaseObjectWithFragments(_DatabaseObject):

    def __init__(self, c8y=None):
        # the object id can only be set manually, e.g. when building an instance from json
        super().__init__(c8y)
        self._updated_fragments = None
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

    def __getattr__(self, item):
        """Directly access a specific fragment."""
        # A fragment is a simple dictionary. By wrapping it into the _DictWrapper class
        # it is ensured that the same access behaviour is ensured on all levels.
        # All updated anywhere within the dictionary tree will be reported as an update
        # to this instance.
        # If the element is not a dictionary, it can be returned directly
        return item if not isinstance(self.fragments[item], dict) else \
            _DictWrapper(self.fragments[item], lambda: self._signal_updated_fragment(item))

    def has(self, fragment_name):
        """Check whether a specific fragment is defined."""
        return fragment_name in self.fragments

    def flag_update(self, name):
        self._signal_updated_fragment(name)

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
        return {name: fragment for name, fragment in obj.fragments.items() if name in obj._updated_fragments}


class _UpdatableProperty(object):

    def __init__(self, name=None):
        self.name = name

    def __get__(self, obj, _):
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        obj._signal_updated_field(self.name)
        obj.__dict__[self.name] = value


class User(_DatabaseObject):

    __parser = _DatabaseObjectParser({
            'user_id': 'id',
            '_u_email': 'email',
            '_u_enabled': 'enabled',  # bool
            '_u_username': 'userName',
            '_u_display_name': 'displayName',
            '_last_password_change': 'lastPasswordChange'})

    def __init__(self, c8y=None, user_id=None, email=None, enabled=True, username=None, display_name=None):
        super().__init__(c8y)
        self.user_id = user_id
        self._u_email = email
        self._u_enabled = enabled
        self._u_username = username
        self._u_display_name = display_name
        # todo: groups
        # todo: roles
        self._last_password_change = None

    username = _UpdatableProperty(name='_u_username')
    display_name = _UpdatableProperty(name='_u_display_name')
    email = _UpdatableProperty(name='_u_email')
    enabled = _UpdatableProperty(name='_u_enabled')

    @property
    def last_password_change(self):
        # hint: could be cached, but it rarely is accessed multiple times
        return _DateUtil.to_datetime(self._last_password_change)

    @classmethod
    def from_json(cls, user_json):
        return cls.__parser.from_json(user_json, User())

    def to_full_json(self):
        return self.__parser.to_full_json(self)

    def to_diff_json(self):
        return self.__parser.to_diff_json(self)

    def add_role(self, role_id):
        pass


class Group(_DatabaseObject):

    __parser = _DatabaseObjectParser({
            'id': 'id',
            'name': 'name',
            'description': 'description'})

    def __init__(self, c8y=None):
        super().__init__(c8y)
        self.id = None
        self.name = None
        self.description = None

    @classmethod
    def from_json(cls, group_json):
        return cls.__parser.from_json(group_json, Group())


class ManagedObject(_DatabaseObjectWithFragments):
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

    __parser = _DatabaseObjectWithFragmentsParser(
        {'id': 'id',
         '_u_type': 'type',
         '_u_name': 'name',
         '_u_owner': 'owner',
         '_creation_time': 'creationTime',
         '_update_time': 'lastUpdated'},
        ['self',
         'childDevices', 'childAssets', 'childAdditions',
         'deviceParents', 'assetParents', 'additionParents'])

    def __init__(self, c8y=None, type=None, name=None, owner=None):
        """Create a new ManagedObject from scratch."""
        super().__init__(c8y)
        # a direct update to the property backends is necessary to bypass
        # the update notification; everything specified within the constructor is
        # not considered to be an update
        self._u_type = type
        self._u_name = name
        self._u_owner = owner
        self._creation_time = None
        self._update_time = None
        self.child_devices = []
        self.child_assets = []
        self.child_additions = []
        self.parent_devices = []
        self.parent_assets = []
        self.parent_additions = []
        self.is_device = False

    type = _UpdatableProperty(name='_u_type')
    name = _UpdatableProperty(name='_u_name')
    owner = _UpdatableProperty(name='_u_owner')

    @classmethod
    def from_json(cls, object_json):
        mo = cls.__parser.from_json(object_json, ManagedObject())
        # todo: references look different
        mo.child_devices = object_json['childDevices']['references']
        mo.child_assets = object_json['childAssets']['references']
        mo.child_additions = object_json['childAdditions']['references']
        mo.parent_devices = object_json['deviceParents']['references']
        mo.parent_assets = object_json['assetParents']['references']
        mo.parent_additions = object_json['additionParents']['references']
        return mo

    def to_full_json(self):
        return self.__parser.to_full_json(self)

    def to_diff_json(self):
        return self.__parser.to_diff_json(self)

    @property
    def creation_time(self):
        return _DateUtil.to_datetime(self._creation_time)

    @property
    def update_time(self):
        return _DateUtil.to_datetime(self._update_time)

    def store(self):
        """Will write the object to the database as a new instance."""
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        return self.c8y.post('/inventory/managedObjects', self.to_full_json())

    def update(self, object_id=None):
        """
        Write updated fields and fragments to database.

        The id argument is optional if it is set within the object. The same update can be written to multiple
        different objects if the id argument is used.
        """
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.put('/inventory/managedObjects/' +
                     str(object_id if object_id else self.id), self.to_diff_json())

    def delete(self):
        """Will delete the object within the database."""
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.delete('/inventory/managedObjects/' + str(self.id))


class Device(ManagedObject):

    def __init__(self, c8y=None, type=None, name=None, owner=None):
        super().__init__(c8y=c8y, type=type, name=name, owner=owner)
        self.is_device = True

    def to_full_json(self):
        object_json = super().to_full_json()
        object_json['c8y_IsDevice'] = {}
        return object_json

    def delete(self):
        """Delete both the device managed object as well as the device credentials within the database."""
        assert self.name, "Device name must be defined for deletion."
        device_username = 'device_' + self.name
        super().delete()
        self.c8y.users.delete(device_username)


class Binary(ManagedObject):
    def __init__(self, c8y=None, filename=None, media_type=None):
        super().__init__(c8y=c8y, type=media_type, name=filename)


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


class ExternalId(object):

    def __init__(self, c8y=None, external_id=None, external_type=None, managed_object_id=None):
        self.c8y = c8y
        self.external_id = external_id
        self.external_type = external_type
        self.managed_object_id = managed_object_id

    @staticmethod
    def _from_json(identity_json):
        external_type = identity_json['type']
        external_id = identity_json['externalId']
        managed_object_id = identity_json['managedObject']['id']
        return ExternalId(external_id=external_id, external_type=external_type, managed_object_id=managed_object_id)

    def create(self):
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        body_json = {
            'externalId': self.external_id,
            'type': self.external_type}
        self.c8y.post(f'/identity/globalIds/{self.managed_object_id}/externalIds', body_json)

    def delete(self):
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.delete(f'/identity/externalIds/{self.external_type}/{self.external_id}')

    def get_managed_object_id(self):
        if self.managed_object_id is None:
            self.managed_object_id = self.c8y.get(f'/identity/externalIds/{self.external_type}/{self.external_id}')

        return self.managed_object_id

    def __str__(self):
        return str({
            'external_id': self.external_id,
            'external_type': self.external_type,
            'managed_object_id': self.managed_object_id
        })


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
            assert not before  # todo warning
            min_age = _DateUtil.ensure_timedelta(min_age)
            before = _DateUtil.now() - min_age
        if max_age:
            assert not after  # todo warning
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

    def _build_base_query(self, **kwargs):
        params = _Query.__prepare_query_parameters(**kwargs)
        return self.resource + '?' + urlencode(params) + '&currentPage='

    def _get_object(self, object_id):
        return self.c8y.get(self.resource + '/' + str(object_id))

    def _get_page(self, base_query, page_number):
        result_json = self.c8y.get(base_query + str(page_number))
        return result_json[self.object_name]

    def _create(self, jsonify_func, *objects):
        if len(objects) == 1 and isinstance(objects[0], list):
            self._create(jsonify_func, *objects)
        else:
            for o in objects:
                self.c8y.post(self.resource, jsonify_func(o))

    def delete(self, *object_ids):
        for object_id in object_ids:
            self.c8y.delete(self.resource + '/' + str(object_id))


class Inventory(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'inventory/managedObjects')

    def get(self, object_id):
        managed_object = ManagedObject.from_json(self._get_object(object_id))
        managed_object.c8y = self.c8y  # inject c8y connection into instance
        return managed_object

    def get_all(self, type=None, source=None, fragment=None, before=None, after=None, reverse=False, page_size=1000):
        return [x for x in self.select(type, source, fragment, before, after, reverse, page_size)]

    def select(self, type=None, source=None, fragment=None, before=None, after=None, reverse=False, page_size=1000):
        """Lazy implementation."""
        base_query = self._build_base_query(type=type, source=source, fragment=fragment,
                                            before=before, after=after,
                                            reverse=reverse, page_size=page_size)
        page_number = 1
        while True:
            # todo: it should be possible to stream the JSON content as well
            results = [ManagedObject.from_json(x) for x in self._get_page(base_query, page_number)]
            if not results:
                break
            for result in results:
                result.c8y = self.c8y  # inject c8y connection into instance
                yield result
            page_number = page_number + 1

    def create(self, *managed_objects):
        pass

    def update(self, object_id, object_model):
        pass


class DeviceInventory(Inventory):

    def delete(self, *device_ids):
        """Delete both the Device managed object as well as the registered device credentials from database."""
        pass


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


class Users(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'user/' + c8y.tenant_id + '/users')
        self.__groups = Groups(c8y)

    def get(self, user_id):
        """Retrieve a specific user.

        :param user_id The ID of the user (usually the mail address)
        :rtype User
        """
        user = User.from_json(self._get_object(user_id))
        user.c8y = self.c8y  # inject c8y connection into instance
        return user

    def add_roles(self, user_id, *role_ids):
        # todo: this would be an immediate action/write to database
        pass

    def select(self, username=None, groups=None):
        """Lazily select and yield User instances.

        The result can be limited by username (prefix) and/or group membership.

        :param username: A user's username or a prefix thereof
        :param groups: a scalar or list of int (actual group ID), string (group names),
            or actual Group instances
        :rtype Generator of Group instances
        """
        # group_list can be ints, strings (names) or Group objects
        # it needs to become a comma-separated string
        groups_string = None
        if groups:  # either non-empty list or scalar
            # ensure it's a list to allow
            if not isinstance(groups, list):
                groups = [groups]
            if isinstance(groups[0], int):
                groups_string = [str(i) for i in groups]
            elif isinstance(groups[0], Group):
                groups_string = [str(g.id) for g in groups]
            elif isinstance(groups[0], str):
                groups_string = [str(self.__groups.get(name).id) for name in groups]
            else:
                ValueError("Unable to identify type of given group identifiers.")
            groups_string = ','.join(groups_string)
        # lazily yield parsed objects page by page
        base_query = super()._build_base_query(username=username, groups=groups_string)
        page_number = 1
        while True:
            page_results = [User.from_json(x) for x in self._get_page(base_query, page_number)]
            if not page_results:
                break
            for user in page_results:
                user.c8y = self.c8y  # inject c8y connection into instance
                yield user
            page_number = page_number + 1

    def get_all(self, username=None, groups=None):
        """Select and retrieve User instances as list.

        The result can be limited by username (prefix) and/or group membership.

        :param username: A user's username or a prefix thereof
        :param groups: a scalar or list of int (actual group ID), string (group names),
            or actual Group instances
        :rtype List of Group
        """
        return [x for x in self.select(username, groups)]

    def create(self):
        pass


class Groups(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'user/' + c8y.tenant_id + '/groups')
        self.__groups_by_name = None

    def reset_caches(self):
        """Reset internal caching.

        This resets the following caches:
          * Groups by name (used for all group lookup by name)
        """
        self.__groups_by_name = None

    def get(self, group_id):
        """Retrieve a specific group.

        Note:  The C8Y REST API does not support direct query by name. Hence,
        searching by name will actually retrieve all available groups and
        return the matching ones.
        These groups will be cached internally for subsequent calls.

        See also method :py:meth:reset_caches

        :param group_id  a scalar int (actual group ID) or string (group name)
        :rtype Group
        """
        if isinstance(group_id, int):
            return Group.from_json(super()._get_object(group_id))
        # else: find group by name
        if not self.__groups_by_name:
            self.__groups_by_name = {g.name: g for g in self.get_all()}
        return self.__groups_by_name[group_id]

    def get_all(self):
        """Retrieve all available groups.

        :rtype List of Group
        """
        base_query = self._build_base_query()
        result = []
        page_number = 1
        while True:
            xs = self._get_page(base_query, page_number)
            if not xs:
                break
            for x in xs:
                g = Group.from_json(x)
                g.c8y = self.c8y
                result.append(g)
            page_number = page_number + 1
        return result


class Identity(object):
    # the Identity API of C8Y uses inconsistent resource paths and therefore
    # cannot use the generic _Query base class helper

    def __init__(self, c8y):
        self.c8y = c8y

    def create(self, external_id, external_type, managed_object_id):
        body_json = {
            'externalId': external_id,
            'type': external_type}
        self.c8y.post(f'/identity/globalIds/{managed_object_id}/externalIds', body_json)

    def delete(self, external_id, external_type):
        self.c8y.delete(f'/identity/externalIds/{external_type}/{external_id}')

    def get_managed_object_id(self, external_id, external_type):
        try:
            response = self.c8y.get(f'/identity/externalIds/{external_type}/{external_id}')
            return ExternalId._from_json(response)
        except KeyError:
            return None


class Binaries(object):
    def __init__(self, c8y):
        self.c8y = c8y

    def upload(self, binary_meta_information, file_path=None, file=None):
        assert isinstance(binary_meta_information, Binary)

        try:
            if file_path is not None:
                file = open(file_path, 'rb')
        except FileNotFoundError:
            error('File not found for file path: ', file_path)
            return

        if file is None:
            error('No File available to upload')
            return

        return self.c8y.post_file('/inventory/binaries', file, binary_meta_information)

    def update(self, binary_id, media_type, file_path=None, file=None):
        try:
            if not file_path:
                file = open(file_path, 'rb')
        except FileNotFoundError:
            error('File not found for file path: ', file_path)
            return

        if file:
            error('No File available to upload')
            return

        self.c8y.put_file(f'/inventory/binaries/{binary_id}', file, media_type)

    def delete(self, binary_id):
        self.c8y.delete(f'/inventory/binaries/{binary_id}')
