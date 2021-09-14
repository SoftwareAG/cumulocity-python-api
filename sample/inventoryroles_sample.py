# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.app import CumulocityApp
from c8y_api.model import ManagedObject, InventoryRole, \
    Permission, ReadPermission, WritePermission, PermissionLevel, PermissionScope

c8y = CumulocityApp()

print('\nCreate a device group')
dg = ManagedObject(name='New Device Group', type='c8y_DeviceGroup')
dg.add_fragment(name='c8y_IsDeviceGroup')
dg.c8y = c8y
group_id = dg.create()['id']  # todo this is going to change when we parse the result by default
print(f'  New group created. ID: {group_id}')

print('\nCreate a new inventory role')
ir = InventoryRole(name='New Inventory Role', description='Newly created inventory role for test purposes',
                   permissions=[ReadPermission(type='c8y_Device'), WritePermission(type='c8y_Device'),
                                Permission(level=PermissionLevel.ANY, scope=Permission.Scope.EVENT)])
ir.c8y = c8y

created_ir = ir.create()
print(f'  ID: {created_ir.id}')
print(f'  Name: {created_ir.name}')
print(f'  Desc: {created_ir.description}')
print(f'  Permissions: {created_ir.permissions}')

print('\nAssign inventory role to current user')
current_user = c8y.users.get(c8y.username)
current_user.assign_inventory_roles(group_id=group_id, role_ids=[created_ir.id])
assignments = current_user.retrieve_inventory_role_assignments()
for assignment in assignments:
    print(f'  Assigned: {assignment.group} -> {[role.name for role in assignment.roles]}')

input("[ENTER] to continue and cleanup ...")

for assignment in assignments:
    assignment.delete()
created_ir.delete()
c8y.inventory.delete(group_id)
