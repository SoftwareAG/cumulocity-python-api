from c8y_app import CumulocityApi
from c8y_model import GlobalRole

c8y = CumulocityApi()

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
