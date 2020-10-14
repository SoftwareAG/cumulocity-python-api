from ._util import _DateUtil, _UpdatableProperty, _Query, \
    _DatabaseObjectWithFragments, _DatabaseObjectWithFragmentsParser, _DictWrapper
from c8y_api._util import error


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


class ManagedObjectReference(_DatabaseObjectWithFragments):
    __parser = _DatabaseObjectWithFragmentsParser(
        {'managedObject': 'managedObject'},
        [])

    def __init__(self, c8y=None, reference=None):
        super().__init__(c8y)
        self.add_fragment(name='managedObject', id=reference)

    @classmethod
    def from_json(cls, object_json):
        mor = cls.__parser.from_json(object_json, ManagedObjectReference())
        return mor

    def to_full_json(self):
        return self.__parser.to_full_json(self)

    def to_diff_json(self):
        return self.__parser.to_diff_json(self)


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

    def create(self):
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

    def add_child_asset(self, managed_object_child_id):
        """
        Add a child asset to this managed object.

        Provide the id of the managed object you want to add as a child asset
        """
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.post('/inventory/managedObjects/'+str(self.id)+"/childAssets", ManagedObjectReference(reference=managed_object_child_id).to_full_json())

    def add_child_device(self, managed_object_child_id):
        """
        Add a child device to this managed object.

        Provide the id of the managed object you want to add as a child device
        """
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.post('/inventory/managedObjects/'+str(self.id)+"/childDevice", ManagedObjectReference(reference=managed_object_child_id).to_full_json())

    def add_child_addition(self, managed_object_child_id):
        """
        Add a child addition to this managed object.

        Provide the id of the managed object you want to add as a child addition
        """
        assert self.c8y, "Cumulocity connection reference must be set to allow direct database access."
        self.c8y.post('/inventory/managedObjects/'+str(self.id)+"/childAdditions", ManagedObjectReference(reference=managed_object_child_id).to_full_json())


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


class Inventory(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'inventory/managedObjects')

    def get(self, object_id):
        managed_object = ManagedObject.from_json(self._get_object(object_id))
        managed_object.c8y = self.c8y  # inject c8y connection into instance
        return managed_object

    def get_all(self, type=None, fragment=None, page_size=1000):
        return [x for x in self.select(type, fragment, page_size)]

    def select(self, type=None, fragment=None, page_size=1000):
        """Lazy implementation."""
        base_query = self._build_base_query(type=type, fragment=fragment, page_size=page_size)
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

    def create(self, *managed_objects: ManagedObject):
        """Create managed objects in database.

        Takes a list of managed objects and writes them to the database one by
        one using the Cumulocity connection of this Inventory instance.

        :param managed_objects  a list of ManagedObject instances
        """
        super()._create(lambda mo: mo._to_full_json(), *managed_objects)

    def update(self, object_model, *object_ids):
        """Apply a change to a number of existing objects.

        Takes a list of ID of already existing managed objects and applies a
        change within the database to all of them one by one.

        Uses the Cumulocity connection of this Inventiry instance.

        :param object_model  ManagedObject instance holding the change structure
            like an added fragment of updated value.
        :param object_ids  a list of ID of already existing ManagedObject
            instances.
        """
        if object_model.id:
            raise ValueError("The change model must not specify an ID.")
        update_json = object_model._to_diff_json()
        for object_id in object_ids:
            self.c8y.put(self.resource + '/' + str(object_id), update_json)


class DeviceInventory(Inventory):

    def delete(self, *device_ids):
        """Delete both the Device managed object as well as the registered device credentials from database."""
        pass


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


