# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import uuid
import time
import threading

from c8y_api import CumulocityDeviceRegistry
from c8y_api.app import CumulocityApi
from c8y_api.model import Device


device_registry = CumulocityDeviceRegistry(
    base_url='https://eu-latest.cumulocity.com',
    tenant_id='management',
    username='devicebootstrap',
    password='Fhdt1bb1f')

device_uuid = str(uuid.uuid1())
api = CumulocityApi()

print(f"Creating a device request for ID {device_uuid}.")
api.device_inventory.request(device_uuid)
# the request can be accepted once there was some communication
# we will do this asynchronously
def await_communication_and_accept():
    for i in range(1, 100):
        try:
            api.device_inventory.accept(device_uuid)
            break
        except:
            print("Unable to accept device request. Waiting for device communication.")
            time.sleep(1)
threading.Thread(target=await_communication_and_accept).start()

device_api = device_registry.await_connection(device_uuid)
print("Device request accepted.")

print(f"\nCreating a new device object ...")
device = Device(c8y=device_api, name=device_uuid, type='TestDevice').create()
print(f"Object created: #{device.id}")
print(f"  Name:      {device.name}")
print(f"  Type:      {device.type}")
print(f"  Owner:     {device.owner}")
print(f"  Fragments: {', '.join(device.fragments.keys())}")
print(f"  Created:   {device.creation_time}")

print(f"\nChecking the device user ...")
device_user = api.users.get(device.owner)
print(f"  Name:    {device_user.username}")
print(f"  Roles:   {', '.join([str(x) for x in device_user.global_role_ids])}")

print(f"\nDeleting the device (and user) ...")
device.delete()

assert len(api.users.get_all(username=device_user.username)) == 0
