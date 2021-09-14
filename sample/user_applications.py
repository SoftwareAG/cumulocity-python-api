# Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

from c8y_api.app import CumulocityApp
from c8y_api.model import User

# When using the App version, the API handle is initialized using
# standard environment variables
c8y = CumulocityApp()

# 1_ read the app user details
app_user = c8y.users.get(c8y.username)

# 1_ create a new user to play with
u = User(c8y=c8y, username='sample_user', email='sample@softwareag.com',
         application_ids={"7"})
u.create(ignore_result=True)

# 3_ read and test
u = c8y.users.get('sample_user')
assert u.email == 'sample@softwareag.com'
assert '7' in u.application_ids

# 4_ change and update
u.application_ids.add('3')
u.update()

# 5_ verify deletion
u = c8y.users.get('sample_user')
assert '3' in u.application_ids

# 5_ add applications and update
del u.application_ids
u.update()

u = c8y.users.get('sample_user')
assert not u.application_ids
