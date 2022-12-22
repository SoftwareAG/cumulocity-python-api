# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from dotenv import load_dotenv

from c8y_api.app import SimpleCumulocityApp


load_dotenv()
c8y = SimpleCumulocityApp()
print("CumulocityApp initialized.")
print(f"{c8y.base_url}, Tenant: {c8y.tenant_id}, User:{c8y.username}")

try:
    value1 = c8y.tenant_options.get_value(category='remoteaccess', key='credentials.encryption.password')
    print(f"Value: {value1}")
except KeyError:
    print("Unable to read encrypted tenant option.")
