# Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

import pytest

from c8y_api.model._util import _UpdatableSetProperty


class TestClass(object):
    def __init__(self, prop):
        self._prop = prop if prop else set()
        self._orig_prop = None
    prop = _UpdatableSetProperty('_prop', '_orig_prop')


def test_UpdatableSetProperty_1():
    obj = TestClass(prop={'x'})
    obj.prop.add('a')
    obj.prop.remove('x')
    assert obj.prop == {'a'}


def test_UpdatableSetProperty_2():
    obj = TestClass(prop=set())
    obj.prop.add('a')
    obj.prop.add('x')
    obj.prop.remove('x')
    assert obj.prop == {'a'}


def test_UpdatableSetProperty_3():
    obj = TestClass(prop=None)
    obj.prop.add('a')
    obj.prop.add('x')
    obj.prop.remove('x')
    assert obj.prop == {'a'}
