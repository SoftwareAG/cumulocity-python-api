# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from datetime import datetime, timedelta
from dateutil import tz
import logging
import time
from typing import List

import pytest

from c8y_api import CumulocityApi
from c8y_api.model import Device, Measurement, Measurements, Series, Count, Kelvin

from util.testing_util import RandomNameGenerator


def get_ids(ms: List[Measurement]) -> List[str]:
    """Isolate the ID from a list of measurements."""
    return [m.id for m in ms]


@pytest.fixture(scope='session', name='measurement_factory')
def fix_measurement_factory(live_c8y: CumulocityApi):
    """Provide a factory function to create measurements that are cleaned
    up after the session if needed."""

    created_devices = []

    def factory_fun(n: int) -> List[Measurement]:
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
        return ms

    yield factory_fun

    for d in created_devices:
        try:
            d.delete()
        except KeyError:
            logging.warning(f"Device #{d.id} already deleted.")


def test_select(live_c8y: CumulocityApi, measurement_factory):
    """Verify that selection works as expected."""
    # create a couple of measurements
    created_ms = measurement_factory(100)
    created_ids = [m.id for m in created_ms]
    device_id = created_ms[0].source

    # select all measurements using different page sizes
    selected_ids_1 = [m.id for m in live_c8y.measurements.select(source=device_id, page_size=1000)]
    selected_ids_2 = [m.id for m in live_c8y.measurements.select(source=device_id, page_size=10)]

    # -> all created measurements should be in the selection
    assert set(created_ids) == set(selected_ids_1)
    # -> the page size should not affect the selection result
    assert selected_ids_1 == selected_ids_2


def test_single_page_select(live_c8y: CumulocityApi, measurement_factory):
    """Verify that selection works as expected."""
    # create a couple of measurements
    created_ms = measurement_factory(50)
    created_ids = [m.id for m in created_ms]
    device_id = created_ms[0].source

    # select all measurements using different page sizes
    selected_ids = [m.id for m in live_c8y.measurements.select(source=device_id, page_size=10, page_number=2)]

    # -> all created measurements should be in the selection
    assert len(selected_ids) == 10
    assert all(i in set(created_ids) for i in selected_ids)


def clone_measurement(m:Measurement, key) -> Measurement:
    m2 = Measurement(m.c8y, type=m.type, source=m.source, time=m.time)
    if key == 'type':
        m2.type = m2.type + '2'
    for fragment, series in m.fragments.items():
        for name, value in series.items():
            if key == 'fragment' or key == 'value':
                fragment = fragment + '2'
            if key == 'series':
                name = name + '2'
            m2[fragment] = {name: value}
    return m2.create()


@pytest.mark.parametrize('key, key_lambda', [
    ('type', lambda m: m.type),
    ('source', lambda m: m.source),
    ('series', lambda m: f'{m.type}_series'),
    ('value', lambda m: f'{m.type}_metric'),
])
def test_select_by(live_c8y: CumulocityApi, measurement_factory, key, key_lambda):
    """Verify that get and delete by type works as expected."""
    measurements_for_deletion = measurement_factory(10)
    kwargs = {key: key_lambda(measurements_for_deletion[0])}

    # add some 'similar' measurements to verify the query doesn't affect
    # these; doesn't make sense for 'source', there already are many
    if key != 'source':
        for m in measurements_for_deletion:
            clone_measurement(m, key)

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


@pytest.mark.parametrize('key, key_lambda', [
    ('type', lambda m: m.type),
    ('source', lambda m: m.source),
    ('fragment', lambda m: f'{m.type}_metric'),
])
def test_delete_by(live_c8y: CumulocityApi, measurement_factory, key, key_lambda):
    """Verify that get and delete by type works as expected."""
    measurements_for_deletion = measurement_factory(10)
    kwargs = {key: key_lambda(measurements_for_deletion[0])}

    # 0 add some 'similar' measurements
    additional_measurements = []
    if key != 'source':
        additional_measurements = [clone_measurement(m, key) for m in measurements_for_deletion]

    # delete_by kwargs
    live_c8y.measurements.delete_by(**kwargs)
    # -> wait a bit to avoid caching issues
    time.sleep(5)
    # -> verify that they are all gone
    ms = live_c8y.measurements.get_all(**kwargs)
    assert not ms

    # delete additional measurements if there are any
    # this also ensures that they haven't been deleted beforehand
    live_c8y.measurements.delete(*additional_measurements)


@pytest.fixture(scope='session', name='sample_series_device')
def fix_sample_series_device(live_c8y: CumulocityApi, sample_device: Device) -> Device:
    """Add measurement series to the sample device."""
    # create 12K measurements, 2 every minute
    start_time = datetime.fromisoformat('2020-01-01 00:00:00+00:00')
    ms_iter = [Measurement(type='c8y_TestMeasurement',
                      source=sample_device.id,
                      time=start_time + (i * timedelta(seconds=30)),
                      c8y_Iteration={'c8y_Counter': Count(i)},
                      ) for i in range(0, 5000)]
    ms_temps = [Measurement(type='c8y_TestMeasurement',
                      source=sample_device.id,
                      time=start_time + (i * timedelta(seconds=100)),
                      c8y_Temperature={'c8y_AverageTemperature': Kelvin(i * 0.2)},
                      ) for i in range(0, 1000)]
    live_c8y.measurements.create(*ms_iter)
    live_c8y.measurements.create(*ms_temps)

    sample_device['c8y_SupportedSeries'] = ['c8y_Temperature.c8y_AverageTemperature',
                                            'c8y_Iteration.c8y_Counter']
    return sample_device.update()


@pytest.fixture(scope='session')
def unaggregated_series_result(live_c8y: CumulocityApi, sample_series_device: Device) -> Series:
    """Provide an unaggregated series result."""
    start_time = datetime.fromisoformat('2020-01-01 00:00:00+00:00')
    return live_c8y.measurements.get_series(source=sample_series_device.id,
                                            series=sample_series_device.c8y_SupportedSeries,
                                            after=start_time, before='now')


@pytest.fixture(scope='session')
def aggregated_series_result(live_c8y: CumulocityApi, sample_series_device: Device) -> Series:
    """Provide an aggregated series result."""
    start_time = datetime.fromisoformat('2020-01-01 00:00:00+00:00')
    return live_c8y.measurements.get_series(source=sample_series_device.id,
                                            series=sample_series_device.c8y_SupportedSeries,
                                            aggregation=Measurements.AggregationType.HOURLY,
                                            after=start_time, before='now')


@pytest.mark.parametrize('series_fixture', [
    'unaggregated_series_result',
    'aggregated_series_result'])
def test_collect_single_series(series_fixture, request):
    """Verify that collecting a single value (min or max) from a
    series works as expected."""
    series_result = request.getfixturevalue(series_fixture)
    for spec in series_result.specs:
        values = series_result.collect(series=spec.series, value='min')
        # -> None values should be filtered out
        assert values
        assert all(v is not None for v in values)
        # -> Values should all have the same type
        # pylint: disable=unidiomatic-typecheck
        assert all(type(a) == type(b) for a, b in zip(values, values[1:]))
        # -> Values should be increasing continuously
        assert all(a<b for a,b in zip(values, values[1:]))


@pytest.mark.parametrize('series_fixture', [
    'unaggregated_series_result',
    'aggregated_series_result'])
def test_collect_multiple_series(series_fixture, request):
    """Verify that collecting a single value (min or max) for multiple
    series works as expected."""
    series_result = request.getfixturevalue(series_fixture)
    series_names = [s.series for s in series_result.specs]
    values = series_result.collect(series=series_names, value='min')
    assert values
    # -> Each element should be an n-tuple (n as number of series)
    assert all(isinstance(v, tuple) for v in values)
    assert all(len(v) == len(series_names) for v in values)
    # -> Each value within the n-tuple belongs to one series
    #    There will be None values (when a series does not define a value
    #    at that timestamp). Subsequent values will have the same type
    assert any(any(e is None for e in v) for v in values)
    for i in range(0, len(series_names)):
        t = type(values[0][i])
        assert all(isinstance(v[i], t) for v in values if v[i])
