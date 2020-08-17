import uuid

from c8y_api import CumulocityApi, CumulocityDeviceRegistry
from c8y_model import Device

device_id = 'device_' + str(uuid.uuid1())
print('Requesting credentials for device ' + device_id)

c8y_dr = CumulocityDeviceRegistry.default()
device_c8y = c8y_dr.await_connection(device_id, timeout='10m', pause='5s')

d1 = Device(type='c8y_Linux', name=device_id)
d1.add_fragment('c8y_Test', run=1)
d1.c8y = device_c8y
d1.store()

common_c8y = CumulocityApi(base_url='http://pmt-training.eu-latest.cumulocity.com',
                           tenant_id='t21106993', username='chrsou', password='Flower34')
for d in common_c8y.inventory.select(type='c8y_Linux', fragment='c8y_Test'):
    print(f"Found device: {d.id}")
