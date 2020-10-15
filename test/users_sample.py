from c8y_api.app import CumulocityApi
from c8y_api.model import User

c8y = CumulocityApi()
current_user = c8y.users.get(c8y.username)

print("Current User:")
print(f"User:            {current_user.user_id}")
print(f"Alias:           {current_user.display_name}")
print(f"Password Change: {current_user.last_password_change.isoformat()}")
print(f"Permissions:     {current_user.permission_ids}")
print(f"Roles:           {current_user.global_role_ids}")

print("\nCurrent user JSON:")
print(current_user._to_full_json())

print("\nPermissions:")
for role_id in current_user.permission_ids:
    print(f" - {role_id}")

print("\nGlobal Roles:")
for role_id in current_user.global_role_ids:
    g = c8y.global_roles.get(role_id)
    print(f" - {g.name} ({g.id})")

print("\nCreate new human users with password:")
new_user = User(username='sou', email='sou@softwareag.com', password='password', enabled=True,
                global_role_ids=[8])
new_user.c8y = c8y
new_user.create()

db_user = c8y.users.get('sou')
print(f"  Require Password Reset: {db_user.require_password_reset}")
print(f"  Permissions:   {db_user.global_role_ids}")
print(f"  Global Roles:: {db_user.permission_ids}")

print("\nUpdate user in DB:")
db_user.require_password_reset = True
db_user.permission_ids = {'ROLE_AUDIT_READ'}
db_user.global_role_ids.remove(8)
db_user.global_role_ids.add(3)
updated_user = db_user.update()

print("\nUpdate/Diff JSON after changes:")
print(f"  Require Password Reset: {updated_user.require_password_reset}")
print(f"  Global Roles: {updated_user.global_role_ids}")
print(f"  Permissions: {updated_user.permission_ids}")

print('\nDeleting previously created user:')
updated_user.delete()
try:
    users = c8y.users.get("sou")
    assert False
except KeyError:
    pass

print("\nFinding users by name prefix:")
users = c8y.users.select(username='Chris')
for user in users:
    print(f"Found: {user.email}")

print("\nFinding users by group membership:")
users = c8y.users.select()
for user in users:
    print(f"Found: {user.email}")


