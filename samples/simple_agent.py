import pickle
from c8y_api.app import CumulocityApi
from c8y_api import CumulocityDeviceRegistry
from c8y_api.model import ManagedObject, Device, Event

# TODO: enter base URL
base_url = 'cumulocity.com'
# TODO: enter tenant id
tenant_id = '*'
bootstrap_username = 'devicebootstrap'
bootstrap_password = 'Fhdt1bb1f'
device_external_id = 'python-device-external-id'

# Just for demo purposes, do not save device credentials into a txt file in production!
def save_credentials(cr):
    print(f'Saving credentials')
    with open('credentials.txt', 'wb') as credentials_file:
        pickle.dump(cr, credentials_file)
    credentials_file.close()


def load_credentials():
    with open('credentials.txt', 'rb') as credentials_file:
        cr = pickle.load(credentials_file)
        return cr


def provision_device():
    print(f'Please register and accept a device with ID: {device_external_id} on the Cumulocity tenant {base_url}')
    c8y_device_registry = CumulocityDeviceRegistry(base_url, tenant_id, bootstrap_username, bootstrap_password)
    cr = c8y_device_registry.await_credentials(device_external_id)
    save_credentials(cr)
    return cr


def create_device(c8yapi: CumulocityApi):
    device_mo = Device(c8yapi, 'sag_PythonDevice', 'Python device', None).create()
    c8yapi.identity.create(device_external_id, 'c8y_Serial', device_mo.id)
    return device_mo


try:
    credentials = load_credentials()
except (FileNotFoundError, EOFError) as e:
    print(f'Device credentials not found.')
    credentials = provision_device()

# print(f'Connection successful. Device credentials: username = {credentials.username} password = {credentials.password}')
c8y_agent = CumulocityApi(base_url, credentials.tenant_id, credentials.username, credentials.password)

# check if device is already created
try:
    device = c8y_agent.identity.get_object(device_external_id, 'c8y_Serial')
except KeyError:
    print('Device is not present on the Cumulocity side')
    device = create_device(c8y_agent)

event = Event(None, 'sag_PythonInitDone', None, device.id, 'Device initialization is done')
c8y_agent.events.create(event)
