from c8y_api.model import Measurements, Measurement, Fragment
import json


f1 = Fragment._from_json('c8y_custom', json.loads(
    '{"date":"2020-07-24", "details":{"owner":"me", "price": {"value": 12.3, "unit": "EUR"}}}'))
print(f1.details.price.unit + " " + str(f1.details.price.value))

# this doesn't work yet, because overloading the __setattr__ function is tedious
f2 = Fragment('c8y_custom', total=42, period='2020-07')
f2.something = 'some value'
f2.temperature = {'value': 38, 'unit': 'c'}

m1 = Measurement(type='some_sum', source='14415672')\
        .add_fragment('c8y_something', day='2020-07-24', total=14.0)\
        .add_fragment('c8y_something', day='2020-07-24', total=14.0)
m1.add_fragments(f1)
m1.add_fragments(f1, f1, f1)
m1.store()

# future syntactic sugar
# m2 = Measurement(type='some_sum', source='14415672')
# m2.c8y_something = Fragment(day='2020-07-24', total=14.0)
# m2.c8y_other = Fragment(name='c8y_other', value=42)
# m2.store()

for m in Measurements.select(type='some_sum'):
    print(m.id)
    m.delete()

for measurement in Measurements.select(fragment="report_result"):
    if measurement.report_result.has('date'):
        print(measurement.report_result.date)

measurement = Measurements.get_last(fragment='pt_current')
print(measurement.id + ": " + str(measurement.pt_current.CURR.value))
