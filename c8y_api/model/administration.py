# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._util import _DateUtil
from c8y_api.model._parser import SimpleObjectParser, ComplexObjectParser
from c8y_api.model._updatable import _UpdatableProperty, _UpdatableSetProperty
from c8y_api.model._base import CumulocityResource, SimpleObject, WithUpdatableFragments


class PermissionLevel(object):
    ANY = '*'
    READ = 'READ'
    WRITE = 'ADMIN'


class PermissionScope(object):
    ANY = '*'
    ALARM = 'ALARM'
    AUDIT = 'AUDIT'
    EVENT = 'EVENT'
    MEASUREMENT = 'MEASUREMENT'
    MANAGED_OBJECT = 'MANAGED_OBJECT'
    OPERATION = 'OPERATION'


class Permission(SimpleObject):

    __parser = SimpleObjectParser({
            'id': 'id',
            'level': 'permission',
            'type': 'type',
            'scope': 'scope'})

    def __init__(self, level=PermissionLevel.ANY, scope=PermissionScope.ANY, type='*'):  # noqa
        """
        :param level: one of ADMIN, READ, * (default)
        :param type: type on which to restrict or * (default)
        :param scope: one of ALARM, AUDIT, EVENT, MEASUREMENT, MANAGED_OBJECT, OPERATION, or * (default)
        """
        super().__init__(None)
        self.id = None
        self.level = level
        self.type = type
        self.scope = scope

    @classmethod
    def from_json(cls, object_json):
        p = cls.__parser.from_json(object_json, Permission())
        return p

    def to_full_json(self):
        return self.__parser.to_full_json(self)


class ReadPermission(Permission):
    def __init__(self, scope=PermissionScope.ANY, type='*'):  # noqa
        super().__init__(level=PermissionLevel.READ, scope=scope, type=type)


class WritePermission(Permission):
    def __init__(self, scope=PermissionScope.ANY, type='*'):  # noqa
        super().__init__(level=PermissionLevel.WRITE, scope=scope, type=type)


class AnyPermission(Permission):
    def __init__(self, scope=PermissionScope.ANY, type='*'):  # noqa
        super().__init__(level=PermissionLevel.ANY, scope=scope, type=type)


class InventoryRole(SimpleObject):

    __parser = SimpleObjectParser({
            'id': 'id',
            '_u_name': 'name',
            '_u_description': 'description'})

    def __init__(self, id=None, c8y=None, name=None, description=None, permissions=None):  # noqa
        """
        :param c8y:
        :param name: name of the inventory role
        """
        super().__init__(c8y)
        self.id = id
        self._u_name = name
        self._u_description = description
        self.permissions = permissions if permissions else []

    name = _UpdatableProperty('_u_name')
    description = _UpdatableProperty('_u_description')

    @classmethod
    def from_json(cls, object_json):
        r = cls.__parser.from_json(object_json, InventoryRole())
        r.permissions = list(map(lambda p: Permission.from_json(p), object_json['permissions']))
        return r

    def to_full_json(self):
        j = self.__parser.to_full_json(self)
        j['permissions'] = list(map(lambda p: p._to_json(), self.permissions))
        return j

    def to_diff_json(self):
        j = self.__parser.to_diff_json(self)
        # the permission list can only be specified as a whole
        j['permissions'] = list(map(lambda p: p._to_json(), self.permissions))
        return j

    def create(self, ignore_result=False):
        """Will write the object to the database as a new instance."""
        self._assert_c8y()
        response_json = self.c8y.post('/user/inventoryroles', self.to_full_json())
        if not ignore_result:
            result = self.from_json(response_json)
            result.c8y = self.c8y
            return result
        return None

    def update(self, ignore_result=False):
        """Will update the Inventory Role object"""
        self._assert_c8y()
        self._assert_id()
        response_json = self.c8y.put(f'/user/inventoryroles/{self.id}', self.to_diff_json())
        if not ignore_result:
            result = self.from_json(response_json)
            result.c8y = self.c8y
            return result
        return None

    def delete(self):
        """Will delete the object within the database."""
        self._assert_c8y()
        self.c8y.delete(f'/user/inventoryroles/{self.id}')


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
        j['roles'] = list(map(lambda r: r._to_json(), self.roles))
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

    __parser = SimpleObjectParser({
            'id': 'id',
            '_u_name': 'name',
            '_u_description': 'description'})

    def __init__(self, c8y=None, name=None, description=None, permission_ids=None):
        super().__init__(c8y)
        self.id = None
        self._u_name = name
        self._u_description = description
        self._x_permissions = permission_ids if permission_ids else set()
        self._x_orig_permissions = self._x_permissions

    name = _UpdatableProperty('_u_name')
    description = _UpdatableProperty('_u_description')
    permission_ids = _UpdatableSetProperty('_x_permissions', '_x_orig_permissions')

    @classmethod
    def from_json(cls, role_json):
        role = cls.__parser.from_json(role_json, GlobalRole())
        if role_json['roles']:
            if role_json['roles']['references']:
                role._x_permissions = {ref['role']['id'] for ref in role_json['roles']['references']}
        return role

    def _to_full_json(self):
        """ Return a complete JSON (dict) representation of the object.
        As the 'full' JSON does not include the referenced permissions sensible
        use of this function is module internal. """
        return self.__parser.to_full_json(self)

    def _to_diff_json(self):
        """ Return a difference JSON (dict) representation of the object which
        includes only updated aspects.
        As the JSON does not include the referenced permissions sensible
        use of this function is module internal. """
        return self.__parser.to_diff_json(self)

    def create(self, ignore_result=False):
        self._assert_c8y()
        # 1 create the base object
        base_path = f'/user/{self.c8y.tenant_id}/groups'
        new_id = self.c8y.post(base_path, self._to_full_json())['id']
        object_path = base_path + '/' + str(new_id)
        # 2 assign permissions to new global role
        roles_path = object_path + '/roles'
        for pid in self._x_permissions:
            self.c8y.post(roles_path, self._build_role_reference(pid))
        # 3 get complete object as a result
        if not ignore_result:
            new_obj = self.from_json(self.c8y.get(object_path))
            new_obj.c8y = self.c8y
            return new_obj
        return None

    def update(self, ignore_result=False):
        """
        Write changed aspects to database.

        :param ignore_result  if False (default), the updated object is
            returned as new instance

        Note: The GlobalRole object is spread across multiple database
        concepts that need to be updated separately. Because of this it can
        only be updated directly - it is not possible to apply a 'change' to
        another object.
        """
        self._assert_c8y()
        self._assert_id()
        object_path = f'/user/{self.c8y.tenant_id}/groups/{self.id}'
        # 1 update the base object
        update_json = self._to_diff_json()
        update_json['name'] = self.name  # for whatever reason name must be provided
        self.c8y.put(object_path, update_json)
        # 2 update roles
        if self._x_orig_permissions:
            added = self._x_permissions.difference(self._x_orig_permissions)
            removed = self._x_orig_permissions.difference(self._x_permissions)
            roles_path = object_path + '/roles'
            for pid in added:
                self.c8y.post(roles_path, self._build_role_reference(pid))
            for pid in removed:
                self.c8y.delete(roles_path + '/' + pid)
        # 3 get updated object as result
        if not ignore_result:
            updated_obj = self.from_json(self.c8y.get(object_path))
            updated_obj.c8y = self.c8y
            return updated_obj
        return None

    def delete(self):
        self._assert_c8y()
        self._assert_id()
        object_path = f'/user/{self.c8y.tenant_id}/groups/{self.id}'
        self.c8y.delete(object_path)

    @staticmethod
    def _build_role_reference(role_id):
        return {'role': {'self': 'user/roles/' + role_id}}


class User(SimpleObject):

    __parser = SimpleObjectParser({
            '_user_id': 'id',
            'username': 'userName',
            '_u_owner': 'owner',
            '_u_delegated_by': 'delegatedBy',
            '_u_email': 'email',
            '_u_enabled': 'enabled',  # bool
            '_u_display_name': 'displayName',
            '_u_password': 'password',
            '_u_first_name': 'firstName',
            '_u_last_name': 'lastName',
            '_u_require_password_reset': 'shouldResetPassword',
            '_password_reset_mail': 'sendPasswordResetEmail',
            '_last_password_change': 'lastPasswordChange'})
    __custom_properties_parser = ComplexObjectParser({}, [])

    def __init__(self, c8y=None, username=None, email=None, enabled=True, display_name=None,
                 password=None, first_name=None, last_name=None, phone=None, require_password_reset=None,
                 owner=None, delegated_by=None, permission_ids=None, global_role_ids=None, application_ids=None):
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
        :param owner:  specify the parent/owner user by username
        :param delegated_by:  specify delegate user by username
        :param permission_ids:  the initial set of roles (permissions) for this user
            a newly created user will be assigned these after creation
            Note: human users are usually assigned to groups (global roles)
        :param global_role_ids:  the initial set of groups (global roles) for this user
            a newly created user will be assigned to these after creation
        """
        super().__init__(c8y)
        self.user_id = None
        self.username = username
        self._u_owner = owner
        self._u_delegated_by = delegated_by
        self._u_email = email
        self._u_enabled = enabled
        self._u_display_name = display_name
        self._u_password = password
        self._u_phone = phone
        self._u_first_name = first_name
        self._u_last_name = last_name
        self._u_require_password_reset = require_password_reset
        self._password_reset_mail = not self._u_password
        self._last_password_change = None
        self._x_application_ids = application_ids if application_ids else set()
        self._x_global_roles = global_role_ids if global_role_ids else set()
        self._x_permissions = permission_ids if permission_ids else set()
        self._x_orig_application_ids = None
        self._x_orig_global_roles = None
        self._x_orig_permissions = None
        self.custom_properties = WithUpdatableFragments()

    owner = _UpdatableProperty('_u_owner')
    delegated_by = _UpdatableProperty('_u_delegated_by')
    display_name = _UpdatableProperty('_u_display_name')
    email = _UpdatableProperty('_u_email')
    phone = _UpdatableProperty('_u_phone')
    first_name = _UpdatableProperty('_u_first_name')
    last_name = _UpdatableProperty('_u_last_name')
    enabled = _UpdatableProperty('_u_enabled')
    application_ids = _UpdatableSetProperty('_x_application_ids', '_x_orig_application_ids')
    require_password_reset = _UpdatableProperty('_u_require_password_reset')
    permission_ids = _UpdatableSetProperty('_x_permissions', '_x_orig_permissions')
    global_role_ids = _UpdatableSetProperty('_x_global_roles', '_x_orig_global_roles')

    @property
    def last_password_change(self):
        # hint: could be cached, but it is rarely accessed multiple times
        return _DateUtil.to_datetime(self._last_password_change)

    @classmethod
    def from_json(cls, user_json):
        user = cls.__parser.from_json(user_json, User())
        if 'applications' in user_json:
            user.application_ids = {x['id'] for x in user_json['applications']}
        if user_json['roles']:
            if user_json['roles']['references']:
                user._x_permissions = {ref['role']['id'] for ref in user_json['roles']['references']}
        if user_json['groups']:
            if user_json['groups']['references']:
                user._x_global_roles = {ref['group']['id'] for ref in user_json['groups']['references']}
        if user_json['customProperties']:
            user.custom_properties = cls.__custom_properties_parser.from_json(user_json['customProperties'],
                                                                              WithUpdatableFragments())
        return user

    def _to_full_json(self):
        user_json = self.__parser.to_full_json(self)
        if self.application_ids:
            user_json['applications'] = self._build_application_references(self.application_ids)
        if self.custom_properties:
            user_json['customProperties'] = self.__custom_properties_parser.to_full_json(self.custom_properties)
        return user_json

    def _to_diff_json(self):
        user_json = self.__parser.to_diff_json(self)
        if self._x_orig_application_ids:
            user_json['applications'] = self._build_application_references(self._x_application_ids)
        if self.custom_properties:
            user_json['customProperties'] = self.__custom_properties_parser.to_diff_json(self.custom_properties)
        return user_json

    def create(self, ignore_result=False):
        self._assert_c8y()
        self._assert_username()
        # 1: create the user itself
        base_path = f'/user/{self.c8y.tenant_id}/users'
        self.c8y.post(base_path, self._to_full_json())
        user_path = self._build_user_path()
        # 2: assign to owner if defined
        if self.owner:
            self.c8y.put(user_path + '/owner', self._build_owner_reference())
        # 3: assign delegate if defined
        #   -> no need, is already created through the base JSON
        # if self.delegated_by:
        #     self.c8y.put(user_path + '/delegatedBy', {self._build_delegate_reference())
        # 4: assign user to global roles
        for group_id in self.global_role_ids:
            self.c8y.global_roles.assign_users(group_id, [self.username])
        # 5: assign single permissions to user
        user_roles_path = user_path + '/roles'
        for role_id in self.permission_ids:
            ref_json = self._build_role_reference(role_id)
            self.c8y.post(user_roles_path, ref_json)
        if not ignore_result:
            new_obj = self.from_json(self.c8y.get(user_path))
            new_obj.c8y = self.c8y
            return new_obj
        return None

    def update(self, ignore_result=False):
        # todo: this violates the principle of REST API Resemblance
        """
        Write changed aspects to database.

        :param ignore_result  Do not read and parse the updated object

        Note: The User object is spread across multiple database concepts
        that need to be updated separately. Because of this it can only be
        updated directly - it is not possible to apply a 'change' to
        another object.
        """
        self._assert_c8y()
        self._assert_username()
        user_path = self._build_user_path()
        diff_json = self._to_diff_json()
        # 1: write base object changes
        self.c8y.put(user_path, diff_json)
        # 2: if owner was changed, update separately
        if 'owner' in diff_json:
            owner_path = user_path + '/owner'
            if not self.owner:
                self.c8y.delete(owner_path)
            else:
                self.c8y.put(owner_path, self._build_owner_reference())
        # 3: if delegate is defined, update separately
        if 'delegatedBy' in diff_json:
            delegate_path = user_path + '/delegatedBy'
            if not self.delegated_by:
                self.c8y.delete(delegate_path)
            else:
                self.c8y.put(delegate_path, self._build_delegate_reference(self.delegated_by))
        # 4: assign/unassign user from global roles
        if self._x_orig_global_roles:
            added = self._x_global_roles.difference(self._x_orig_global_roles)
            removed = self._x_orig_global_roles.difference(self._x_global_roles)
            if added:
                for gid in added:
                    self.c8y.global_roles.assign_users(gid, [self.username])
            if removed:
                for gid in removed:
                    self.c8y.global_roles.unassign_users(gid, [self.username])
        # 5: add/remove permissions
        if self._x_orig_permissions:
            added = self._x_permissions.difference(self._x_orig_permissions)
            removed = self._x_orig_permissions.difference(self._x_permissions)
            roles_path = user_path + '/roles'
            for pid in added:
                self.c8y.post(roles_path, self._build_role_reference(pid))
            for pid in removed:
                self.c8y.delete(roles_path + '/' + pid)
        if not ignore_result:
            new_obj = self.from_json(self.c8y.get(user_path))
            new_obj.c8y = self.c8y
            return new_obj
        return None

    def delete(self):
        self._assert_c8y()
        self._assert_username()
        self.c8y.delete(self._build_user_path())

    def update_password(self, new_password):
        pass

    def set_owner(self, user_id):
        self._assert_c8y()
        self._assert_username()
        self.c8y.users.set_owner(self.username, user_id)

    def assign_global_role(self, role_id):
        GlobalRoles(self.c8y).assign_users(role_id, [self.username])

    def unassign_global_role(self, role_id):
        GlobalRoles(self.c8y).unassign_users(role_id, [self.username])

    def retrieve_global_roles(self):
        return GlobalRoles(self.c8y).get_all(self.username)

    def retrieve_inventory_role_assignments(self):
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

    def _build_user_path(self):
        return f'/user/{self.c8y.tenant_id}/users/{self.username}'

    def _build_role_reference(self, role_id):
        return {'role': {'self': f'/users/{self.c8y.tenant_id}/roles/{role_id}'}}

    def _build_user_reference(self):
        return {'user': {'self': f'/user/{self.c8y.tenant_id}/users/{self.username}'}}

    def _build_owner_reference(self):
        return {'owner': self.owner}

    @staticmethod
    def _build_delegate_reference(user_id):
        return {'delegatedBy': user_id}

    @staticmethod
    def _build_application_references(ids):
        if not ids:
            return []
        return [{'id': str(aid), 'type': 'MICROSERVICE'} for aid in ids]

    def _assert_username(self):
        if not self.username:
            raise ValueError("Username must be provided.")


class InventoryRoles(CumulocityResource):

    def __init__(self, c8y):
        super().__init__(c8y, 'user/inventoryroles')
        self.object_name = "roles"

    def get(self, object_id):
        role = InventoryRole.from_json(self._get_object(object_id))
        role.c8y = self.c8y  # inject c8y connection into instance
        return role

    def get_all(self, page_size=1000):
        """Lazy implementation."""
        base_query = self._build_base_query(page_size=page_size)
        page_number = 1
        while True:
            results = [InventoryRole.from_json(x) for x in self._get_page(base_query, page_number)]
            if not results:
                break
            for result in results:
                result.c8y = self.c8y  # inject c8y connection into instance
                yield result
            page_number = page_number + 1

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


class Users(CumulocityResource):

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


class GlobalRoles(CumulocityResource):

    def __init__(self, c8y):
        super().__init__(c8y, 'user/' + c8y.tenant_id + '/groups')
        self.__groups_by_name = None
        self.__groups_by_id = None

    def reset_caches(self):
        """Reset internal caching.

        This resets the following caches:
          * Groups by name (used for all group lookup by name)
        """
        self.__groups_by_name = None
        self.__groups_by_id = None

    def get(self, role_id):
        """Retrieve a specific global role.

        Note:  The C8Y REST API does not support direct query by name. Hence,
        searching by name will actually retrieve all available groups and
        return the matching ones.
        These groups will be cached internally for subsequent calls.

        See also method :py:meth:reset_caches

        :param role_id  a scalar int (actual group ID) or string (group name)
        :rtype Group
        """
        if isinstance(role_id, int):
            return GlobalRole.from_json(super()._get_object(role_id))
        # else: find group by name
        if not self.__groups_by_name:
            self.__groups_by_name = {g.name: g for g in self.get_all()}
        return self.__groups_by_name[role_id]

    def select(self, username=None, page_size=5):
        """Iterate over global roles.

        :param  username  retrieve global roles assigned to a specified user
            If omitted, all available global roles are returned
        :param page_size:  Number of results fetched per request

        :rtype Generator of GlobalRole instances
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

    def get_all(self, username=None, page_size=1000):
        """Retrieve global roles.

        :param username:  retrieve global roles assigned to a specified user
            If omitted, all available global roles are returned
        :param page_size:  Maximum number of entries fetched per requests;
            this is a performance setting.

        :rtype: List of GlobalRole
        """
        return list(self.select(username, page_size))

    def assign_users(self, role_id, usernames):
        """Add users to a global role.

        :param role_id  technical ID (int) of the global role
        :param usernames  technical usernames of the users to assign
        """
        if not isinstance(usernames, list):
            usernames = [usernames]
        path = self._build_object_path(role_id) + '/users'
        for username in usernames:
            user_reference = self._build_user_reference(username)
            self.c8y.post(path, user_reference)

    def unassign_users(self, role_id, usernames):
        """Add users to a global role.

        :param role_id  technical ID (int) of the global role
        :param usernames  technical usernames of the users to assign
        """
        if not isinstance(usernames, list):
            usernames = [usernames]
        base_path = self._build_object_path(role_id) + '/users/'
        for username in usernames:
            self.c8y.delete(base_path + username)

    def _build_user_reference(self, username):
        return {'user': {'self': f'/user/{self.c8y.tenant_id}/users/{username}'}}
