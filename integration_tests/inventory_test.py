# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import pytest

from c8y_api.app import CumulocityApi
from c8y_api.model import ManagedObject

from tests.utils import RandomNameGenerator


@pytest.fixture(scope='session')
def object_factory(logger, live_c8y):
    """Provides a generic factory function which creates given ManagedObject
    instances within the database and cleans up afterwards.

    This fixture is supposed to be used by other fixtures.
    """

    created_objs = []

    def factory_fun(*objs: ManagedObject):
        logger.info(f"Creating {len(objs)} ManagedObject instances in live Cumulocity instance ...")
        for obj in objs:
            obj.c8y = live_c8y
            created_obj = obj.create()
            created_objs.append(created_obj)
            logger.info(f'Created ManagedObject: #{created_obj.id}, name: {obj.name}, type: {obj.type}')
        return created_objs

    yield factory_fun

    logger.info("Removing previously created ManagedObject instances ...")
    for created_obj in created_objs:
        created_obj.delete()
        logger.info(f"Deleted ManagedObject: #{created_obj.id}")


@pytest.fixture(scope='session')
def immutable_objects_with_common_type(logger, live_c8y, object_factory):
    """Provide a list of ManagedObjects having valid digital twins."""

    num = 5
    typename = 'test_' + RandomNameGenerator.random_name()
    logger.info(f"Creating managed objects with common type: {typename}")

    objs = [ManagedObject(type=typename, name=f'{typename}-{i}') for i in range(1, num+1)]
    yield object_factory(*objs)


@pytest.fixture(scope='function')
def mutable_object(logger, live_c8y, object_factory):
    """Provide a single mutable object with distincive name and type."""

    name = 'test_' + RandomNameGenerator.random_name()
    yield object_factory(ManagedObject(name=name, type=name))


@pytest.fixture(scope='function')
def mutable_objects_with_common_type(logger, live_c8y, object_factory):
    """Provide a list of ManagedObjects having valid digital twins."""

    num = 3
    typename = 'test_' + RandomNameGenerator.random_name()
    logger.info(f"Creating managed objects with common type: {typename}")

    objs = [ManagedObject(type=typename, name=f'{typename}-{i}') for i in range(1, num+1)]
    yield object_factory(*objs)


def test_get_all_by_type(live_c8y: CumulocityApi, immutable_objects_with_common_type):
    """Verify that get_all by type works as expected."""

    typename = immutable_objects_with_common_type[0].type
    result = live_c8y.inventory.get_all(type=typename)

    expected_ids = {x.id for x in immutable_objects_with_common_type}
    actual_ids = {x.id for x in result}

    assert actual_ids == expected_ids
