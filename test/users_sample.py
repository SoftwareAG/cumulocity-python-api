from c8y_app import CumulocityApi
from c8y_model import User

c8y = CumulocityApi()
current_user = c8y.users.get(c8y.username)

print("Current User:")
print(f"User:            {current_user.user_id}")
print(f"Alias:           {current_user.display_name}")
print(f"Password Change: {current_user.last_password_change.isoformat()}")

print("\nCurrent user JSON:")
print(current_user.to_full_json())

print("\nUpdate/Diff JSON after changes:")
current_user.email = "new@softwareag.com"
current_user.enabled = False
current_user.display_name = 'Chris Sour'
print(current_user.to_diff_json())

print("\nFinding users by name prefix:")
users = c8y.users.select(username='Chris')
for user in users:
    print(f"Found: {user.email}")

print("\nFinding users by group membership:")
users = c8y.users.select(groups='business')
for user in users:
    print(f"Found: {user.email}")


