# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable: redefined-outer-name

import json
import os

import pytest

from c8y_api.model import Device


@pytest.fixture(scope='function')
def sample_device() -> Device:
    """Provide a sample object for various tests."""
    return Device(name='name', type='type', owner='owner',
                  simple_string='string',
                  simple_int=123,
                  simple_float=123.4,
                  simple_true=True,
                  simple_false=False,
                  complex_1={'level0': 'value'},
                  complex_2={'string': 'value', 'level0': {'level1': 'value'}})


def test_formatting(sample_device: Device):
    """Verify that JSON formatting works."""
    sample_device.id = 'id'
    object_json = sample_device.to_full_json()

    assert 'id' not in object_json
    assert object_json['name'] == sample_device.name
    assert object_json['type'] == sample_device.type
    assert object_json['owner'] == sample_device.owner
    assert 'c8y_IsDevice' in object_json

    assert object_json['simple_string'] == sample_device.simple_string
    assert object_json['simple_int'] == sample_device.simple_int
    assert object_json['simple_float'] == sample_device.simple_float
    assert object_json['simple_true'] is True
    assert object_json['simple_false'] is False
    assert object_json['complex_1']['level0'] == 'value'
    assert object_json['complex_2']['level0']['level1'] == 'value'

    expected_keys = {'name', 'type', 'owner', 'c8y_IsDevice',
                     'simple_string', 'simple_int', 'simple_float', 'simple_true', 'simple_false',
                     'complex_1', 'complex_2'}
    assert set(object_json.keys()) == expected_keys


def test_parsing():
    """Verify that parsing a Device from JSON works."""

    # 1) read a sample object from file
    path = os.path.dirname(__file__) + '/device.json'
    with open(path) as f:
        device_json = json.load(f)

    d = Device.from_json(device_json)

    # 2) assert parsed data
    assert d.id == device_json['id']
    assert d.type == device_json['type']
    assert d.name == device_json['name']
    assert d.creation_time == device_json['creationTime']
    assert d.is_device
    assert d.creation_datetime

    # 3) custom fragments
    assert d.c8y_SupportedOperations == device_json['c8y_SupportedOperations']
    test_fragment = d.c8y_DataPoint.test
    test_json = device_json['c8y_DataPoint']['test']
    assert test_fragment.string == test_json['string']
    assert test_fragment.int == test_json['int']
    assert test_fragment.float == test_json['float']
    assert test_fragment.true == test_json['true']
    assert test_fragment.false == test_json['false']
