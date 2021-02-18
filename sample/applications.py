# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.app import CumulocityApi

# When using the App version, the API handle is initialized using
# standard environment variables
c8y = CumulocityApi()


def print_application(application):
    print(f"Application #{application.id}: '{application.name}', "
          f"type: {application.type}, availability: {application.availability}")


# Applications can be pulled by their ID
app_1 = c8y.applications.get(1)
print_application(app_1)

# It is possible to iterate through all applications defined
for a in c8y.applications.select():
    print_application(a)

# Applications can be selected by their name
print(f"\nAll applications named 'cockpit':")
for a in c8y.applications.select(name='cockpit'):
    print_application(a)

# Applications can be selected by their owner
print(f"\nAll applications owned by the 'management' tenant:")
for a in c8y.applications.select(owner='management'):
    print_application(a)

# Applications can be selected by their assigned tenant
print(f"\nAll applications subscribed by the '{c8y.tenant_id}' tenant:")
for a in c8y.applications.select(tenant=c8y.tenant_id):
    print_application(a)

# Applications can be selected by user
print(f"\nAll applications assigned to the '{c8y.username}' user:")
for a in c8y.applications.select(user=c8y.username):
    print_application(a)
