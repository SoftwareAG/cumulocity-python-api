# Copyright (c) 2021 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import datetime as dt

from c8y_api.app import CumulocityApp
from c8y_api.model import Alarm


def print_alarm(alarm):
    print(f'\nAlarm #{alarm.id}, {alarm.time}')
    print(f'  "{alarm.text}"')
    print(f'  Type:     {alarm.type}')
    print(f'  Source:   {alarm.source}')
    print(f'  Created:  {alarm.creation_time}')
    print(f'  Status:   {alarm.status}')
    print(f'  Severity: {alarm.severity}')
    print(f'  Count:    {alarm.count}')
    print(f'  First O.: {alarm.first_occurrence_time}')
    print(f'  Created:  {alarm.creation_time}')
    fragment_names = list(alarm.fragments.keys())
    print(f'  Fragments: {", ".join(fragment_names)}')
    for key in fragment_names:
        print(f'   {key}: {alarm.fragments[key]}')


c8y = CumulocityApp()

sample_source_id = None

# (1) select by type and status
for a in c8y.alarms.select(type='Failure', status='CLEARED', limit=10):
    if not sample_source_id:
        sample_source_id = a.source
    print_alarm(a)

# (2) select by source
for a in c8y.alarms.select(source=sample_source_id, limit=10):
    print_alarm(a)

# (3) create a new alarm from scratch
date_string = dt.datetime.now().isoformat()
a1 = Alarm(c8y=c8y, type='Custom Type', source=sample_source_id, text='Some custom text.', time=date_string,
           status='ACTIVE', severity='MINOR')
a1.add_fragment("custom_fragment", key="value", more={"x": 1, "y": 2})
a1_created = a1.create()  # the create method returns a new object, having the Id defined
print(f"\nAlarm created: #{a1_created.id}")
print(f"  Custom fragment: {a1_created.custom_fragment.more}")

# (4) read alarms by ID
a1_read = c8y.alarms.get(a1_created.id)
assert a1_read.id == a1_created.id

# (6) bulk create
print("\nRaising an alarm multiple times ...")
c8y.alarms.create(a1, a1, a1)  # 3 times the same alarm raised, this will increase the count of the event
a1_read = c8y.alarms.get(a1_created.id)
assert a1_read.count == 4

# (7) use get_all to get all matching as a list
alarms_so_far = c8y.alarms.get_all(type="Custom Type", source=sample_source_id)
assert len(alarms_so_far) == 1  # it will still be 1

# (8) delete events by query
c8y.alarms.delete_by(type='Custom Type', source=sample_source_id)
assert len(c8y.alarms.get_all(type='Custom Type', source=sample_source_id)) == 0
print(f"\nDeleted all alarms with type='Custom Type' and source='{sample_source_id}'.")

# (9) update alarms
a2 = Alarm(c8y=c8y, type='Custom', source=sample_source_id, severity='MINOR', time=date_string, text="Custom Alarm.")\
    .create()
print(f"\nCreated alarm #{a2.id} with severity {a2.severity}.")
a2.severity = 'MAJOR'
a2_1 = a2.update()
print(f"Updated alarm #{a2_1.id} to severity {a2_1.severity}.")
assert a2_1.severity == 'MAJOR'

# (9a) apply an update to other alarms
a3 = Alarm(c8y=c8y, source=sample_source_id, status='ACTIVE', severity='MINOR', time=date_string)

#  - create and collect a couple of alarms, looking similar
a3_items = []
for i in range(1, 3):
    a3.type = 'Custom #' + str(i)
    a3.text = 'Some custom text #' + str(i)
    # delete any previously created alarms to avoid disturbance
    c8y.alarms.delete_by(type=a3.type, source=a3.source)
    a3_items.append(a3.create())

#  - create a change object
a3_chg = Alarm(c8y=c8y, severity='MAJOR')
#  - apply the change to previously created alarms
a3_items2 = []
for a in a3_items:
    a3_items2.append(a3_chg.apply_to(a.id))
#  - verify that all alarms where changed
for i in range(len(a3_items)):
    assert a3_items[i].severity != a3_items2[i].severity
    assert a3_items2[i].severity == a3_chg.severity

#  - create another change object (note: no c8y reference necessary)
a3_chg = Alarm(status='ACKNOWLEDGED')
a3_chg.add_fragment('custom_marker_fragment')
#  - apply the change to all previously created alarms at once
a3_ids = [x.id for x in a3_items]
c8y.alarms.apply_to(a3_chg, *a3_ids)
#  - verify that all alarms where changed
for alarm_id in a3_ids:
    a = c8y.alarms.get(alarm_id)
    assert a.status == a3_chg.status
    assert 'custom_marker_fragment' in a.fragments

# cleanup
for a in a3_items:
    a.delete()
