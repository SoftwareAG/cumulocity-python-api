# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
# pylint: disable=too-many-lines

from __future__ import annotations

from typing import Any, Generator, List

from c8y_api.model._base import CumulocityResource
from c8y_api.model._util import _QueryUtil
from c8y_api.model.managedobjects import ManagedObjectUtil, ManagedObject, Device, DeviceGroup


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
        return list(self.select(type=type, fragment=fragment, name=name, owner=owner, limit=limit, page_size=page_size))

    def select(self, type: str = None, fragment: str = None, name: str = None, owner: str = None,  # noqa (type)
               query: str = None, limit: int = None, page_size: int = 1000) -> Generator[ManagedObject]:
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
                Note: The Cumulocity REST API does not support filtering for
                names directly; this is a convenience parameter which will
                translate all filters into a query string.
            owner (str):  Username of the object owner
            query (str):  Complex query to execute; all other filters are
                ignored if such a custom query is provided
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator for ManagedObject instances
        """
        return self._select(ManagedObject.from_json, type=type, fragment=fragment, name=name, owner=owner,
                            query=None, limit=limit, page_size=page_size)

    def _select(self, jsonyfy_func, type: str = None, fragment: str = None, name: str = None,  # noqa
                owner: str = None, query: str = None, limit: int = None, page_size: int = 1000) -> Generator[Any]:

        query_filters = []

        # if there is no custom query, we check whether standard filters need to
        # be translated into a query
        if not query and name:

            # A name filter can only be expressed as a query, which then
            # triggers "query mode" (all filters are translated into a query)
            query_filters.append(f"name eq '{_QueryUtil.encode_odata_query_value(name)}'")

            if type:
                query_filters.append(f"type eq '{type}'")
            if owner:
                query_filters.append(f"owner eq '{owner}'")
            if fragment:
                query_filters.append(f"has({fragment})")
            if len(query_filters) == 1:
                query = query_filters[0]
            else:
                query = '$filter=(' + ' and '.join(query_filters) + ')'

        if query:
            base_query = self._build_base_query(query=query, page_size=page_size)
        else:
            base_query = self._build_base_query(type=type, fragment=fragment, owner=owner, page_size=page_size)

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
               query: str = None, limit: int = None, page_size: int = 100) -> Generator[Device]:
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
                Note: The Cumulocity REST API does not support filtering for
                names directly; this is a convenience parameter which will
                translate all filters into a query string.
            owner (str):  Username of the object owner
            query (str):  Complex query to execute; all other filters are
                ignored if such a custom query is provided
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator for Device objects
        """
        return self._select(ManagedObject.from_json, type=type, fragment='c8y_IsDevice', name=name, owner=owner,
                            query=query, limit=limit, page_size=page_size)

    def get_all(self, type: str = None, name: str = None, owner: str = None,   # noqa (type, parameters)
                page_size: int = 100) -> List[Device]:
        # pylint: disable=arguments-differ
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
        # pylint: disable=arguments-differ, arguments-renamed
        """ Retrieve a specific device group object.

        :param group_id:  ID of the device group object
        :return:  a DeviceGroup instance
        :raises:  KeyError if the ID is not defined within the database
        """
        group = DeviceGroup.from_json(self._get_object(group_id))
        group.c8y = self.c8y
        return group

    def select(self, type: str = DeviceGroup.ROOT_TYPE, parent: str | int = None, fragment: str = None,  # noqa
               name: str = None, owner: str = None, query: str = None, page_size: int = 100) -> Generator[DeviceGroup]:
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
                Like the `name` parameter, this is a convenience parameter
                which will translate all filters into a query string.
            fragment (str): Additional fragment present within the objects
            name (str): Name string of the groups to select
                Note:  he Cumulocity REST API does not support filtering for
                names directly; this is a convenience parameter which will
                translate all filters into a query string.
                No partial matching/patterns are supported
            owner (str): Username of the group owner
            query (str):  Complex query to execute; all other filters are
                ignored if such a custom query is provided
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator of DeviceGroup instances
        """
        query_filters = []

        # if there is no custom query, we check whether standard filters need to
        # be translated into a query
        if not query:

            # Both name and parent filters can only be expressed as a query,
            # which then triggers "query mode"
            if name:
                query_filters.append(f"name eq '{_QueryUtil.encode_odata_query_value(name)}'")
            if parent:
                query_filters.append(f"bygroupid({parent})")
                type = DeviceGroup.CHILD_TYPE  # noqa

            # if any query was defined, all filters must be put into the query
            if query_filters:
                if type:
                    query_filters.append(f"type eq '{type}'")
                if owner:
                    query_filters.append(f"owner eq '{owner}'")
                if fragment:
                    query_filters.append(f"has({fragment}")
                query = '$filter=' + ' and '.join(query_filters)

        if query:
            base_query = self._build_base_query(query=query, page_size=page_size)
        else:
            base_query = self._build_base_query(type=type, fragment=fragment, owner=owner, page_size=page_size)

        return super()._iterate(base_query, limit=9999, parse_func=DeviceGroup.from_json)

    def get_all(self, type: str = DeviceGroup.ROOT_TYPE, parent: str | int = None, fragment: str = None, # noqa
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
        for child_id in child_ids:
            self.c8y.post(self.build_object_path(root_id) + '/childAssets',
                          json=ManagedObjectUtil.build_managed_object_reference(child_id), accept='')

    def unassign_children(self, root_id, *child_ids):
        """Unlink child groups from this device group.

        Args:
            root_id (str|int): ID of the root device group
            child_ids (*str|int): ID of the child device groups
        """
        refs = {'references': [ManagedObjectUtil.build_managed_object_reference(i) for i in child_ids]}
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
