import pytest
import json

from c8y_api.model import GlobalRole


def test_to_full_json():
    gr = GlobalRole(name="SomeName", description="SomeDescription", permission_ids=['ABC'])
    j = gr.to_full_json()
    assert set(j.keys()) == {'name', 'description'}
    assert j['name'] == 'SomeName'
    assert j['description'] == 'SomeDescription'


def test_to_diff_json_1():
    gr1 = GlobalRole(name="SomeName", description="SomeDescription", permission_ids=['ABC'])
    gr1.name = "NewName"
    j1 = gr1.to_diff_json()
    assert set(j1.keys()) == {'name'}
    assert j1['name'] == 'NewName'
