# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta
from dateutil import tz
import logging
import time
from typing import List

import pytest

from c8y_api import CumulocityApi
from c8y_api.model import Device, Measurement, Count

from tests import RandomNameGenerator


def get_ids(ms: List[Measurement]) -> List[str]:
    """Isolate the ID from a list of measurements."""
    return [m.id for m in ms]


@pytest.fixture(scope='session')
def measurement_factory(live_c8y: CumulocityApi):
    """Provide a factory function to create measurements that are cleaned
    up after the session if needed."""

    created_devices = []
    created_measurements = []

    def factory_fun(n: int, auto_delete=True):
        typename = RandomNameGenerator.random_name(2)
        fragment = f'{typename}_metric'
        series = f'{typename}_series'

        # 1) create device
        device = Device(c8y=live_c8y, type=f'{typename}_device', name=typename, test_marker={'name': typename}).create()
        created_devices.append(device)
        logging.info('Created device #{}', device.id)

        # 2) create measurements
        ms = []
        now = time.time()
        for i in range(0, n):
            measurement_time = datetime.fromtimestamp(now - i*60, tz.tzutc())
            m = Measurement(c8y=live_c8y, type=typename, source=device.id, time=measurement_time)
            m[fragment] = {series: Count(i+1)}
            m = m.create()
            logging.info('Created measurement #{}: {}', m.id, m.to_json())
            ms.append(m)
        if auto_delete:
            created_measurements.extend(ms)
        return ms

    yield factory_fun

    for cm in created_measurements:
        cm.delete()

    for d in created_devices:
        d.delete()


@pytest.fixture(scope='function')
def measurements_for_deletion(measurement_factory):
    """Provide measurements that can be deleted."""
    return measurement_factory(10, auto_delete=False)


@pytest.mark.parametrize('key, key_lambda', [
    ('type', lambda m: m.type),
    ('source', lambda m: m.source),
    ('fragment', lambda m: f'{m.type}_metric'),
    ('value', lambda m: f'{m.type}_metric'),
    ('series', lambda m: f'{m.type}_series')])
def test_get_and_delete_by(live_c8y: CumulocityApi, measurements_for_deletion, key, key_lambda):
    """Verify that get and delete by type works as expected."""
    kwargs = {key: key_lambda(measurements_for_deletion[0])}

    # 1_ get_all
    ms = live_c8y.measurements.get_all(**kwargs)
    assert len(ms) == len(measurements_for_deletion)
    assert set(get_ids(ms)) == set(get_ids(measurements_for_deletion))

    # 2_ get_last
    ms = sorted(measurements_for_deletion, key=lambda x: x.datetime)
    datetimes = [m.datetime for m in ms]

    # a) getting the last
    last = live_c8y.measurements.get_last(**kwargs)
    assert last.datetime == datetimes[-1]

    # b) getting the last before a certain time
    idx = 3
    last = live_c8y.measurements.get_last(before=datetimes[idx], **kwargs)
    assert last.datetime == datetimes[idx-1]

    # c) getting the last of a min age
    age = timedelta(minutes=3)
    last = live_c8y.measurements.get_last(min_age=age)
    # the 3rd entry would have the exact date if no time had passed
    # -> hence, the 3rd should just be right
    assert last.datetime == datetimes[-4]

    # 3_ delete_by
    live_c8y.measurements.delete_by(**kwargs)
    # -> wait a bit to avoid caching issues
    time.sleep(5)
    # -> verify that they are all gone
    ms = live_c8y.measurements.get_all(**kwargs)
    assert not ms
