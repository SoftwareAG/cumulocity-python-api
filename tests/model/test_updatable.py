# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
from abc import ABC
from typing import Set

import pytest

from c8y_api.model._base import SimpleObject
from c8y_api.model._updatable import _UpdatableSetProperty  # noqa (private)


class UpdatableSets:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._updated_sets = None

    def _signal_updated_set(self, name):
        if not self._updated_sets:
            self._updated_sets = {name}
        else:
            self._updated_sets.add(name)

    def get_updated_sets(self) -> Set[str]:
        return self._updated_sets if self._updated_sets else set()


class TestClass(SimpleObject, ABC):

    def __init__(self):
        super().__init__(c8y=None)

    regular_prop = SimpleObject.UpdatableProperty('regular_prop')


@pytest.fixture(scope='function')
def test_object() -> TestClass:
    return TestClass()


def test_regular_update(test_object: TestClass):
    test_object.regular_prop = 12
    assert test_object.regular_prop == 12
    assert test_object.__getattribute__('regular_prop') == 12
    assert test_object.get_updates() == {'regular_prop'}


class AnyClass(object):
    def __init__(self, prop):
        self._prop = prop if prop else set()
        self._orig_prop = None
    prop = _UpdatableSetProperty('_prop', '_orig_prop')


def test_predefined_set():
    obj = AnyClass(prop={'x'})
    obj.prop.add('a')
    obj.prop.remove('x')
    assert obj.prop == {'a'}


def test_empty_set():
    obj = AnyClass(prop=set())
    obj.prop.add('a')
    obj.prop.add('x')
    obj.prop.remove('x')
    assert obj.prop == {'a'}


def test_none():
    obj = AnyClass(prop=None)
    obj.prop.add('a')
    obj.prop.add('x')
    obj.prop.remove('x')
    assert obj.prop == {'a'}
