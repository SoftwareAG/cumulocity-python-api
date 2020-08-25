from c8y_app import CumulocityApi
from c8y_model import User

c8y = CumulocityApi()
current_user = c8y.users.get(c8y.username)

print(f"User:            {current_user.user_id}")
print(f"Alias:           {current_user.display_name}")
print(f"Password Change: {current_user.last_password_change.isoformat()}")


print(current_user.to_full_json())
current_user.email = "new@softwareag.com"
current_user.enabled = False
current_user.username = 'csou'
current_user.display_name = 'Chris Sour'
print(current_user.to_diff_json())
current_user.display_name = 'Chris Soura'
print(current_user.to_diff_json())
