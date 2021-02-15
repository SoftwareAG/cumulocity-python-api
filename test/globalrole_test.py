# Copyright (c) 2020 Software AG, Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA, and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except as specifically provided for in your License Agreement with Software AG

import pytest
import json

from c8y_api.model import GlobalRole


def test_to_full_json():
    gr = GlobalRole(name="SomeName", description="SomeDescription", permission_ids=['ABC'])
    j = gr._to_full_json()
    assert set(j.keys()) == {'name', 'description'}
    assert j['name'] == 'SomeName'
    assert j['description'] == 'SomeDescription'


def test_to_diff_json_1():
    gr1 = GlobalRole(name="SomeName", description="SomeDescription", permission_ids=['ABC'])
    gr1.name = "NewName"
    j1 = gr1._to_diff_json()
    assert set(j1.keys()) == {'name'}
    assert j1['name'] == 'NewName'
