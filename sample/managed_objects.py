# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import json

from c8y_api.app import CumulocityApi
from c8y_api.model import ManagedObject, Device, Fragment

api = CumulocityApi()

# (1) Creating managed objects from scratch
print("\nCreating custom managed objects ...")
mo = ManagedObject(name='test')
mo.set_attribute(name='c8y_attribute', value="some message string")
mo.add_fragment(name='c8y_Fragment', region='EMEA')
mo.add_fragments(Fragment('c8y_F1', v=1), Fragment('c8y_F2', v=2))
mo.c8y = api  # needs to be defined for object-oriented database access
mo1 = mo.create()
print(f"  Created object #{mo1.id}.")
print(f"    Attribute: {mo1.c8y_attribute}")
print(f"    Region:    {mo1.c8y_Fragment.region}")
print(f"    Created:   {mo1.creation_time} (string)")
print(f"    Updated:   {mo1.update_datetime} (datetime object)")
print(f"    Region:    {mo1.c8y_Fragment.region}")

mo2 = mo.create()
print(f"  Created object #{mo2.id}.")
print(f"     {json.dumps(mo2.to_json())}")

# (2) Changes are tracked automatically and can we written to the database
print("\nWriting updates ...")
mo1.c8y_attribute = "other message string"  # this doesn't flag the updated
mo1.set_attribute('c8y_attribute' , "better message string")  # this flags the update
mo1.c8y_Fragment.region = 'APJ'
mo1.type = "ChangedType"
print(f"  Changes:   {mo1.get_updates()}")
print(f"  Diff JSON: {mo1.to_diff_json()}")

# (3) Updates can also be written to other objects
print("\nApplying changes to other objects ...")
mo2 = mo1.apply_to(mo2.id)
print(f"    Attribute: {mo2.c8y_attribute}")
print(f"    Region:    {mo2.c8y_Fragment.region}")

# (4) Updates can be 'rolled out' to multiple others
mo_chg = ManagedObject(type='NewType')\
    .add_fragment('c8y_NewFragment', special=True)
api.inventory.apply_to(mo_chg, mo1.id, mo2.id)

# (5) Objects can be read by ID
mo1x = api.inventory.get(mo1.id)
mo2x = api.inventory.get(mo2.id)

# (6) Objects can be read by a query
print("\nQuerying for managed objects ...")
for mo in api.inventory.select(type='NewType', fragment='c8y_NewFragment'):
    if mo.id == mo1x.id:
        print(f"  Found expected object #1")
    else:
        print(f"  Found object: {mo.id}")

# (7) Linking to other assets
d = Device(api, type="SomeDeviceType").create()

mo1.add_child_device(d.id)
mo1.add_child_asset(d.id)

print("\nDeleting objects ...")
mo1.delete()
api.inventory.delete(mo2.id)
