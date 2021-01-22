# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.app import CumulocityApi
from c8y_api.model import Events


def print_event(event):
    print(f'\nEvent #{event.id}, {event.time}')
    print(f'  "{event.text}"')
    print(f'  Type:     {event.type}')
    print(f'  Category: {event.category}')
    print(f'  Source:   {event.source}')
    print(f'  Created:  {event.creation_time}')


c8y = CumulocityApi()

sample_source_id = None

# (1) select by type
for e in c8y.events.select(type='Local Config Changed', limit=10):
    if not sample_source_id:
        sample_source_id = e.source
    print_event(e)

# (1) select by category
for e in c8y.events.select(category='Device Maintenance', limit=10):
    print_event(e)

# (1) select by source
for e in c8y.events.select(source=sample_source_id, limit=10):
    print_event(e)

