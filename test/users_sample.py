from c8y_app import CumulocityApi
from c8y_model import User

c8y = CumulocityApi()
current_user = c8y.users.get(c8y.username)

print(f"User:   {current_user.user_id}")
print(f"Alias:  {current_user.user_id}")

print(current_user.to_full_json())
current_user.email = "new@softwareag.com"
current_user.enabled = False
print(current_user.to_diff_json())
