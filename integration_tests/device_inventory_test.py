import pytest

from c8y_api.app import CumulocityApi
from c8y_api.model import Device
from utils import c8y, RandomNameGenerator


@pytest.fixture(scope='function')
def random_devices(c8y: CumulocityApi):
    num = 3
    basename = RandomNameGenerator.random_name()
    typename = basename + '_type'

    names = [f'{basename}-{i}' for i in range(0, num)]
    devices = [Device(c8y=c8y, type=typename, name=name) for name in names]
    db_devices = [d.create() for d in devices]

    yield db_devices

    c8y.device_inventory.delete(*db_devices)


def test_get_all(c8y: CumulocityApi, random_devices):
    typename = random_devices[0].type

    result = c8y.device_inventory.get_all(type=typename)

    assert result
    assert len(result) == len(random_devices)

    result_names = {x.name for x in result}
    expected_names = {x.name for x in random_devices}
    assert result_names == expected_names
