# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api._util import error
from c8y_api.model._util import _UpdatableProperty, _Query, _DatabaseObject,\
    _DatabaseObjectWithFragments, _DatabaseObjectWithFragmentsParser, _DictWrapper


class NamedObject(object):
    """ Represent a named object within the database.

    This class is used to model Cumulocity references.
    """
    def __init__(self, id=None, name=None):  # noqa
        """ Create a new instance.

        :param id:  Database ID of the object
        :param name:  Name of the object
        :returns:  New NamedObject instance
        """
        self.id = id
        self.name = name

    @classmethod
    def from_json(cls, object_json):
        """ Build a new instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        :param object_json:  JSON object (nested dictionary)
            representing a named object within Cumulocity
        :returns:  NamedObject instance
        """
        return NamedObject(id=object_json['id'], name=object_json.get('name', ''))

    def to_json(self):
        """ Convert the instance to JSON.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        :returns:  JSON object (nested dictionary)
        """
        return {'id': self.id, 'name': self.name}


class Fragment(object):
    """ Represent a custom fragment within database objects.

    This class is used by other classes to represent custom fragments
    within their data model.

    For example, every measurement contains such a fragment, holding
    the actual data points:
    :: json
        "pt_current": {
            "CURR": {
                "unit": "A",
                "value": 50
            }
        }

    A fragment has a name (*pt_current* in above example) and can virtually
    define any substructure.
    """
    def __init__(self, name, **kwargs):
        """ Create a new fragment.

        :param name:  Name of the fragment
        :param kwargs:  Named elements of the fragment. Each element
            can either be a simple value of a complex substructure
            modelled as nested dictionary.
        :returns:  New Fragment instance
        """
        self.name = name
        self.items = kwargs

    def __getattr__(self, name):
        """ Get a specific element of the fragment.

        :param name:  Name of the element
        :returns:  Value of the element. May be a simple value or a
            complex substructure defined as nested dictionary.
        """
        item = self.items[name]
        return item if not isinstance(item, dict) else _DictWrapper(item)

    def has(self, name):
        """ Check whether a specific element is defined.

        :param name:  Name of the element
        :returns:  True if the element is present, False otherwise
        """
        return name in self.items

    def add_element(self, name, element):
        """ Add an element.

        :param name:  Name of the element
        :param element:  Value of the element, either a simple value or
            a complex substructure defined as nested dictionary.
        :returns:  self
        """
        self.items[name] = element
        return self


class ManagedObject(_DatabaseObjectWithFragments):
    """ Represent a managed object within the database.

    Instances of this class are returned by functions of the corresponding
    Inventory API. Use this class to create new or update managed objects.

    Within Cumulocity a managed object is used to hold virtually any
    *additional* (apart from measurements, events and alarms) information.
    This custom information is modelled in *fragments*, named elements
    of any structure.

    Fragments are modelled as standard Python fields and can be accessed
    directly if the names & structures are known:
    :: python

        x = mo.c8y_CustomFragment.values.x

    Managed objects can be changed and such updates are written as
    *differences* to the database. The API does the tracking of these
    differences automatically - just use the ManagedObject class like
    any other Python class.
    :: python

        mo.owner = 'admin@cumulocity.com'
        mo.c8y_CustomFragment.region = 'EMEA'
        mo.add_fragment('c8y_CustomValue', value=12, uom='units')

    Note: This does not work if a fragment is actually a field, not a
    structure own it's own. A direct assignment to such a value fragment,
    like
    :: python

        mo.c8y_CustomReferences = [1, 2, 3]

    is currently not supported nicely as it will not be recognised as an
    update. A manual update flagging is required:
    :: python

        mo.c8y_CustomReferences = [1, 2, 3]
        mo.flag_update('c8y_CustomReferences')

    See also https://cumulocity.com/guides/reference/inventory/#managed-object
    """

    __RESOURCE = '/inventory/managedObjects/'

    _parser = _DatabaseObjectWithFragmentsParser(
        {'id': 'id',
         '_u_type': 'type',
         '_u_name': 'name',
         '_u_owner': 'owner',
         'creation_time': 'creationTime',
         'update_time': 'lastUpdated'},
        ['self',
         'childDevices', 'childAssets', 'childAdditions',
         'deviceParents', 'assetParents', 'additionParents'])

    def __init__(self, c8y=None, type=None, name=None, owner=None):  # noqa
        """ Create a new ManagedObject instance.

        Custom fragments can be added to the object after creation, using
        the add_fragment function.

        :param c8y:  Cumulocity connection reference; needs to be set for the
            direct manipulation (create, delete) to function
        :param type:   ManagedObject type
        :param name:   Descriptive name of the object
        :param owner:   User ID of the owner for this object

        :returns:  ManagedObject instance
        """
        super().__init__(c8y)
        # a direct update to the property backends is necessary to bypass
        # the update notification; everything specified within the constructor is
        # not considered to be an update
        self._u_type = type
        self._u_name = name
        self._u_owner = owner
        self.creation_time = None
        self.update_time = None
        self.child_devices = []
        self.child_assets = []
        """List of NamedObject references to child assets."""
        self.child_additions = []
        self.parent_devices = []
        self.parent_assets = []
        self.parent_additions = []
        self._object_path = None
        self.is_device = False
        self.is_device_group = False
        # trigger changes to updatable fields
        if type:
            self.type = type
        if name:
            self.name = name
        if owner:
            self.owner = owner

    type = _UpdatableProperty(name='_u_type')
    name = _UpdatableProperty(name='_u_name')
    owner = _UpdatableProperty(name='_u_owner')

    @classmethod
    def from_json(cls, object_json):
        """ Build a new ManagedObject instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        :param object_json:  JSON object (nested dictionary)
            representing a managed object within Cumulocity
        :returns:  ManagedObject object
        """
        mo = cls._parser.from_json(object_json, ManagedObject())
        mo.child_devices = cls._parse_references(object_json['childDevices'])
        mo.child_assets = cls._parse_references(object_json['childAssets'])
        mo.child_additions = cls._parse_references(object_json['childAdditions'])
        return mo

    @classmethod
    def _parse_references(cls, base_json):
        return [NamedObject.from_json(j['managedObject']) for j in base_json['references']]

    def to_json(self):
        """ Convert the instance to JSON.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        Note: This JSON representation does not include child assets,
        child devices and child additions.

        :returns:  JSON object (nested dictionary)
        """
        return self._parser.to_full_json(self)

    def to_diff_json(self):
        """ Convert the changes made to this instance to a JSON representation.

        The JSON format produced by this function is what is used by the
        Cumulocity REST API.

        Note: This JSON representation does not include child assets,
        child devices and child additions, even if they changed.

        :returns:  JSON object (nested dictionary)
        """
        return self._parser.to_diff_json(self)

    @property
    def creation_datetime(self):
        """ Convert the object's creation to a Python datetime object.

        :returns:  Standard Python datetime object
        """
        return super()._to_datetime(self.creation_time)

    @property
    def update_datetime(self):
        """ Convert the object's creation to a Python datetime object.

        :returns:  Standard Python datetime object
        """
        return super()._to_datetime(self.update_time)

    def create(self):
        """ Create a new representation of this object within the database.

        This function can be called multiple times to create multiple
        instances of this object with different ID.

        :returns:  A fresh ManagedObject instance representing the created
            object within the database. This instance can be used to get
            at the ID of the new managed object.

        See also function Inventory.create which doesn't parse the result.
        """
        super()._assert_c8y()
        result_json = self.c8y.post(self.__RESOURCE, self.to_json())
        result = ManagedObject.from_json(result_json)
        result.c8y = self.c8y
        return result

    def update(self):
        """ Write changes to the database.

        :returns:  A fresh ManagedObject instance representing the updated
            object within the database.

        See also function Inventory.update which doesn't parse the result.
        """
        super()._assert_c8y()
        super()._assert_id()
        result_json = self.c8y.put(self._build_object_path(), self.to_diff_json())
        result = ManagedObject.from_json(result_json)
        result.c8y = self.c8y
        return result

    def apply_to(self, other_id):
        """ Apply changes made to this object to another object in the
        database.

        :param other_id:  Database ID of the event to update.
        :returns:  A fresh ManagedObject instance representing the updated
            object within the database.

        See also function Inventory.apply_to which doesn't parse the result.
        """
        self._assert_c8y()
        # put diff json to another object (by ID)
        result_json = self.c8y.put(self.__RESOURCE + other_id, self.to_diff_json())
        result = ManagedObject.from_json(result_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        """ Delete this object within the database.

        The database ID must be defined for this to function.

        :returns:  None

        See also function Inventory.delete to delete multiple objects.
        """
        super()._assert_c8y()
        super()._assert_id()
        self.c8y.delete(self._build_object_path())

    def add_child_asset(self, child_id):
        """ Link a child asset to this managed object.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        :param child_id:  object ID of the child asset
        :returns:  None
        """
        self._add_any_child('/childAssets', child_id)

    def add_child_device(self, child_id):
        """ Link a child device to this managed object.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        :param child_id:  object ID of the child device
        :returns:  None
        """
        self._add_any_child('/childDevices', child_id)

    def add_child_addition(self, child_id):
        """ Link a child addition to this managed object.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        :param child_id:  object ID of the child addition
        :returns:  None
        """
        self._add_any_child('/childAdditions', child_id)

    def _add_any_child(self, path, child_id):
        self._assert_c8y()
        self._assert_id()
        self.c8y.post(self._build_object_path() + path,
                      self._build_managed_object_reference(child_id))

    def _build_object_path(self):
        if not self._object_path:
            self._object_path = self.__RESOURCE + self.id
        return self._object_path

    @classmethod
    def _build_managed_object_reference(cls, object_id):
        return {'managedObject': {'id': object_id}}


class Device(ManagedObject):
    """ Represent an instance of a Device object within Cumulocity.

    Instances of this class are returned by functions of the corresponding
    DeviceInventory API. Use this class to create new or update Device
    objects.

    Device objects are regular managed objects with additional standardized
    fragments and fields.

    See also https://cumulocity.com/guides/reference/inventory/#managed-object
        https://cumulocity.com/guides/reference/device-management/
    """

    def __init__(self, c8y=None, type=None, name=None, owner=None):  # noqa
        """ Create a new Device instance.

        A Device object will always have a `c8y_IsDevice` fragment.
        Additional custom fragments can be added to the object after
        creation, using the add_fragment function.

        :param c8y:  Cumulocity connection reference; needs to be set for the
            direct manipulation (create, delete) to function
        :param type:   ManagedObject type
        :param name:   Descriptive name of the object
        :param owner:   User ID of the owner for this object

        :returns:  Device instance
        """
        super().__init__(c8y=c8y, type=type, name=name, owner=owner)
        self.is_device = True

    def to_json(self):
        # no doc changes
        object_json = super().to_json()
        object_json['c8y_IsDevice'] = {}
        return object_json

    def delete(self):
        """ Delete the device and the device user from database.

        Note: In contrast to the regular *delete* function defined in class
        ManagedObject, this version also removes the corresponding device
        user from database.

        :returns:  None
        """
        assert self.name, "Device name must be defined for deletion."
        device_username = 'device_' + self.name
        super().delete()
        self.c8y.users.delete(device_username)


class DeviceGroup(ManagedObject):
    """ Represent a device group within Cumulocity.

    Instances of this class are returned by functions of the corresponding
    DeviceGroupInventory API. Use this class to create new or update
    DeviceGroup objects.

    DeviceGroup objects are regular managed objects with additional
    standardized fragments and fields.

    See also https://cumulocity.com/guides/reference/inventory/#managed-object
        https://cumulocity.com/guides/users-guide/device-management/#grouping-devices
    """

    def __init__(self, c8y=None, name=None, owner=None):
        """ Build a new DeviceGroup object.

        Custom fragments can be added to the object after creation, using
        the add_fragment function.

        A *type* of a device group will always be either `c8y_DeviceGroup`
        or `c8y_DeviceSubGroup` (depending on it's level). This is handled
        by the API.

        :param c8y:  Cumulocity connection reference; needs to be set for the
            direct manipulation (create, delete) to function
        :param name:   Descriptive name of the object
        :param owner:   User ID of the owner for this object

        :returns:  DeviceGroup instance
        """
        # the 'type' of a device group can be c8y_DeviceGroup or c8y_DeviceSubgroup
        # it will be set dynamically when used
        super().__init__(c8y=c8y, type=None, name=name, owner=owner)
        self._added_child_groups = None
        self.is_device_group = True

    @classmethod
    def from_json(cls, object_json):
        return cls._from_managed_object(super().from_json(object_json))

    @classmethod
    def _from_managed_object(cls, managed_object):
        group = DeviceGroup(c8y=managed_object.c8y, name=managed_object.name, owner=managed_object.owner)
        group.id = managed_object.id
        group.child_assets = managed_object.child_assets
        return group

    def to_json(self):
        raise NotImplementedError("This method cannot be implemented for the DeviceGroup class.")

    def _to_json(self, is_root):
        object_json = super().to_json()
        object_json['type'] = 'c8y_DeviceGroup' if is_root else 'c8y_DeviceSubgroup'
        object_json['c8y_IsDeviceGroup'] = {}
        return object_json

    def add_group(self, name, owner=None):
        """ Add a child group.

        This change is written to the database immediately.

        :param name:  Name of the new group
        :param owner:  Owner of the new group
        :returns:  Updated DeviceGroup object
        """
        self._assert_id()
        child_json = DeviceGroup(name=name, owner=owner if owner else self.owner)._to_json(is_root=False)
        response_json = self._post_child_json(self.id, child_json)
        result = self.from_json(response_json)
        result.c8y = self.c8y
        return result

    def add_device(self, device_id):
        """ Add a device to this group.

        This change is written to the database immediately.

        :param device_id:  Database ID of the device to add
        :returns:  Updated DeviceGroup object
        """
        self._assert_id()
        device_json = {'id': device_id}
        response_json = self._post_child_json(self.id, device_json)
        result = self.from_json(response_json)
        result.c8y = self.c8y
        return result

    def add(self, *groups):
        """ Add child groups to this instance.

        Groups can be nested to any level.

        :param groups:  Collection of group objects to add as children
        :returns:  Self reference (for method chaining)
        """
        if len(groups) == 1 and isinstance(groups, list):
            self.add(*groups)
        if not self._added_child_groups:
            self._added_child_groups = []
        self._added_child_groups.extend(groups)
        return self

    def create(self):
        """ Create a new representation of this object within the database.

        This operation will create the group and all added child groups
        within the database.

        :returns:  A fresh DeviceGroup instance representing the created
            object within the database. This instance can be used to get at
            the ID of the new object.

        See also function DeviceGroupInventory.create which doesn't parse
        the result.
        """
        self._assert_c8y()
        # 1_ create the group
        group_json = self._to_json(is_root=True)
        response_json = self.c8y.post('/inventory/managedObjects', group_json)
        group_id = response_json['id']
        # 2_ create child groups recursively
        if self._added_child_groups:
            self._create_child_groups(parent_id=group_id, parent=self, groups=self._added_child_groups)
        # 3_ parse/return result
        if self._added_child_groups:
            # if there were child assets we need to read the object again
            response_json = self.c8y.get('/inventory/managedObjects/' + group_id)
        result = self.from_json(response_json)
        result.c8y = self.c8y
        return result

    def update(self):
        """ Write changed to the database.

        Note: Removing child groups is currently not supported.

        :returns:  A fresh DeviceGroup instance representing the updated
            object within the database.
        """
        # this will update any updated fields of this object as well as
        # create and link child groups added
        self._assert_c8y()
        self._assert_id()
        # 1_ update main object
        group_json = self.to_diff_json()
        object_path = '/inventory/managedObjects/' + self.id
        # json might actually be empty
        response_json = {}
        if group_json:
            response_json = self.c8y.post(object_path, group_json)
        # 2_ create child groups recursively
        if self._added_child_groups:
            self._create_child_groups(parent_id=self.id, parent=self, groups=self._added_child_groups)
        # 3_ parse/return result
        if self._added_child_groups:
            # if there were child assets we need to read the object again
            response_json = self.c8y.get(f'/inventory/managedObjects/{self.id}')
        result = self.from_json(response_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete('/inventory/managedObjects/' + str(self.id) + '?cascade=false')

    def delete_tree(self):
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete('/inventory/managedObjects/' + str(self.id) + '?cascade=true')

    def _create_child_groups(self, parent_id, parent, groups):
        for group in groups:
            # enrich child with defaults
            group.c8y = parent.c8y
            if not group.owner:
                group.owner = parent.owner
            # create as child assets
            response_json = self._post_child_json(parent_id, group._to_json(is_root=False))  # noqa
            # recursively create further levels
            if group._added_child_groups:  # noqa
                child_id = response_json['id']
                self._create_child_groups(parent_id=child_id, parent=group, groups=group._added_child_groups)  # noqa

    def _post_child_json(self, parent_id, child_json):
        self._assert_c8y()
        path = f'/inventory/managedObjects/{parent_id}/childAssets'
        return self.c8y.post(path, child_json, accept='application/vnd.com.nsn.cumulocity.managedObject+json')


class Binary(ManagedObject):
    def __init__(self, c8y=None, filename=None, media_type=None):
        super().__init__(c8y=c8y, type=media_type, name=filename)


class Inventory(_Query):

    def __init__(self, c8y):
        super().__init__(c8y, 'inventory/managedObjects')

    def get(self, id):  # noqa (id)
        """ Retrieve a specific managed object from the database.

        :param id:  ID of the managed object
        :returns:  A ManagedObject instance
        :raises:  KeyError if the ID is not defined within the database
        """
        managed_object = ManagedObject.from_json(self._get_object(id))
        managed_object.c8y = self.c8y  # inject c8y connection into instance
        return managed_object

    def get_all(self, type=None, fragment=None, name=None, limit=None, page_size=1000):  # noqa (type)
        """ Query the database for managed objects and return the results
        as list.

        This function is a greedy version of the select function. All
        available results are read immediately and returned as list.

        :returns:  List of ManagedObject instances
        """
        return [x for x in self.select(type=type, fragment=fragment, name=name, limit=limit, page_size=page_size)]

    def select(self, type=None, fragment=None, name=None, limit=None, page_size=1000):  # noqa (type)
        """ Query the database for managed objects and iterate over the
        results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Managed object type
        :param name:  Name of the managed object
        :param fragment:  Name of a present custom/standard fragment
        :param limit:  Limit the number of results to this number.
        :param page_size:  Define the number of events which are read (and
            parsed in one chunk). This is a performance related setting.

        :returns:  Generator of ManagedObject instances
        """
        query = None
        if name:
            query = f"name eq '{name}'"
        base_query = self._build_base_query(type=type, fragment=fragment, query=query, page_size=page_size)
        return super()._iterate(base_query, limit, ManagedObject.from_json)

    def create(self, *managed_objects: ManagedObject):
        """Create managed objects within the database.

        :param managed_objects:  collection of ManagedObject instances
        :returns:  None
        """
        super()._create(ManagedObject.to_json, *managed_objects)

    def update(self, *objects):
        """ Write changes to the database.

        :param objects:  A collection of ManagedObject instances
        :returns: None

        See also function ManagedObject.update which parses the result.
        """
        super()._update(ManagedObject.to_diff_json, *objects)

    def apply_to(self, object_model, *object_ids):
        """Apply a change to a number of existing objects.

        Takes a list of ID of already existing managed objects and applies a
        change within the database to all of them one by one.

        Uses the Cumulocity connection of this Inventory instance.

        :param object_model  ManagedObject instance holding the change structure
            like an added fragment of updated value.
        :param object_ids  a list of ID of already existing ManagedObject
            instances.
        """
        super()._apply_to(ManagedObject.to_diff_json, object_model, *object_ids)


class DeviceInventory(Inventory):

    def request(self, id):  # noqa (id)
        """ Create a device request.

        :param id:  Unique ID of the device (e.g. Serial, FMEI); this is
            _not_ the database ID.
        :returns: None
        """
        self.c8y.post('/devicecontrol/newDeviceRequests', {'id': id})

    def accept(self, id):  # noqa (id)
        """ Accept a device request.

        :param id:  Unique ID of the device (e.g. Serial, FMEI); this is
            _not_ the database ID.
        :returns: None
        """
        self.c8y.put('/devicecontrol/newDeviceRequests/' + str(id), {'status': 'ACCEPTED'})

    def get(self, id):  # noqa (id)
        """ Retrieve a specific device object.

        :param id:  ID of the device object
        :return:  a Device instance
        :raises:  KeyError if the ID is not defined within the database
        """
        device = Device.from_json(self._get_object(id))
        device.c8y = self.c8y
        return device

    def select(self, type=None, name=None, limit=None, page_size=100):  # noqa (type, parameters)
        """ Query the database for devices and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        :param type:  Managed object type
        :param name:  Name of the device
        :param limit:  Limit the number of results to this number.
        :param page_size:  Define the number of events which are read (and
            parsed in one chunk). This is a performance related setting.

        :returns:  Generator of Device objects
        """
        return super().select(type=type, fragment='c8y_IsDevice', name=name, limit=limit, page_size=page_size)

    def get_all(self, type=None, name=None, page_size=100):  # noqa (type, parameters)
        """ Query the database for devices and return the results as list.

        This function is a greedy version of the select function. All
        available results are read immediately and returned as list.

        :returns:  List of Device objects
        """
        return [x for x in self.select(type=type, name=name, page_size=page_size)]

    def delete(self, *devices):
        """ Delete one or more devices and the corresponding within the database.

        The objects can be specified as instances of an database object
        (then, the id field needs to be defined) or simply as ID (integers
        or strings).

        Note: In contrast to the regular *delete* function defined in class
        ManagedObject, this version also removes the corresponding device
        user from database.

        :param devices:  Device objects within the database specified
            (with defined ID).
        :returns:  None
        """
        for d in devices:
            d.delete()


class DeviceGroupInventory(Inventory):

    def get(self, group_id):
        """ Retrieve a specific device group object.

        :param group_id:  ID of the device group object
        :return:  a DeviceGroup instance
        :raises:  KeyError if the ID is not defined within the database
        """
        group = DeviceGroup.from_json(self._get_object(group_id))
        group.c8y = self.c8y
        return group

    def select(self, fragment=None, name=None, page_size=100):  # noqa
        """ Select managed objects by various parameters.

        This is a lazy implementation; results are fetched in pages but
        parsed and returned one by one.

        The type of all DeviceGroup objects is fixed 'c8y_DeviceGroup',
        hence filtering by type is not possible.

        :param fragment:  fragment string that is present within the objects
        :param name:  name string of the objects to select; no partial
            matching/patterns are supported
        :param page_size:  number of objects to fetch per request
        :return:  Generator of ManagedObject instances
        """
        query = None
        if name:
            query = f"name eq '{name}'"
        base_query = self._build_base_query(type='c8y_DeviceGroup', fragment=fragment, query=query, page_size=page_size)
        page_number = 1
        while True:
            results = [DeviceGroup.from_json(x) for x in self._get_page(base_query, page_number)]
            if not results:
                break
            for result in results:
                result.c8y = self.c8y  # inject c8y connection into instance
                yield result
            page_number = page_number + 1

    def get_all(self, fragment=None, name=None, page_size=100):  # noqa
        """ Select managed objects by various parameters.

        In contract to the select method this version is not lazy. It will
        collect the entire result set before returning.

        The type of all DeviceGroup objects is fixed 'c8y_DeviceGroup',
        hence filtering by type is not possible.

        :param fragment:  fragment string that is present within the objects
        :param name:  name string of the objects to select; no partial
            matching/patterns are supported
        :param page_size:  number of objects to fetch per request
        :return:  List of ManagedObject instances
        """
        return [x for x in self.select(fragment=fragment, name=name, page_size=page_size)]

    def create(self, *groups):
        """Batch create a collection of groups and entire group trees.

        :param groups:  collection of DeviceGroup instances; each can
            define children as needed.
        """
        if len(groups) == 1 and isinstance(groups, list):
            self.create(*groups)
        for group in groups:
            if not group.c8y:
                group.c8y = self
            group.create(True)


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


class ExternalId(_DatabaseObject):
    """ Represents an instance of an ExternalID in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Identity API. Use this class to create or remove external ID.

    See also: https://cumulocity.com/guides/reference/identity/#external-id
    """
    def __init__(self, c8y=None, external_id=None, external_type=None, managed_object_id=None):
        """ Create a new ExternalId object.

        :param c8y:  Cumulocity connection reference; needs to be set for
            the direct manipulation (create, delete) to function.
        :param external_id:  A string to be used as ID for external use
        :param external_type:  Type of the external ID,
            e.g. _com_cumulocity_model_idtype_SerialNumber_
        :param managed_object_id:  Valid database ID of a managed object
            within Cumulocity

        :returns:  ExternalId object
        """
        super().__init__(c8y=c8y)
        self.external_id = external_id
        self.external_type = external_type
        self.managed_object_id = managed_object_id

    @staticmethod
    def from_json(object_json):
        """ Build a new ExternalId instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        :param object_json:  JSON object (nested dictionary)
            representing an external ID object within Cumulocity
        :returns:  Event object
        """
        external_type = object_json['type']
        external_id = object_json['externalId']
        managed_object_id = object_json['managedObject']['id']
        return ExternalId(external_id=external_id, external_type=external_type, managed_object_id=managed_object_id)

    def create(self):
        """ Store the external ID to the database.

        :returns:  self
        """
        self._assert_c8y()
        self.c8y.identity.create(self.external_id, self.external_type, self.managed_object_id)
        return self

    def delete(self):
        """ Remove the external ID from the database.

        :returns:  self
        """
        self._assert_c8y()
        self.c8y.identity.delete(self.external_id, self.external_type)

    def get_id(self):
        """ Read the referenced managed object ID from database.

        :returns:  Database ID referenced by the external_id and
            external_type of this instance.
        """
        self._assert_c8y()
        return self.c8y.identity.get_id(self.external_id, self.external_type)

    def get_object(self):
        """ Read the referenced managed object from database.

        :returns:  Database ID referenced by the external_id and
            external_type of this instance.
        """
        self._assert_c8y()
        return self.c8y.identity.get_object(self.external_id, self.external_type)

    def __repr__(self):
        return {'external_id': self.external_id,
                'external_type': self.external_type,
                'object_id': self.managed_object_id}


class Identity(object):
    # the Identity API of C8Y uses inconsistent resource paths and therefore
    # cannot use the generic _Query base class helper

    def __init__(self, c8y):
        self.c8y = c8y

    def create(self, external_id, external_type, managed_object_id):
        """ Create a new External ID within the database.

        :param external_id:  A string to be used as ID as reference
        :param external_type:  Type of the external ID,
            e.g. _com_cumulocity_model_idtype_SerialNumber_
        :param managed_object_id:  Valid database ID of a managed object
            within Cumulocity

        :returns: None
        """
        body_json = {
            'externalId': external_id,
            'type': external_type}
        path = f'/identity/globalIds/{managed_object_id}/externalIds'
        self.c8y.post(path, body_json)

    def delete(self, external_id, external_type):
        """ Remove an External ID from the database.

        :param external_id:  The external ID used as reference
        :param external_type:  Type of the external ID,
            e.g. _com_cumulocity_model_idtype_SerialNumber_

        :returns: None
        """
        self.c8y.delete(self._build_object_path(external_id, external_type))

    def get(self, external_id, external_type):
        """ Obtain a specific External ID from the database.

        :param external_id:  The external ID used as reference
        :param external_type:  Type of the external ID,
            e.g. _com_cumulocity_model_idtype_SerialNumber_

        :returns: ExternalID object
        """
        return ExternalId.from_json(self._get_raw(external_id, external_type))

    def get_id(self, external_id, external_type):
        """ Read the ID of the referenced managed object by its external ID.

        :param external_id:  The external ID used as reference
        :param external_type:  Type of the external ID,
            e.g. _com_cumulocity_model_idtype_SerialNumber_

        :returns: A database ID (string)
        """
        return self._get_raw(external_id, external_type)['managedObject']['id']

    def get_object(self, external_id, external_type):
        """ Read a managed object by its external ID reference.

        :param external_id:  A string to be used as ID for external use
        :param external_type:  Type of the external ID,
            e.g. _com_cumulocity_model_idtype_SerialNumber_

        :returns: ManagedObject instance
        """
        return self.c8y.inventory.get(self.get_id(external_id, external_type))

    def _get_raw(self, external_id, external_type):
        return self.c8y.get(self._build_object_path(external_id, external_type))

    @staticmethod
    def _build_object_path(external_id, external_type):
        return f'/identity/externalIds/{external_type}/{external_id}'
