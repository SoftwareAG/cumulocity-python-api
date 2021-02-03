# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import datetime as dt

from c8y_api.app import CumulocityApi
from c8y_api.model import Event


def print_event(event):
    print(f'\nEvent #{event.id}, {event.time}')
    print(f'  "{event.text}"')
    print(f'  Type:     {event.type}')
    print(f'  Source:   {event.source}')
    print(f'  Created:  {event.creation_time}')
    fragment_names = list(event.fragments.keys())
    print(f'  Fragments: {", ".join(fragment_names)}')
    for key in fragment_names:
        print(f'   {key}: {event.fragments[key]}')


c8y = CumulocityApi()

sample_source_id = None

# (1) select by type
for e in c8y.events.select(type='Local Config Changed', limit=10):
    if not sample_source_id:
        sample_source_id = e.source
    print_event(e)

# (2) select by source
for e in c8y.events.select(source=sample_source_id, limit=10):
    print_event(e)

# (3) create a new event from scratch
date_string = dt.datetime.now().isoformat()
e1 = Event(c8y=c8y, type='Custom Type', source=sample_source_id, text='Some custom text.', time=date_string)
e1.add_fragment("custom_fragment", key="value", more={"x": 1, "y": 2})
e1_created = e1.create()  # the create method returns a new object, having the Id defined
print(f"\nEvent created: #{e1_created.id}")
print(f"  Custom fragment: {e1_created.custom_fragment.more}")

# (4) read events by ID
e1_read = c8y.events.get(e1_created.id)
assert e1_read.id == e1_created.id

# (5) delete an event
e1_read.delete()
try:
    c8y.events.get(e1_read.id)
    raise AssertionError("An exception should have been thrown.")
except KeyError:
    print(f"\nEvent deleted: #{e1_read.id}")

# (6) bulk create
print("\nCreating multiple events ...")
c8y.events.create(e1, e1, e1)  # 3 times the same event created, IDs are unknown

# (7) use get_all to get all matching as a list
events_so_far = c8y.events.get_all(type="Custom Type")
for e in events_so_far:
    print(f"  Matching event: #{e.id}")
assert len(events_so_far) > 3  # it could be more form previous tests

# (8) delete events by query
c8y.events.delete_by(type='Custom Type')
assert len(c8y.events.get_all(type='Custom Type')) == 0
print("\nDeleted all events with type='Custom Type'.")

# (9) delete multiple events by their ID
id1 = e1.create().id
id2 = e1.create().id
print(f"\nAbout to delete fresh created events #{id1} and #{id2} ...")
c8y.events.delete(id1, id2)
assert len(c8y.events.get_all(type='Custom Type')) == 0
print("Done.")

# (10) create and update an event
e2 = Event(c8y=c8y, type='Custom Type', source=sample_source_id, text='Some custom text.', time=date_string)\
    .create()
print(f"\nCreated event #{e2.id}.")
print(f"  Diff JSON: {e2.to_diff_json()}")
e2.text = "Updated event text."
e2.type = 'Updated Type'  # Updating the type is not supported by Cumulocity, this will be ignored
print(f"  Diff JSON after changes: {e2.to_diff_json()}")
e2 = e2.update()  # this will only send the changed fields for best performance
print(f"Event #{e2.id} updated.")
e2a = c8y.events.get(e2.id)
assert e2a.type != 'Updated Type'
assert e2a.text == "Updated event text."

# (10a) it is also possible to apply an update to other objects in the database
updater = Event(c8y=c8y, text='Updated event text #2.')
print(f"\nApplying update to event #{e2.id}: {updater.to_diff_json()}")
e2 = updater.apply_to(e2.id)
e2b = c8y.events.get(e2.id)
assert e2b.text == "Updated event text #2."

# (10b) the same can be done on multiple IDs
e3 = Event(c8y=c8y, type="Other", time=date_string, source=sample_source_id, text="Other")\
    .create()
updater2 = Event(c8y=c8y, text='Updated event text #3.')
c8y.events.apply_to(updater2, e2.id, e3.id)
e2c = c8y.events.get(e2.id)
e3c = c8y.events.get(e3.id)
assert e2c.text == "Updated event text #3."
assert e2c.text == e3c.text

# cleanup
e2.delete()
e3.delete()
