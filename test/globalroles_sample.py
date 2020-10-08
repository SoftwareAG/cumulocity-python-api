from c8y_app import CumulocityApi
from c8y_model import GlobalRole

c8y = CumulocityApi()

role = GlobalRole(name='new_role', description='description', permission_ids=['ROLE_ALARM_READ', 'ROLE_EVENT_READ'])
role.c8y = c8y
created_role1 = role.create(True)

print(created_role1.id)
print(created_role1.name)
print(created_role1.description)
print(created_role1.permission_ids)

role_update = GlobalRole()
role_update.description = 'updated description'
role_update.permission_ids.add('ROLE_AUDIT_READ')
# role_update.permission_ids.remove('ROLE_ALARM_READ')

# updated_role1 = role_update.update(created_role1, parse=True)
#
# print(updated_role1.id)
# print(updated_role1.name)
# print(updated_role1.description)
# print(updated_role1.permission_ids)

created_role1.c8y = c8y
created_role1.delete()
