# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
# pylint: disable=too-many-lines

from __future__ import annotations

from typing import Any, Generator, List

from c8y_api._base_api import CumulocityRestApi
from c8y_api.model import Users, User
from c8y_api.model._base import _DictWrapper, CumulocityResource, SimpleObject, ComplexObject
from c8y_api.model._parser import ComplexObjectParser


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

        "pt_current": {
            "CURR": {
                "unit": "A",
                "value": 50
            }
        }

    A fragment has a name (*pt_current* in above example) and can virtually
    define any substructure.
    """
    def __init__(self, name: str, **kwargs):
        """ Create a new fragment.

        Params
            name (str):  Name of the fragment
            kwargs:  Named elements of the fragment. Each element
                can either be a simple value of a complex substructure
                modelled as nested dictionary.
        Returns:
            New Fragment instance
        """
        self.name = name
        self.items = kwargs

    def __getattr__(self, name: str):
        """ Get a specific element of the fragment.

        Args:
            name (str):  Name of the element

        Returns:
            Value of the element. May be a simple value or a
            complex substructure defined as nested dictionary.
        """
        item = self.items[name]
        return item if not isinstance(item, dict) else _DictWrapper(item)

    def has(self, name: str) -> bool:
        """ Check whether a specific element is defined.

        Args:
            name (str):  Name of the element

        Returns:
            True if the element is present, False otherwise
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


class InventoryUtil:
    """Utility functions to work with the Inventory API."""

    @staticmethod
    def build_managed_object_reference(object_id: str | int) -> dict:
        """Build the JSON for a managed object reference.

        Args:
            object_id (str|int): ID of a managed object

        Returns
            JSON (nested dict) for a managed object reference.
        """
        return {'managedObject': {'id': str(object_id)}}


class ManagedObject(ComplexObject):
    """ Represent a managed object within the database.

    Instances of this class are returned by functions of the corresponding
    Inventory API. Use this class to create new or update managed objects.

    Within Cumulocity a managed object is used to hold virtually any
    *additional* (apart from measurements, events and alarms) information.
    This custom information is modelled in *fragments*, named elements
    of any structure.

    Fragments are modelled as standard Python fields and can be accessed
    directly if the names & structures are known:

        x = mo.c8y_CustomFragment.values.x

    Managed objects can be changed and such updates are written as
    *differences* to the database. The API does the tracking of these
    differences automatically - just use the ManagedObject class like
    any other Python class.

        mo.owner = 'admin@cumulocity.com'
        mo.c8y_CustomFragment.region = 'EMEA'
        mo.add_fragment('c8y_CustomValue', value=12, uom='units')

    Note: This does not work if a fragment is actually a field, not a
    structure own it's own. A direct assignment to such a value fragment,
    like

        mo.c8y_CustomReferences = [1, 2, 3]

    is currently not supported nicely as it will not be recognised as an
    update. A manual update flagging is required:

        mo.c8y_CustomReferences = [1, 2, 3]
        mo.flag_update('c8y_CustomReferences')

    See also https://cumulocity.com/guides/reference/inventory/#managed-object
    """

    _resource = '/inventory/managedObjects'
    _accept = CumulocityRestApi.ACCEPT_MANAGED_OBJECT

    _not_updatable = {'creation_time', 'update_time'}
    _parser = ComplexObjectParser(
        {'_u_type': 'type',
         '_u_name': 'name',
         '_u_owner': 'owner',
         'creation_time': 'creationTime',
         'update_time': 'lastUpdated'},
        ['childDevices', 'childAssets', 'childAdditions',
         'deviceParents', 'assetParents', 'additionParents'])

    def __init__(self, c8y: CumulocityRestApi = None,
                 type: str = None, name: str = None, owner: str = None, **kwargs):  # noqa
        """ Create a new ManagedObject instance.

        Custom fragments can be added to the object using `kwargs` or after
        creation using += or [] syntax.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            type (str):  ManagedObject type
            name (str):  ManagedObject name
            owner (str):  User ID of the owning user (can be left None to
                automatically assign to the connection user upon creation)
            kwargs:  Additional arguments are treated as custom fragments

        Returns:
            ManagedObject instance
        """
        super().__init__(c8y, **kwargs)
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
        self.is_binary = False

    type = SimpleObject.UpdatableProperty(name='_u_type')
    name = SimpleObject.UpdatableProperty(name='_u_name')
    owner = SimpleObject.UpdatableProperty(name='_u_owner')

    @property
    def creation_datetime(self):
        """ Convert the object's creation to a Python datetime object.

        Returns:
            Standard Python datetime object
        """
        return super()._to_datetime(self.creation_time)

    @property
    def update_datetime(self):
        """ Convert the object's creation to a Python datetime object.

        Returns:
            Standard Python datetime object
        """
        return super()._to_datetime(self.update_time)

    @classmethod
    def _from_json(cls, object_json: dict, new_object: Any) -> Any:
        # pylint: disable=arguments-differ, arguments-renamed
        """This function is used by derived classes to share the logic.
        Purposely no type information."""
        mo = super(ManagedObject, cls)._from_json(object_json, new_object)
        if 'c8y_IsDevice' in object_json:
            mo.is_device = True
        if 'c8y_IsBinary' in object_json:
            mo.is_binary = True
        if 'childDevices' in object_json:
            mo.child_devices = cls._parse_references(object_json['childDevices'])
        if 'childAssets' in object_json:
            mo.child_assets = cls._parse_references(object_json['childAssets'])
        if 'childAdditions' in object_json:
            mo.child_additions = cls._parse_references(object_json['childAdditions'])
        return mo

    @classmethod
    def from_json(cls, json: dict) -> ManagedObject:
        """ Build a new ManagedObject instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        Args:
            json (dict): JSON object (nested dictionary)
                representing a managed object within Cumulocity

        Returns:
            ManagedObject object
        """
        return cls._from_json(json, ManagedObject())

    def to_json(self, only_updated=False) -> dict:
        json = super().to_json(only_updated)
        if not only_updated:
            if self.is_device:
                json['c8y_IsDevice'] = {}
            if self.is_device_group:
                json['c8y_IsDeviceGroup'] = {}
            if self.is_binary:
                json['c8y_IsBinary'] = ''
        return json

    @classmethod
    def _parse_references(cls, base_json):
        return [NamedObject.from_json(j['managedObject']) for j in base_json['references']]

    def create(self) -> ManagedObject:
        """ Create a new representation of this object within the database.

        This function can be called multiple times to create multiple
        instances of this object with different ID.

        Returns:
            A fresh ManagedObject instance representing the created
            object within the database. This instance can be used to get
            at the ID of the new managed object.

        See also function Inventory.create which doesn't parse the result.
        """
        return self._create()

    def update(self) -> ManagedObject:
        """ Write changes to the database.

        Returns:
            A fresh ManagedObject instance representing the updated
            object within the database.

        See also function Inventory.update which doesn't parse the result.
        """
        return self._update()

    def apply_to(self, other_id: str | int) -> ManagedObject:
        """Apply the details of this object to another object in the database.

        Note: This will take the full details, not just the updates.

        Args:
            other_id (str|int):  Database ID of the event to update.
        Returns:
            A fresh ManagedObject instance representing the updated
            object within the database.

        See also function Inventory.apply_to which doesn't parse the result.
        """
        self._assert_c8y()
        # put diff json to another object (by ID)
        result_json = self.c8y.put(self.__RESOURCE + str(other_id), json=self.to_diff_json(),
                                   accept=self.c8y.ACCEPT_MANAGED_OBJECT)
        result = ManagedObject.from_json(result_json)
        result.c8y = self.c8y
        return result

    def delete(self):
        """ Delete this object within the database.

        The database ID must be defined for this to function.

        See also function Inventory.delete to delete multiple objects.
        """
        self._delete()

    def add_child_asset(self, child: ManagedObject | str | int):
        """ Link a child asset to this managed object.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (ManagedObject|str|int): Child asset or its object ID
        """
        self._add_any_child('/childAssets', child)

    def add_child_device(self, child: ManagedObject | str | int):
        """ Link a child device to this managed object.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (ManagedObject|str|int): Child device or its object ID
        """
        self._add_any_child('/childDevices', child)

    def add_child_addition(self, child: ManagedObject | str | int):
        """ Link a child addition to this managed object.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (ManagedObject|str|int): Child addition or its object ID
        """
        self._add_any_child('/childAdditions', child)

    def unassign_child_asset(self, child: ManagedObject | str | int):
        """Remove the link to a child asset.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (ManagedObject|str|int): Child device or its object ID
        """
        self._unassign_any_child('/childAssets', child)

    def unassign_child_device(self, child: Device | str | int):
        """Remove the link to a child device.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (Device|str|int): Child device or its object ID
        """
        self._unassign_any_child('/childDevices', child)

    def unassign_child_addition(self, child: ManagedObject | str | int):
        """Remove the link to a child addition.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (ManagedObject|str|int): Child device or its object ID
        """
        self._unassign_any_child('/childAdditions', child)

    def _add_any_child(self, path, child: ManagedObject | str | int):
        self._assert_c8y()
        self._assert_id()
        child_id = child.id if hasattr(child, 'id') else child
        self.c8y.post(self._build_object_path() + path,
                      json=InventoryUtil.build_managed_object_reference(child_id),
                      accept=None)

    def _unassign_any_child(self, path, child: ManagedObject | str | int):
        self._assert_c8y()
        self._assert_id()
        child_id = child.id if hasattr(child, 'id') else child
        self.c8y.delete(self._build_object_path() + path + '/' + child_id)


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

    def __init__(self, c8y: CumulocityRestApi = None,
                 type: str = None, name: str = None, owner: str = None, **kwargs):  # noqa
        """ Create a new Device instance.

        A Device object will always have a `c8y_IsDevice` fragment.
        Additional custom fragments can be added using `kwargs` or
        after creation, using += or [] syntax.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            type (str):  Device type
            name (str):  Device name
            owner (str):  User ID of the owning user (can be left None to
                automatically assign to the connection user upon creation)
            kwargs:  Additional arguments are treated as custom fragments

        Returns:
            Device instance
        """
        super().__init__(c8y=c8y, type=type, name=name, owner=owner, **kwargs)
        self.is_device = True

    @classmethod
    def from_json(cls, json: dict) -> Device:
        # (no doc changes)
        return super()._from_json(json, Device())

    def to_json(self, only_updated=False) -> dict:
        # (no doc changes)
        object_json = super().to_json(only_updated)
        if not only_updated:
            object_json['c8y_IsDevice'] = {}
        return object_json

    def get_username(self) -> str:
        """Return the device username.

        Returns:
            Username of the device's user.
        """
        assert self.name, "Device name must be defined."
        return 'device_' + self.name

    def get_user(self) -> User:
        """Return the device user.

        Returns:
            Device's user.
        """
        return Users(self.c8y).get(self.get_username())


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

    ROOT_TYPE = 'c8y_DeviceGroup'
    CHILD_TYPE = 'c8y_DeviceSubGroup'

    def __init__(self, c8y=None, root: bool = False, name: str = None, owner: str = None, **kwargs):
        """ Build a new DeviceGroup object.

        A type of a device group will always be either `c8y_DeviceGroup`
        or `c8y_DeviceSubGroup` (depending on it's level). This is handled
        by the API.

        A DeviceGroup object will always have a `c8y_IsDeviceGroup` fragment.
        Additional custom fragments can be added using `kwargs` or after
        creation, using += or [] syntax.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            root (bool):  Whether the group is a root group (default is False)
            name (str):  Device name
            owner (str):  User ID of the owning user (can be left None to
                automatically assign to the connection user upon creation)
            kwargs:  Additional arguments are treated as custom fragments

        Returns:
            DeviceGroup instance
        """
        super().__init__(c8y=c8y, type=self.ROOT_TYPE if root else self.CHILD_TYPE,
                         name=name, owner=owner, **kwargs)
        self._added_child_groups = None
        self.is_device_group = True

    @classmethod
    def from_json(cls, json: dict) -> DeviceGroup:
        """ Build a new DeviceGroup instance from JSON.

        The JSON is assumed to be in the format as it is used by the
        Cumulocity REST API.

        Args:
            json (dict): JSON object (nested dictionary)
                representing a device group within Cumulocity

        Returns:
            DeviceGroup instance
        """
        return super()._from_json(json, DeviceGroup())

    def create_child(self, name: str, owner: str = None, **kwargs) -> DeviceGroup:
        """ Create and assign a child group.

        This change is written to the database immediately.

        Args:
            name (str):  Device name
            owner (str):  User ID of the owning user (can be left None to
                automatically assign to the connection user upon creation)
            kwargs:  Additional arguments are treated as custom fragments

        Returns:
            The newly created DeviceGroup object
        """
        self._assert_c8y()
        self._assert_id()
        child_json = DeviceGroup(name=name, owner=owner if owner else self.owner, **kwargs).to_json()

        response_json = self.c8y.post(self._build_object_path() + '/childAssets', json=child_json,
                                      accept=CumulocityRestApi.ACCEPT_MANAGED_OBJECT)
        result = self.from_json(response_json)
        result.c8y = self.c8y
        return result

    def create(self) -> DeviceGroup:
        """ Create a new representation of this object within the database.

        This operation will create the group and all added child groups
        within the database.

        :returns:  A fresh DeviceGroup instance representing the created
            object within the database. This instance can be used to get at
            the ID of the new object.

        See also function DeviceGroupInventory.create which doesn't parse
        the result.
        """
        return super()._create()

    def update(self) -> DeviceGroup:
        """ Write changed to the database.

        Note: Removing child groups is currently not supported.

        :returns:  A fresh DeviceGroup instance representing the updated
            object within the database.
        """
        return super()._update()

    def delete(self):
        """Delete this device group.

        The child groups (if there are any) are left dangling. This is
        equivalent to using the `cascade=false` parameter in the
        Cumulocity REST API.
        """
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete(self._build_object_path() + '?cascade=false')

    def delete_tree(self):
        """Delete this device group and its children.

        This is equivalent to using the `cascade=true` parameter in the
        Cumulocity REST API.
        """
        self._assert_c8y()
        self._assert_id()
        self.c8y.delete(self._build_object_path() + '?cascade=true')

    def assign_child_group(self, child: DeviceGroup | str | int):
        """Link a child group to this device group.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (DeviceGroup|str|int): Child device or its object ID
        """
        super().add_child_asset(child)

    def unassign_child_group(self, child: DeviceGroup | str | int):
        """Remove the link to a child group.

        This operation is executed immediately. No additional call to
        the `update` method is required.

        Args:
            child (DeviceGroup|str|int): Child device or its object ID
        """
        super().unassign_child_asset(child)


class Inventory(CumulocityResource):
    """Provides access to the Inventory API.

    This class can be used for get, search for, create, update and
    delete managed objects within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Inventory-API
    """

    def __init__(self, c8y):
        super().__init__(c8y, 'inventory/managedObjects')

    def get(self, id) -> ManagedObject:  # noqa (id)
        """ Retrieve a specific managed object from the database.

        Args:
            ID of the managed object

        Returns:
             A ManagedObject instance

        Raises:
            KeyError if the ID is not defined within the database
        """
        managed_object = ManagedObject.from_json(self._get_object(id))
        managed_object.c8y = self.c8y  # inject c8y connection into instance
        return managed_object

    def get_all(self, type: str = None, fragment: str = None, name: str = None, owner: str = None,  # noqa (type)
                limit: int = None, page_size: int = 1000):
        """ Query the database for managed objects and return the results
        as list.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        Returns:
            List of ManagedObject instances
        """
        return list(self.select(type=type, fragment=fragment, name=name, limit=limit, page_size=page_size))

    def select(self, type: str = None, fragment: str = None, name: str = None, owner: str = None,  # noqa (type)
               limit: int = None, page_size: int = 1000) -> Generator[ManagedObject]:
        """ Query the database for managed objects and iterate over the
        results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        Args:
            type (str):  Managed object type
            fragment (str):  Name of a present custom/standard fragment
            name (str):  Name of the managed object
            owner (str):  Username of the object owner
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator for ManagedObject instances
        """
        return self._select(ManagedObject.from_json, type=type, fragment=fragment, name=name, owner=owner,
                            limit=limit, page_size=page_size)

    def _select(self, jsonyfy_func, type: str = None, fragment: str = None, name: str = None,
                owner: str = None,  limit: int = None, page_size: int = 1000) -> Generator[Any]:
        base_query = self._build_base_query(type=type, fragment=fragment, owner=owner,
                                            query=f"name eq '{name}'" if name else None, page_size=page_size)
        return super()._iterate(base_query, limit, jsonyfy_func)

    def create(self, *objects: ManagedObject):
        """Create managed objects within the database.

        Args:
            objects (*ManagedObject): collection of ManagedObject instances
        """
        super()._create(ManagedObject.to_json, *objects)

    def update(self, *objects: ManagedObject):
        """ Write changes to the database.

        Args:
            objects (*ManagedObject): collection of ManagedObject instances

        See also function ManagedObject.update which parses the result.
        """
        super()._update(ManagedObject.to_diff_json, *objects)

    def apply_to(self, object_model: ManagedObject, *object_ids):
        """Apply a change to multiple already existing objects.

        Applies the details of a model object to a set of already existing
        managed objects.

        Note: This will take the full details, not just the updates.

        Args:
            object_model (ManagedObject): ManagedObject instance holding
                the change structure (e.g. a specific fragment)
            object_ids (*str): a collection of ID of already existing
                managed objects within the database
        """
        super()._apply_to(ManagedObject.to_full_json, object_model, *object_ids)


class DeviceInventory(Inventory):
    """Provides access to the Device Inventory API.

    This class can be used for get, search for, create, update and
    delete device objects within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Inventory-API
    """

    def request(self, id: str):  # noqa (id)
        """ Create a device request.

        Args:
            id (str): Unique ID of the device (e.g. Serial, IMEI); this is
            _not_ the database ID.
        """
        self.c8y.post('/devicecontrol/newDeviceRequests', {'id': id})

    def accept(self, id: str):  # noqa (id)
        """ Accept a device request.

        Args:
            id (str): Unique ID of the device (e.g. Serial, IMEI); this is
            _not_ the database ID.
        """
        self.c8y.put('/devicecontrol/newDeviceRequests/' + str(id), {'status': 'ACCEPTED'})

    def get(self, id: str) -> Device:  # noqa (id)
        """ Retrieve a specific device object.

        Args:
            id (str): ID of the device object

        Returns:
            A Device instance

        Raises:
            KeyError if the ID is not defined within the database
        """
        device = Device.from_json(self._get_object(id))
        device.c8y = self.c8y
        return device

    def select(self, type: str = None, name: str = None, owner: str = None,  # noqa (type, args)
               limit: int = None, page_size: int = 100) -> Generator[Device]:
        # pylint: disable=arguments-differ
        """ Query the database for devices and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters specification.  Filters can be
        combined (within reason).

        Args:
            type (str):  Device type
            name (str):  Name of the device
            owner (str):  Username of the object owner
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator for Device objects
        """
        return self._select(ManagedObject.from_json, type=type, fragment='c8y_IsDevice', name=name, owner=owner,
                            limit=limit, page_size=page_size)

    def get_all(self, type: str = None, name: str = None, owner: str = None,   # noqa (type, parameters)
                page_size: int = 100) -> List[Device]:
        # pylint: disable=arguments-differ, arguments-renamed
        """ Query the database for devices and return the results as list.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        Returns:
            List of Device objects
        """
        return list(self.select(type=type, name=name, owner=owner, page_size=page_size))

    def delete(self, *devices: Device):
        """ Delete one or more devices and the corresponding within the database.

        The objects can be specified as instances of an database object
        (then, the id field needs to be defined) or simply as ID (integers
        or strings).

        Note: In contrast to the regular `delete` function defined in class
        ManagedObject, this version also removes the corresponding device
        user from database.

        Args:
            devices (*Device): Device objects within the database specified
                (with defined ID).
        """
        for d in devices:
            d.delete()


class DeviceGroupInventory(Inventory):
    """Provides access to the Device Groups Inventory API.

    This class can be used for get, search for, create, update and
    delete device groups within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Inventory-API
    """

    def get(self, group_id):
        # pylint: disable=arguments-renamed
        """ Retrieve a specific device group object.

        :param group_id:  ID of the device group object
        :return:  a DeviceGroup instance
        :raises:  KeyError if the ID is not defined within the database
        """
        group = DeviceGroup.from_json(self._get_object(group_id))
        group.c8y = self.c8y
        return group

    def select(self, type: str = DeviceGroup.ROOT_TYPE, parent: str | int = None, fragment: str = None,
               name: str = None, owner: str = None, page_size: int = 100) -> Generator[DeviceGroup]:
        # pylint: disable=arguments-differ, arguments-renamed
        """ Select device groups by various parameters.

        This is a lazy implementation; results are fetched in pages but
        parsed and returned one by one.

        The type of all DeviceGroup objects is fixed 'c8y_DeviceGroup',
        'c8y_DeviceSubGroup' if searching by `parent` respectively. Hence
        manual filtering by type is not supported.

        Args:
            type (bool):  Filter for root or child groups respectively.
                Note: If set to None, no type filter will be applied which
                will match all kinds of managed objects. If you want to
                match device groups only you need to use the fragment filter.
            parent (str): ID of the parent device group
                Note: this forces the `type` filter to be c8y_DeviceSubGroup
            fragment (str): Additional fragment present within the objects
            name (str): Name string of the groups to select; no partial
                matching/patterns are supported
            owner (str): Username of the group owner
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator of DeviceGroup instances
        """
        query_filters = []
        if name:
            query_filters.append(f"name eq '{name}'")
        if parent:
            query_filters.append(f"bygroupid({parent})")
            type = DeviceGroup.CHILD_TYPE

        # if any query was defined, all filters must be put into the query
        if query_filters:
            query_filters.append(f"type eq {type}")
            # all other filters must be set as well
            if fragment:
                query_filters.append(f"has({fragment})")
            if owner:
                query_filters.append(f"owner eq '{owner}'")
            query = '$filter=' + ' and '.join(query_filters)

            base_query = self._build_base_query(query=query, page_size=page_size)
        # otherwise we can just build the regular query
        else:
            base_query = self._build_base_query(type=type, fragment=fragment, owner=owner, page_size=page_size)

        return super()._iterate(base_query, limit=9999, parse_func=DeviceGroup.from_json)

    def get_all(self, type: str = DeviceGroup.ROOT_TYPE, parent: str | int = None, fragment: str = None,
                name: str = None, owner: str = None, page_size: int = 100):  # noqa
        # pylint: disable=arguments-differ, arguments-renamed
        """ Select managed objects by various parameters.

        In contract to the select method this version is not lazy. It will
        collect the entire result set before returning.

        Returns:
            List of DeviceGroup instances
        """
        return list(self.select(type=type, parent=parent, fragment=fragment, name=name, page_size=page_size))

    def create(self, *groups):
        """Batch create a collection of groups and entire group trees.

        :param groups:  collection of DeviceGroup instances; each can
            define children as needed.
        """
        super()._create(DeviceGroup.to_json, *groups)

    def assign_children(self, root_id, *child_ids):
        """Link child groups to this device group.

        Args:
            root_id (str|int): ID of the root device group
            child_ids (*str|int): ID of the child device groups
        """
        # adding multiple references at once is not (yet) supported
        # refs = {'references': [InventoryUtil.build_managed_object_reference(id) for id in child_ids]}
        # self.c8y.post(self.build_object_path(root_id) + '/childAssets', json=refs, accept='')
        for id in child_ids:
            self.c8y.post(self.build_object_path(root_id) + '/childAssets',
                          json=InventoryUtil.build_managed_object_reference(id), accept='')

    def unassign_children(self, root_id, *child_ids):
        """Unlink child groups from this device group.

        Args:
            root_id (str|int): ID of the root device group
            child_ids (*str|int): ID of the child device groups
        """
        refs = {'references': [InventoryUtil.build_managed_object_reference(id) for id in child_ids]}
        self.c8y.delete(self.build_object_path(root_id) + '/childAssets', json=refs)

    def delete(self, *groups: DeviceGroup | str | int):
        """Delete one or more single device groups within the database.

        The child groups (if there are any) are left dangling. This is
        equivalent to using the `cascase=false` parameter in the
        Cumulocity REST API.

        Args:
            groups:  Objects resp. their ID within the database
        """
        self._delete(False, *groups)

    def delete_trees(self, *groups: DeviceGroup | str | int):
        """Delete one or more device groups trees within the database.

        This is equivalent to using the `cascade=true` parameter in the
        Cumulocity REST API.

        Args:
            groups:  Objects resp. their ID within the database
        """
        self._delete(False, *groups)

    def _delete(self, cascade: bool, *objects: DeviceGroup | str | int):
        try:
            object_ids = [o.id for o in objects]  # noqa (id)
        except AttributeError:
            object_ids = objects
        for object_id in object_ids:
            self.c8y.delete(self.build_object_path(object_id) + f"?cascade={'true' if cascade else 'false'}")
