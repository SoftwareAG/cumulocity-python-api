from c8y_app import CumulocityApi
from c8y_model import ManagedObject, InventoryRole, InventoryRoleAssignment, \
    Permission, ReadPermission, WritePermission, AnyPermission, PermissionLevel, PermissionScope

c8y = CumulocityApi()

print('\nCreate a device group')
dg = ManagedObject(name='New Device Group', type='c8y_DeviceGroup')
dg.add_fragment(name='c8y_IsDeviceGroup')
dg.c8y = c8y
group_id = dg.create()['id']  # todo this is going to change when we parse the result by default
print(f'  New group created. ID: {group_id}')

print('\nCreate a new inventory role')
ir = InventoryRole(name='New Inventory Role', description='Newly created inventory role for test purposes',
                   permissions=[ReadPermission(type='c8y_Device'), WritePermission(type='c8y_Device'),
                                Permission(level=PermissionLevel.ANY, scope=PermissionScope.EVENT)])
ir.c8y = c8y
created_ir = ir.create()
print(f'  ID: {created_ir.id}')
print(f'  Name: {created_ir.name}')
print(f'  Desc: {created_ir.description}')
print(f'  Permissions: {created_ir.permissions}')

print('\nAssign inventory role to current user')
current_user = c8y.users.get(c8y.username)
print(current_user)

ira = InventoryRoleAssignment(username=current_user.username, group=group_id, roles=[created_ir])
ira.c8y = c8y
created_ira = ira.create()

input("[ENTER] to continue and cleanup ...")

created_ira.delete()
created_ir.delete()
c8y.inventory.delete(group_id)