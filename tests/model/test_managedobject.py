# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=redefined-outer-name

import json
import os

import pytest

from c8y_api.model import ManagedObject


def test_parsing():
    """Verify that parsing a User from JSON works."""

    # 1) read a sample object from file
    path = os.path.dirname(__file__) + '/managed_object.json'
    with open(path, encoding='utf-8', mode='rt') as f:
        object_json = json.load(f)

    mo = ManagedObject.from_json(object_json)

    # 2) assert parsed data
    assert mo.id == object_json['id']
    assert mo.type == object_json['type']
    assert mo.name == object_json['name']

    # 3) custom fragments
    assert mo.applicationId == object_json['applicationId']
    test_fragment = mo.c8y_Status.details.test
    test_json = object_json['c8y_Status']['details']['test']
    assert test_fragment.string == test_json['string']
    assert test_fragment.int == test_json['int']
    assert test_fragment.float == test_json['float']
    assert test_fragment.true == test_json['true']
    assert test_fragment.false == test_json['false']


@pytest.fixture(scope='function')
def sample_object() -> ManagedObject:
    """Provide a sample object for various tests."""
    return ManagedObject(name='name', type='type', owner='owner',
                         simple_string='string',
                         simple_int=123,
                         simple_float=123.4,
                         simple_true=True,
                         simple_false=False,
                         complex_1={'level0': 'value'},
                         complex_2={'string': 'value', 'level0': {'level1': 'value'}})


def test_formatting(sample_object: ManagedObject):
    """Verify that JSON formatting works."""
    sample_object.id = 'id'
    object_json = sample_object.to_full_json()

    assert 'id' not in object_json
    assert object_json['name'] == sample_object.name
    assert object_json['type'] == sample_object.type
    assert object_json['owner'] == sample_object.owner

    assert object_json['simple_string'] == sample_object.simple_string
    assert object_json['simple_int'] == sample_object.simple_int
    assert object_json['simple_float'] == sample_object.simple_float
    assert object_json['simple_true'] is True
    assert object_json['simple_false'] is False
    assert object_json['complex_1']['level0'] == 'value'
    assert object_json['complex_2']['level0']['level1'] == 'value'

    expected_keys = {'name', 'type', 'owner',
                     'simple_string', 'simple_int', 'simple_float', 'simple_true', 'simple_false',
                     'complex_1', 'complex_2'}
    assert set(object_json.keys()) == expected_keys


def test_updating(sample_object: ManagedObject):
    """Verify that updating results in proper diff JSON."""
    sample_object.id = 'id'

    # 1) after no update
    assert not sample_object.get_updates()
    object_json = sample_object.to_diff_json()
    assert object_json == {}

    # 2) readonly properties are not recorded
    sample_object.creation_time = '2001-12-31'
    sample_object.update_time = '2001-12-31'
    assert not sample_object.get_updates()
    assert sample_object.to_diff_json() == {}

    # 3) updatable properties are recorded
    sample_object.type = 'new type'
    sample_object.name = 'new name'
    sample_object.owner = 'new owner'
    expected_updates = {'type', 'name', 'owner'}
    # -> len is the same, we cannot test the keys as they are internal
    assert len(sample_object.get_updates()) == len(expected_updates)
    assert set(sample_object.to_diff_json().keys()) == expected_updates

    # 4) updated fragments are recorded
    # Note: simple fragments can only be updated using [] notation
    sample_object['simple_float'] = 543.21
    sample_object['simple_false'] = False
    sample_object.complex_2.level0.level1 = 'new value'
    expected_updates.update({'simple_float', 'simple_false', 'complex_2'})
    assert len(sample_object.get_updates()) == len(expected_updates)
    assert set(sample_object.to_diff_json().keys()) == expected_updates


@pytest.fixture(scope='session')
def object_with_fragments():
    """Create an object featuring various custom fragments."""

    kwargs = {'simple_string': 'string',
              'simple_int': 123,
              'simple_float': 123.4,
              'simple_true': True,
              'simple_false': False,
              'complex_1': {'level0': 'value'},
              'complex_2': {'level0': {'level1': 'value'}}}
    return kwargs, ManagedObject(**kwargs)


def test_dot_access(object_with_fragments):
    """Verify that fragment can be access using dot syntax."""

    kwargs, mo = object_with_fragments

    assert mo.simple_string == kwargs['simple_string']
    assert mo.simple_int == kwargs['simple_int']
    assert mo.simple_float == kwargs['simple_float']
    assert mo.simple_true == kwargs['simple_true']
    assert mo.simple_false == kwargs['simple_false']

    assert mo.complex_1.level0 == kwargs['complex_1']['level0']
    assert mo.complex_2.level0.level1 == kwargs['complex_2']['level0']['level1']

    # testing 1st level (ComplexObject class)
    with pytest.raises(AttributeError) as e:
        _ = mo.not_existing
    assert 'not_existing' in str(e)

    # testing 2nd level (_DictWrapper class)
    with pytest.raises(AttributeError) as e:
        _ = mo.complex_1.not_existing
    assert 'not_existing' in str(e)


def test_fragment_presence(object_with_fragments):
    """Verify that fragment presence can be checked."""

    kwargs, mo = object_with_fragments

    for attr_name in kwargs.keys():
        assert attr_name in mo
        assert mo.has(attr_name)
    assert 'wrong_one' not in mo
    assert not mo.has('wrong_again')


def test_item_access(object_with_fragments):
    """Verify that fragments can be accessed using [] operator."""

    kwargs, mo = object_with_fragments

    assert mo['simple_string'] == kwargs['simple_string']
    assert mo['simple_int'] == kwargs['simple_int']
    assert mo['simple_float'] == kwargs['simple_float']
    assert mo['simple_true'] == kwargs['simple_true']
    assert mo['simple_false'] == kwargs['simple_false']

    assert mo['complex_1']['level0'] == kwargs['complex_1']['level0']
    assert mo['complex_2']['level0']['level1'] == kwargs['complex_2']['level0']['level1']

    # testing 1st level (ComplexObject class)
    with pytest.raises(KeyError) as e:
        _ = mo['not_existing']
    assert 'not_existing' in str(e)

    # testing 2nd level (_DictWrapper class)
    with pytest.raises(KeyError) as e:
        _ = mo['complex_1']['not_existing']
    assert 'not_existing' in str(e)
