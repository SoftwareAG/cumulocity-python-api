# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import pytest

from c8y_api.model import InventoryRole, Permission, ReadPermission, WritePermission, AnyPermission

from tests import RandomNameGenerator


def test_CRUD(live_c8y):
    """Verify that object-oriented create, update and delete works."""

    permissions = [ReadPermission(scope=Permission.Scope.ANY),
                   WritePermission(scope=Permission.Scope.MEASUREMENT, type='c8y_Custom'),
                   AnyPermission(scope=Permission.Scope.ALARM, type='*')]
    role = InventoryRole(name=RandomNameGenerator.random_name(2), description='SomeDescription',
                         permissions=permissions)

    # 1) create role
    role.c8y = live_c8y
    role = role.create()
    # -> ids are set
    assert role.id
    assert all(p.id for p in role.permissions)

    # 2) update the role
    role.description = 'new description'
    del(role.permissions[0])
    updated_role = role.update()
    # -> updated role has all the changed fields
    assert updated_role.id == role.id
    assert updated_role.description == role.description
    # -> the ID of the permissions should persist
    assert {p.id for p in updated_role.permissions} == {p.id for p in role.permissions}

    # 3) delete the role
    role.delete()
    # -> verify that the role is gone
    # (unfortunately this throws a SyntaxError instead of a KeyError)
    with pytest.raises(SyntaxError):
        live_c8y.inventory_roles.get(role.id)


def test_CRUD2(live_c8y):
    """Verify that API-based create, update and delete works."""

    permissions = [ReadPermission(scope=Permission.Scope.ANY),
                   WritePermission(scope=Permission.Scope.MEASUREMENT, type='c8y_Custom'),
                   AnyPermission(scope=Permission.Scope.ALARM, type='*')]
    role = InventoryRole(name=RandomNameGenerator.random_name(2), description='SomeDescription',
                         permissions=permissions)

    # 1) create role
    live_c8y.inventory_roles.create(role)

    # 2) get all roles
    all_roles = live_c8y.inventory_roles.get_all()
    # -> created role can be found
    created_role = next(filter(lambda r: r.name == role.name, all_roles))

    # 3) can be updated
    created_role.description = 'new description'
    live_c8y.inventory_roles.update(created_role)

    # 4) directly grab from DB
    updated_role = live_c8y.inventory_roles.get(created_role.id)
    # -> it was updated
    assert updated_role.description == created_role.description

    # 5) delete the role
    live_c8y.inventory_roles.delete(created_role.id)
    # -> verify that the role is gone
    # (unfortunately this throws a SyntaxError instead of a KeyError)
    with pytest.raises(SyntaxError):
        live_c8y.inventory_roles.get(created_role.id)
