# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

from typing import Generator, List

from c8y_api._base_api import CumulocityRestApi
from c8y_api.model._base import CumulocityResource, SimpleObject
from c8y_api.model._parser import SimpleObjectParser, ComplexObjectParser
from c8y_api.model._util import _DateUtil


class PermissionUtil:
    """Utility functions to work with the Permission API."""

    @staticmethod
    def build_reference(permission_id: str) -> dict:
        """Build the JSON for a Cumulocity reference to a permission."""
        # Luckily these references don't need the tenant ID
        return {'role': {'self': f'user/roles/{permission_id}'}}


class Permission(SimpleObject):
    """Represents an Permission object within Cumulocity.

    Notes:
      - Permissions are not created/deleted but only assigned to users or
        global roles

    See also: https://cumulocity.com/api/#tag/Roles
    """

    class Level(object):
        """Permission levels."""
        ANY = '*'
        READ = 'READ'
        WRITE = 'ADMIN'

    class Scope(object):
        """Permission scopes."""
        ANY = '*'
        ALARM = 'ALARM'
        AUDIT = 'AUDIT'
        EVENT = 'EVENT'
        MEASUREMENT = 'MEASUREMENT'
        MANAGED_OBJECT = 'MANAGED_OBJECT'
        OPERATION = 'OPERATION'

    _parser = SimpleObjectParser({
            'level': 'permission',
            'type': 'type',
            'scope': 'scope'})

    def __init__(self, level: str = Level.ANY, scope: str = Scope.ANY, type: str = '*'):
        """Create a new Permission instance.

        Args:
            level (str): One of ADMIN, READ, * (default)
            scope (str): One of ALARM, AUDIT, EVENT, MEASUREMENT,
                MANAGED_OBJECT, OPERATION, or * (default)
            type (str): Type on which to restrict or * (default)
        """
        super().__init__(c8y=None)
        self.level = level
        self.type = type
        self.scope = scope

    @classmethod
    def from_json(cls, object_json: dict) -> Permission:
        # no doc change required
        return cls._from_json(object_json, Permission())

    def to_json(self, only_updated=False) -> dict:
        # no doc change required
        json = self._to_json()
        # for permissions it is actually ok to give the ID if there is any
        # for updates, this will create less objects within the database
        if self.id:
            # permission IDs are actually ints
            json['id'] = int(self.id)
        return json


class ReadPermission(Permission):
    """Prepresents a read permission within Cumulocity."""
    # pylint: disable=abstract-method
    def __init__(self, scope=Permission.Scope.ANY, type='*'):  # noqa
        super().__init__(level=Permission.Level.READ, scope=scope, type=type)


class WritePermission(Permission):
    """Prepresents a write permission within Cumulocity."""
    # pylint: disable=abstract-method
    def __init__(self, scope=Permission.Scope.ANY, type='*'):  # noqa
        super().__init__(level=Permission.Level.WRITE, scope=scope, type=type)


class AnyPermission(Permission):
    """Prepresents a read/write permission within Cumulocity."""
    # pylint: disable=abstract-method
    def __init__(self, scope=Permission.Scope.ANY, type='*'):  # noqa
        super().__init__(level=Permission.Level.ANY, scope=scope, type=type)


class InventoryRole(SimpleObject):
    """Represent an instance of an inventory role object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    Inventory Role API.
    Use this class to create new or update inventory role objects.

    See also: https://cumulocity.com/api/#tag/Inventory-Roles
    """

    _parser = SimpleObjectParser({
            '_u_name': 'name',
            '_u_description': 'description'})
    _resource = '/user/inventoryroles'

    def __init__(self, c8y: CumulocityRestApi = None, name: str = None, description: str = None,
                 permissions: List[Permission] = None):
        """Create a new InventoryRole instance.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            name (str):  Name of the inventory role
            description (str):  A description for the inventory role
            permissions (List[Permission]):  A collection of permissions that
                the inventory role assembles
        """
        super().__init__(c8y)
        self._u_name = name
        self._u_description = description
        self.permissions = permissions if permissions else []

    name = SimpleObject.UpdatableProperty('_u_name')
    description = SimpleObject.UpdatableProperty('_u_description')

    @classmethod
    def from_json(cls, json: dict) -> InventoryRole:
        # no doc change required
        obj = super()._from_json(json, InventoryRole())
        obj.permissions = list(map(lambda p: Permission.from_json(p), json['permissions']))
        return obj

    def to_json(self, only_updated=False) -> dict:
        # no doc change required
        json = super()._to_json(only_updated)
        json['permissions'] = list(map(lambda p: p.to_json(), self.permissions))
        return json

    def create(self) -> InventoryRole:
        """Create the role within the database.

        Returns:
            A fresh InventoryRole object representing what was
            created within the database (including the ID).
        """
        return super()._create()

    def update(self) -> InventoryRole:
        """Update the role within the database.

        Note: This will only send changed fields to increase performance.

        Returns:
            A fresh InventoryRole object representing the updated
            database state (including the ID).
        """
        return super()._update()

    def delete(self):
        """Delete the role within the database."""
        super()._delete()


class InventoryRoleAssignment(SimpleObject):
    __parser = SimpleObjectParser({
            'id': 'id',
            'group': 'managedObject'})

    def __init__(self, c8y=None, username=None, group=None, roles=None):
        """
        :param c8y:
        :param username: user to which to assign the inventory roles
        :param group: id of the group on which to assign the inventory roles
        :param roles: list of inventory role objects to assign
        """
        super().__init__(c8y)
        self.id = None
        self.username = username
        self.group = group
        self.roles = roles if roles else []

    @classmethod
    def from_json(cls, object_json):
        r = cls.__parser.from_json(object_json, InventoryRoleAssignment())
        r.roles = list(map(lambda p: InventoryRole.from_json(p), object_json['roles']))
        return r

    def to_full_json(self):
        j = self.__parser.to_full_json(self)
        j['roles'] = list(map(lambda r: r._from_json(), self.roles))
        return j

    def to_diff_json(self):
        return self.to_full_json()

    def create(self, ignore_result=False):
        """Will write the object to the database as a new instance."""
        self._assert_c8y()
        base_path = f'/user/{self.c8y.tenant_id}/users/{self.username}/roles/inventory'
        result_json = self.c8y.post(base_path, self.to_full_json())
        if not ignore_result:
            return self.from_json(result_json)
        return None

    def update(self, ignore_result=False):
        """Will update the Inventory Role object"""
        self._assert_c8y()
        result_json = self.c8y.put(self._build_object_path(), self.to_diff_json())
        if not ignore_result:
            return self.from_json(result_json)
        return None

    def delete(self):
        """Will delete the object within the database."""
        self._assert_c8y()
        self._assert_username()
        self.c8y.delete(self._build_object_path())

    def _build_object_path(self):
        return f'/user/{self.c8y.tenant_id}/users/{self.username}/roles/inventory/{self.id}'

    def _assert_username(self):
        if not self.username:
            raise ValueError("Username must be provided.")


class GlobalRole(SimpleObject):
    """Represents an Global Role object within Cumulocity.

    Notes:
      - Global Roles are called 'groups' in the Cumulocity Standard REST API;
        However, 'global roles' is the official concept name and therefore
        used for consistency with the Cumulocity realm.

      - Only a limited set of properties are actually updatable. Others must
        be set explicitely using the corresponding API (for example: permissions).

    See also: https://cumulocity.com/api/#tag/Groups
    """

    _parser = SimpleObjectParser({
            'id': 'id',
            '_u_name': 'name',
            '_u_description': 'description'})
    _resource = 'INVALID'  # needs to be dynamically generated. see _build_resource_path
    _accept = CumulocityRestApi.ACCEPT_GLOBAL_ROLE
    _custom_properties_parser = ComplexObjectParser({}, [])

    def __init__(self, c8y=None, name=None, description=None):
        super().__init__(c8y)
        self._u_name = name
        self._u_description = description
        self.permission_ids = set()
        self.application_ids = set()

    name = SimpleObject.UpdatableProperty('_u_name')
    description = SimpleObject.UpdatableProperty('_u_description')

    @classmethod
    def from_json(cls, role_json) -> GlobalRole:
        # no doc change
        role: GlobalRole = cls._from_json(role_json, GlobalRole())
        # role ID are int for some reason - convert for consistency
        role.id = str(role.id)
        if role_json['roles'] and role_json['roles']['references']:
            role.permission_ids = {ref['role']['id'] for ref in role_json['roles']['references']}
        if role_json['applications']:
            role.application_ids = {ref['id'] for ref in role_json['applications']}
        return role

    # custom implementation for to_json not required

    def create(self) -> GlobalRole:
        return super()._create()

    def update(self) -> GlobalRole:
        return super()._update()

    def delete(self):
        super()._delete()

    def add_permissions(self, *permissions: str):
        """Add permissions to a global role.

        This operation is executed immediately.

        Args:
            permissions (*str):  An Iterable of permission ID
        """
        super()._assert_c8y()
        super()._assert_id()
        GlobalRoles(self.c8y).assign_permissions(self.id, *permissions)

    def remove_permissions(self, *permissions):
        """Remove permissions from a global role.

        This operation is executed immediately.

        Args:
            permissions (*str):  An Iterable of permission ID
        """
        super()._assert_c8y()
        super()._assert_id()
        GlobalRoles(self.c8y).unassign_permissions(self.id, *permissions)

    def add_users(self, *users: str):
        """Add users to a global role.

        This operation is executed immediately.

        Args:
            users (*str):  An Iterable of usernames
        """
        super()._assert_c8y()
        super()._assert_id()
        GlobalRoles(self.c8y).assign_users(self.id, *users)

    def remove_users(self, *users: str):
        """Remove users from a global role.

        This operation is executed immediately.

        Args:
            users (*str):  An Iterable of usernames
        """
        super()._assert_c8y()
        super()._assert_id()
        GlobalRoles(self.c8y).unassign_users(self.id, *users)

    def _build_resource_path(self):
        # overriding the default as we need the tenand ID in there
        return f'/user/{self.c8y.tenant_id}/groups'


class UserUtil:
    """Utility functions to work with the User API."""

    @staticmethod
    def build_user_reference(tenant_id: str, username: str) -> dict:
        return {'user': {'self': f'/user/{tenant_id}/users/{username}'}}

    @staticmethod
    def build_owner_reference(user_id: str) -> dict:
        return {'owner': user_id}

    @staticmethod
    def build_delegate_reference(user_id: str) -> dict:
        return {'delegatedBy': user_id}

    @staticmethod
    def build_application_references(*ids):
        if not ids:
            return []
        return [{'id': str(aid), 'type': 'MICROSERVICE'} for aid in ids]


class User(SimpleObject):
    """Represents an User object within Cumulocity.

    Notes:
      - Only a limited set of properties are actually updatable. Others must
        be set explicitely using the corresponding API (for example: global roles, permissions,
        owner, etc.)
    """

    _parser = SimpleObjectParser({
            'username': 'userName',
            'password_strength': 'passwordStrength',
            'owner': 'owner',
            'delegated_by': 'delegatedBy',
            '_u_email': 'email',
            '_u_enabled': 'enabled',
            '_u_display_name': 'displayName',
            '_u_password': 'password',
            '_u_first_name': 'firstName',
            '_u_last_name': 'lastName',
            '_u_tfa_enabled': 'twoFactorAuthenticationEnabled',
            '_u_require_password_reset': 'shouldResetPassword',
            '_password_reset_mail': 'sendPasswordResetEmail',
            '_last_password_change': 'lastPasswordChange'})
    _resource = 'INVALID'  # needs to be dynamically generated. see _build_resource_path
    _accept = CumulocityRestApi.ACCEPT_USER
    _custom_properties_parser = ComplexObjectParser({}, [])

    def __init__(self, c8y=None, username=None, email=None, enabled=True, display_name=None,
                 password=None, first_name=None, last_name=None, phone=None,
                 tfa_enabled=None, require_password_reset=None):
        """
        :param c8y:
        :param username:
        :param email:
        :param enabled:
        :param display_name:
        :param password:  the initial password for the user
            if omitted, a newly created user will be send a password reset link
            (for human users)
        :param first_name:
        :param last_name:
        :param phone:
        """
        super().__init__(c8y)
        self.username = username
        self.password_strength = None
        self.owner = None
        self.delegated_by = None
        self._u_email = email
        self._u_enabled = enabled
        self._u_display_name = display_name
        self._u_password = password
        self._u_phone = phone
        self._u_first_name = first_name
        self._u_last_name = last_name
        self._u_tfa_enabled = tfa_enabled or False
        self._u_require_password_reset = require_password_reset
        self._password_reset_mail = not self._u_password
        self._last_password_change = None
        self.global_role_ids = set()
        self.permission_ids = set()
        self.application_ids = set()
        # self.custom_properties = WithUpdatableFragments()

    display_name = SimpleObject.UpdatableProperty('_u_display_name')
    email = SimpleObject.UpdatableProperty('_u_email')
    phone = SimpleObject.UpdatableProperty('_u_phone')
    first_name = SimpleObject.UpdatableProperty('_u_first_name')
    last_name = SimpleObject.UpdatableProperty('_u_last_name')
    enabled = SimpleObject.UpdatableProperty('_u_enabled')
    tfa_enabled = SimpleObject.UpdatableProperty('_u_tfa_enabled')
    require_password_reset = SimpleObject.UpdatableProperty('_u_require_password_reset')

    @property
    def last_password_change(self):
        # hint: could be cached, but it is rarely accessed multiple times
        return _DateUtil.to_datetime(self._last_password_change)

    @classmethod
    def from_json(cls, user_json) -> User:
        user = cls._from_json(user_json, User())
        if user_json['groups'] and user_json['groups']['references']:
            user.global_role_ids = {str(ref['group']['id']) for ref in user_json['groups']['references']}
        if user_json['roles'] and user_json['roles']['references']:
            user.permission_ids = {ref['role']['id'] for ref in user_json['roles']['references']}
        if 'applications' in user_json:
            user.application_ids = {x['id'] for x in user_json['applications']}
        # if user_json['customProperties']:
        #     user.custom_properties = cls.__custom_properties_parser.from_json(user_json['customProperties'],
        #                                                                       WithUpdatableFragments())
        return user

    # no need to override the standard to_json method

    def create(self) -> User:
        return self._create()

    def update(self) -> User:
        self._assert_c8y()
        self._assert_username()
        result_json = self.c8y.put(self._build_user_path(), self.to_diff_json(), accept=self._accept)
        return self.from_json(result_json)

    def delete(self):
        self._delete()

    def update_password(self, new_password):
        pass

    def set_owner(self, user_id: str):
        """Set the owner for this user.

        This function is applied immediately.

        Params:
            user_id (str): ID of the owner to set; can be None to
                remove a currently set owner.
        """
        self._assert_c8y()
        self._assert_username()
        Users(self.c8y).set_owner(self.username, user_id)

    def set_delegate(self, user_id: str):
        """Set the delegate for this user.

        This function is applied immediately.

        Params:
            user_id (str): ID of the delegate to set; can be None to
                remove a currently set delegate.
        """
        self._assert_c8y()
        self._assert_username()
        Users(self.c8y).set_delegate(self.username, user_id)

    def assign_global_role(self, role_id):
        self._assert_c8y()
        self._assert_username()
        GlobalRoles(self.c8y).assign_users(role_id, self.username)

    def unassign_global_role(self, role_id):
        self._assert_c8y()
        self._assert_username()
        GlobalRoles(self.c8y).unassign_users(role_id, self.username)

    def retrieve_global_roles(self):
        self._assert_c8y()
        self._assert_username()
        return GlobalRoles(self.c8y).get_all(self.username)

    def retrieve_inventory_role_assignments(self):
        self._assert_c8y()
        self._assert_username()
        return InventoryRoles(self.c8y).get_all_assignments(self.username)

    def assign_inventory_roles(self, group_id, role_ids):
        """Assign an inventory role for a specific device group.

        The assignment is executed immediately. No call to :ref:`update`
        is required.

        :param group_id  object ID of an existing device group
        :param role_ids  object ID of an existing inventory role
        """
        self._assert_c8y()
        roles_path = self._build_user_path() + '/roles/inventory'
        assignment_json = {'managedObject': group_id, 'roles': [{'id': rid} for rid in role_ids]}
        self.c8y.post(roles_path, assignment_json)

    def _build_resource_path(self):
        # overriding the default as we need the tenant ID in there
        return f'/user/{self.c8y.tenant_id}/users'

    def _build_user_path(self):
        return f'/user/{self.c8y.tenant_id}/users/{self.username}'

    def _build_object_path(self):
        # overriding the default as the username is the relevant ID
        return self._build_user_path()

    def _assert_username(self):
        if not self.username:
            raise ValueError("Username must be provided.")


class InventoryRoles(CumulocityResource):
    """Provides access to the InventoryRole API.

    This class can be used for get, search for, create, update and
    delete inventory roles within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Inventory-Roles
    """

    def __init__(self, c8y):
        super().__init__(c8y, '/user/inventoryroles')
        self.object_name = "roles"

    def get(self, id: str | int) -> InventoryRole:
        """Get a specific inventory role object.

        Args:
            id (str|int): Cumulocity ID of the inventory role

        Returns:
            An InventoryRole instance for this ID

        Raises:
            SyntaxError if the ID is not defined.

        Note: In contrast to other API the InventoryRole API does not raise
        an KeyError (i.e. 404) for undefined ID but a SyntaxError (HTTP 500).
        """
        role = InventoryRole.from_json(self._get_object(id))
        role.c8y = self.c8y  # inject c8y connection into instance
        return role

    def select(self, limit: int = None, page_size: int = 1000) -> Generator[InventoryRole]:
        """Get all defined inventory roles.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        Note: The InventoryRole API does not support filters.

        Args:
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of objects read (and parsed
                in one chunk). This is a performance related setting.

        Returns:
            Generator for InventoryRole objects
        """
        base_query = self._build_base_query(page_size=page_size)
        return super()._iterate(base_query, limit, InventoryRole.from_json)

    def get_all(self, limit: int = None, page_size: int = 1000) -> List[InventoryRole]:
        """Get all defined inventory roles.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        See `select` for a documentation of arguments.

        Returns:
            List of InventoryRole objects
        """
        return list(self.select(limit=limit, page_size=page_size))

    def select_assignments(self, username):
        query = f'/user/{self.c8y.tenant_id}/users/{username}/roles/inventory'
        assignments_json = self.c8y.get(query)
        for j in assignments_json['inventoryAssignments']:
            result = InventoryRoleAssignment.from_json(j)
            result.username = username  # username is not part of the parse json and needs to be injected
            result.c8y = self.c8y  # inject c8y connection into instance
            yield result

    def get_all_assignments(self, username):
        return list(self.select_assignments(username))

    def create(self, *roles: InventoryRole):
        """Create objects within the database.

        Args:
            roles (*InventoryRole):  Collection of InventoryRole instances
        """
        super()._create(InventoryRole.to_full_json, *roles)

    def update(self, *roles: InventoryRole):
        """Write changes to the database.

        Args:
            roles (*InventoryRole):  Collection of InventoryRole instances
        """
        super()._update(InventoryRole.to_diff_json, *roles)


class Users(CumulocityResource):
    """Provides access to the User API.

    See also: https://cumulocity.com/api/#tag/Users
    """

    def __init__(self, c8y):
        super().__init__(c8y, 'user/' + c8y.tenant_id + '/users')
        self.__groups = GlobalRoles(c8y)

    def get(self, username):
        """Retrieve a specific user.

        :param username The ID of the user (usually the mail address)
        :rtype User
        """
        user = User.from_json(self._get_object(username))
        user.c8y = self.c8y  # inject c8y connection into instance
        return user

    def select(self, username=None, groups=None, page_size=5):
        """Lazily select and yield User instances.

        The result can be limited by username (prefix) and/or group membership.

        :param username: A user's username or a prefix thereof
        :param groups: a scalar or list of int (actual group ID), string (group names),
            or actual Group instances
        :param page_size:  Number of results fetched per request
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
            elif isinstance(groups[0], GlobalRole):
                groups_string = [str(g.id) for g in groups]
            elif isinstance(groups[0], str):
                groups_string = [str(self.__groups.get(name).id) for name in groups]
            else:
                ValueError("Unable to identify type of given group identifiers.")
            groups_string = ','.join(groups_string)
        # lazily yield parsed objects page by page
        base_query = super()._build_base_query(username=username, groups=groups_string, page_size=page_size)
        page_number = 1
        while True:
            page_results = [User.from_json(x) for x in self._get_page(base_query, page_number)]
            if not page_results:
                break
            for user in page_results:
                user.c8y = self.c8y  # inject c8y connection into instance
                yield user
            page_number = page_number + 1

    def get_all(self, username=None, groups=None, page_size=1000):
        """Select and retrieve User instances as list.

        The result can be limited by username (prefix) and/or group membership.

        :param username: A user's username or a prefix thereof
        :param groups: a scalar or list of int (actual group ID), string (group names),
            or actual Group instances
         :param page_size:  Maximum number of entries fetched per requests;
            this is a performance setting
        :rtype: List of User
        """
        return list(self.select(username, groups, page_size))

    def create(self, *users):
        super()._create(lambda u: u._to_full_json(), *users)   # noqa

    def set_owner(self, user_id: str, owner_id: str):
        """Set the owner of a given user.

        Params:
            user_id (str): The user to set an owner for
            owner_id (str):  The Id of the owner user; Can be None to
                unassign/remove the current owner
        """
        if owner_id:
            self.c8y.put(self.build_object_path(user_id) + '/owner', UserUtil.build_owner_reference(owner_id))
        else:
            self.c8y.delete(self.build_object_path(user_id) + '/owner')

    def set_delegate(self, user_id: str, delegate_id: str):
        """Set the delegate of a given user.

        Params:
            user_id (str): The user to set an owner for
            delegate_id (str):  The Id of the delegate user; Can be None to
                unassign/remove the current owner
        """
        if delegate_id:
            self.c8y.put(self.build_object_path(user_id) + '/delegatedby',
                         UserUtil.build_delegate_reference(delegate_id))
        else:
            self.c8y.delete(self.build_object_path(user_id) + '/delegatedby')


class GlobalRoles(CumulocityResource):
    """Provides access to the Global Role API.

    Notes:
      - Global Roles are called 'groups' in the Cumulocity Standard REST API;
        However, 'global roles' is the official concept name and therefore
        used for consistency with the Cumulocity realm.

    See also: https://cumulocity.com/api/#tag/Groups
    """

    def __init__(self, c8y):
        super().__init__(c8y, 'user/' + c8y.tenant_id + '/groups')
        self._global_roles_by_name = None

    def reset_caches(self):
        """Reset internal caching.

        Caches are used for lookups of global roles by name.
        """
        self._global_roles_by_name = None

    def get(self, role_id: int | str) -> GlobalRole:
        """Retrieve a specific global role.

        Note:  The C8Y REST API does not support direct query by name. Hence,
        searching by name will actually retrieve all available groups and
        return the matching ones.
        These groups will be cached internally for subsequent calls.

        See also method `reset_caches`

        Args:
            role_id (int|str):  An actual global role ID as int/string or a
                global role name

        Returns:
            A GlobalRole instance for the ID/name.
        """
        try:
            # the following will fail if the ID is not int-like
            role_id = str(int(role_id))
            return GlobalRole.from_json(super()._get_object(role_id))
        except ValueError:
            if not self._global_roles_by_name:
                self._global_roles_by_name = {g.name: g for g in self.get_all()}
            return self._global_roles_by_name[role_id]

    def select(self, username: str = None, page_size: int = 5) -> Generator[GlobalRole]:
        """Iterate over global roles.

        Args:
            username (str): Retrieve global roles assigned to a specified user
                If omitted, all available global roles are returned
            page_size (int): Maximum number of entries fetched per requests;
                this is a performance setting

        Return:
            Generator of GlobalRole instances
        """
        if username:
            # select by username
            query = f'/user/{self.c8y.tenant_id}/users/{username}/groups?pageSize={page_size}&currentPage='
            page_number = 1
            while True:
                response_json = self.c8y.get(query + str(page_number))
                references = response_json['references']
                if not references:
                    break
                for ref_json in references:
                    result = GlobalRole.from_json(ref_json['group'])
                    result.c8y = self.c8y  # inject c8y connection into instance
                    yield result
                page_number = page_number + 1
        else:
            # select all
            query = self._build_base_query(page_size=page_size)
            page_number = 1
            while True:
                role_jsons = self._get_page(query, page_number)
                if not role_jsons:
                    break
                for role_json in role_jsons:
                    result = GlobalRole.from_json(role_json)
                    result.c8y = self.c8y
                    yield result
                page_number = page_number + 1

    def get_all(self, username: str = None, page_size: int = 1000) -> List[GlobalRole]:
        """Retrieve global roles.

        Args:
            username (str): Retrieve global roles assigned to a specified user
                If omitted, all available global roles are returned
            page_size (int): Maximum number of entries fetched per requests;
                this is a performance setting

        Return:
            List of GlobalRole instances
        """
        return list(self.select(username, page_size))

    def assign_users(self, role_id: int | str, *usernames: str):
        """Add users to a global role.

        Args:
            role_id (int|str):  Technical ID of the global role
            usernames (*str):  Iterable of usernames to assign
        """
        path = self.build_object_path(role_id) + '/users'
        for username in usernames:
            user_reference = UserUtil.build_user_reference(self.c8y.tenant_id, username)
            self.c8y.post(path, user_reference, accept='')

    def unassign_users(self, role_id: int | str, *usernames: str):
        """Remove users from a global role.

        Args:
            role_id (int|str):  Technical ID of the global role
            usernames (*str):  Iterable of usernames to unassign
        """
        base_path = self.build_object_path(role_id) + '/users/'
        for username in usernames:
            self.c8y.delete(base_path + username)

    def assign_permissions(self, role_id: int | str, *permissions: str):
        """Add permissions to a global role.

        Args:
            role_id (int|str):  Technical ID of the global role
            permissions (*str):  Iterable of permission ID to assign
        """
        # permissions are called 'roles' in the Cumulocity datamodel
        path = self.build_object_path(role_id) + '/roles'
        for permission in permissions:
            reference = PermissionUtil.build_reference(permission)
            self.c8y.post(path, reference, accept='')

    def unassign_permissions(self, role_id: int | str, *permissions: str):
        """Remove permissions from a global role.

        Args:
            role_id (int|str):  Technical ID of the global role
            permissions (*str):  Iterable of permission ID to assign
        """
        # permissions are called 'roles' in the Cumulocity datamodel
        base_path = self.build_object_path(role_id) + '/roles/'
        for permission in permissions:
            self.c8y.delete(base_path + permission)
