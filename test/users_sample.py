from c8y_app import CumulocityApi
from c8y_model import User

c8y = CumulocityApi()
current_user = c8y.users.get(c8y.username)

print("Current User:")
print(f"User:            {current_user.user_id}")
print(f"Alias:           {current_user.display_name}")
print(f"Password Change: {current_user.last_password_change.isoformat()}")
print(f"Role ID:         {current_user.role_ids}")
print(f"Group ID:        {current_user.group_ids}")

print("\nCurrent user JSON:")
print(current_user.to_full_json())

print("\nRoles:")
for role_id in current_user.role_ids:
    print(f" - {role_id}")

print("\nGroups:")
for group_id in current_user.group_ids:
    g = c8y.groups.get(group_id)
    print(f" - {g.name} ({g.id})")

print("\nCreate new human users with password:")
new_user = User(username='sou', email='sou@softwareag.com', password='password',
                groups=[1, 8], roles=['ROLE_INVENTORY_CREATE'])
new_user.c8y = c8y
new_user.create()

db_user = c8y.users.get('sou')
print(f"  Password: {db_user.password}")
print(f"  Require Password Reset: {db_user.require_password_reset}")
print(f"  Group ID: {db_user.group_ids}")
print(f"  Role ID: {db_user.role_ids}")

print("\nUpdate user in DB:")
update_user = User(require_password_reset=True)
c8y.users.update(update_user, 'sou')



print("\nUpdate/Diff JSON after changes:")
current_user.email = "new@softwareag.com"
current_user.enabled = False
current_user.display_name = 'Chris Sour'
# current_user.roles.add('some_role')
# current_user.roles.remove('some_role')
# current_user.roles.add('a')
# current_user.roles.remove('xx')
# print(current_user.to_diff_json())
# current_user.roles.add('a')
# current_user.roles.add('b')
current_user.roles = set(['a', 'b'])
print(current_user.to_diff_json())

print("\nFinding users by name prefix:")
users = c8y.users.select(username='Chris')
for user in users:
    print(f"Found: {user.email}")

print("\nFinding users by group membership:")
users = c8y.users.select(groups='business')
for user in users:
    print(f"Found: {user.email}")


