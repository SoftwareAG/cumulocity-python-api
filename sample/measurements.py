# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import datetime as dt

from c8y_api.app import CumulocityApi
from c8y_api.model import Measurement, Device, Count, Value, Meters

run_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds')

c8y = CumulocityApi()


# create a device and obtain ID
d = Device(c8y, type='DemoClient')
d.add_fragment('c8y_DemoClient')
d.create()
device_id = c8y.inventory.get_all(fragment='c8y_DemoClient')[0].id

m1 = Measurement(c8y=c8y, type='c8y_DemoMeasurement', source=device_id)
# simple custom fragments can be added directly, special sub structures can
# be added using standard dictionaries
m1.add_fragment('c8y_CustomFragment',
                user=c8y.username, message='Demo Measurement',
                special={'doc': {'k1': 1, 'k2': 2}})
# typical measurement fragment values can be added using the convenience classes
m1.add_fragment('c8y_DemoMeasurement', Iterations=Count(-1),
                L=Meters(12.4), X=Value(42, unit='x'))
# when stored without defined time, the current time will be used automatically
m1_created = m1.create()
print(f"\nMeasurement #{m1_created.id} created:")
print(f"  Time: {m1_created.time}")
print(f"  Fragments: {', '.join([x for x in m1_created.fragments.keys()])}")

# subsequent measurements of the same kind
time = m1_created.time
print("\nCreating additional measurements ...")
for i in range(0, 5):
    # fragments can be accessed using simple dot notification up to any depth
    # this works for assignments as well
    m1.c8y_CustomFragment.special.doc.k1 = 12
    m1.c8y_DemoMeasurement.Iterations.value = i
    # the time will be updated every time
    m1_created = m1.create()
    print(f"Created measurement #{m1_created.id} with time {m1_created.time}.")
    assert time != m1_created.time

# querying the database by type
# other filters are possible: source, fragment, date
my_type = 'c8y_DemoMeasurement'
print(f"\nListing all Measurements for type '{my_type}' ...")
for m in c8y.measurements.select(type=my_type, after=run_at, reverse=True):
    v = m.c8y_DemoMeasurement.Iterations.value
    u = m.c8y_DemoMeasurement.Iterations.unit
    t = m.time
    print(f"  Got measurement at {t}: {v} {u}")
    # a measurement retrieved like this can be deleted directly
    m.delete()
    print(f"  Measurement #{m.id} deleted.")

# measurements can also be created in a bulk
print("\nCreating measurements in a bulk ...")
ms = [Measurement(type='Custom#'+str(i), source=device_id, time=run_at) for i in range(1, 6)]
c8y.measurements.create(*ms)
ids = []
for m in c8y.measurements.get_all(source=device_id):
    if m.type.startswith('Custom#'):
        print(f"  Measurement #{m.id} created. Type: {m.type}")
        ids.append(m.id)
c8y.measurements.delete(*ids)

# Specific timeframes can be specified with before/after parameters.
# The API also provides an alternative mechanism via min/max age of entries
# The select method evaluates lazy (by result page), the get_all method will
# pull everything available. Both methods support a limit parameter to limit
# the number of results possible.
print("\nListing measurements of the last 3 days ...")
ms = c8y.measurements.get_all(min_age=dt.timedelta(days=1), max_age=dt.timedelta(days=3), limit=3)
assert len(ms) == 3
for m in ms:
    print(f"  Got measurement of type {m.type} at {m.time}")

# cleanup assets
# d.delete() does not work, because it is a new object without ID and no connection set
c8y.inventory.delete(device_id)
