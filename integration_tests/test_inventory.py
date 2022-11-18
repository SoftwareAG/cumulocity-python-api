# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=redefined-outer-name

from typing import List

import pytest

from c8y_api import CumulocityApi
from c8y_api.model import ManagedObject

from tests import RandomNameGenerator
from tests.utils import get_ids


@pytest.fixture(scope='session')
def object_factory(logger, live_c8y: CumulocityApi):
    """Provides a generic factory function which creates given ManagedObject
    instances within the database and cleans up afterwards.

    This fixture is supposed to be used by other fixtures.
    """

    created_objs = []

    def factory_fun(*objs: ManagedObject):
        logger.info(f"Creating {len(objs)} ManagedObject instances in live Cumulocity instance ...")
        new_objects = []
        for obj in objs:  # noqa
            obj.c8y = live_c8y
            created_obj = obj.create()
            new_objects.append(created_obj)
            logger.info(f'Created ManagedObject: #{created_obj.id}, name: {obj.name}, type: {obj.type}')
        created_objs.extend(new_objects)
        return new_objects

    yield factory_fun

    logger.info("Removing previously created ManagedObject instances ...")
    for obj in created_objs:
        obj.delete()
        logger.info(f"Deleted ManagedObject: #{obj.id}")


@pytest.fixture(scope='function')
def mutable_object(object_factory) -> ManagedObject:
    """Provide a single managed object ready to be changed during a test."""

    name = RandomNameGenerator.random_name(2)
    typename = name

    mo = ManagedObject(name=name, type=typename, **{name: {'key': 'value'}})
    return object_factory(mo)[0]


def test_update(mutable_object: ManagedObject):
    """Verify that updating managed objects works as expected."""

    mutable_object.name = mutable_object.name + '_altered'
    mutable_object.type = mutable_object.type + '_altered'
    mutable_object['new_attribute'] = 'value'
    mutable_object['new_fragment'] = {'key': 'value'}
    updated_object = mutable_object.update()

    assert updated_object.name == mutable_object.name
    assert updated_object.type == mutable_object.type
    assert updated_object.new_attribute == 'value'
    assert updated_object.new_fragment.key == 'value'


@pytest.fixture(scope='session')
def similar_objects(object_factory) -> List[ManagedObject]:
    """Provide a list of similar ManagedObjects (different name, everything
    else identical).  These are not to be changed."""

    n = 5
    basename = RandomNameGenerator.random_name(2)
    typename = basename

    mos = [ManagedObject(name=f'{basename}_{i}', type=typename, **{f'{typename}_fragment': {}}) for i in range(1, n+1)]
    return object_factory(*mos)


@pytest.mark.parametrize('key, value_fun', [
    ('type', lambda mo: mo.type),
    ('name', lambda mo: mo.type + '*'),
    ('fragment', lambda mo: mo.type + '_fragment')
])
def test_get_by_something(live_c8y: CumulocityApi, similar_objects: List[ManagedObject], key, value_fun):
    """Verify that managed objects can be selected by common type."""
    kwargs = {key: value_fun(similar_objects[0])}
    selected_mos = live_c8y.inventory.get_all(**kwargs)
    assert get_ids(similar_objects) == get_ids(selected_mos)
