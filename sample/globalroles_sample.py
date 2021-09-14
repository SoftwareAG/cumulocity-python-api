# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.app import CumulocityApp
from c8y_api.model import GlobalRole

c8y = CumulocityApp()

role = GlobalRole(name='new_role', description='description', permission_ids=['ROLE_ALARM_READ', 'ROLE_EVENT_READ'])
role.c8y = c8y
created_role = role.create()

print(created_role.id)
print(created_role.name)
print(created_role.description)
print(created_role.permission_ids)

created_role.description = 'updated description'
created_role.permission_ids.add('ROLE_AUDIT_READ')
created_role.permission_ids.remove('ROLE_ALARM_READ')
updated_role = created_role.update()

print("Global role after update:")
print("  Name: " + updated_role.name)
print("  Desc: " + updated_role.description)
print("  Permissions: " + ', '.join(updated_role.permission_ids))

updated_role.delete()

for role in c8y.global_roles.select():
    print(role.name)
