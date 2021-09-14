# Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

from c8y_api.app import CumulocityApp
from c8y_api.model import DeviceGroup

c8y = CumulocityApp()


def print_group_with_children(indent, group_id):
    g = c8y.group_inventory.get(group_id)
    print(f"{indent}'{g.name}', ID {g.id}")
    next_indent = '  ' + indent
    for c in g.child_assets:
        print_group_with_children(next_indent, c.id)


# top level device groups can be created standalone
print("\nCreating a top level group")
parent = DeviceGroup(c8y=c8y, name='parent')
created_parent = parent.create()
print(f"  ID: {created_parent.id}")

# sub device groups need to be hooked to a parent
# this happens immediately
print("\nAdding child to a group")
created_child = created_parent.add_group(name='child2')
print(f"  Created '{created_child.name}', ID {created_child.id}")

# entire trees can be created as well
print("\nCreating an entire tree")
tree = DeviceGroup(c8y=c8y, name='tree-parent')
tree.add(
    DeviceGroup(name='tree-child-1'),
    DeviceGroup(name='tree-folder').add(
        DeviceGroup(name='tree-child-2'),
        DeviceGroup(name='tree-child-3'))
    )
tree.create()

# existing groups can be modified
existing_parent = c8y.group_inventory.get_all(name='tree-parent')[0]
existing_parent.add(DeviceGroup(name='new-child-1'), DeviceGroup(name='new-child-2'))
existing_parent.update()

# iterate through groups
print("\nIterate through groups")
for x in c8y.group_inventory.select():
    print_group_with_children(' ', x.id)

# groups can be deleted - this automatically deletes any children
print("\nIterating and deleting:")
for x in c8y.group_inventory.select(name='parent'):
    print(f"  Found group '{x.name}', ID {x.id}")
    x.delete()
for x in c8y.group_inventory.select(name='tree-parent'):
    print(f"  Found group '{x.name}', ID {x.id}")
    x.delete()
