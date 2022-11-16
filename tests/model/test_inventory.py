# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
from unittest.mock import Mock

import pytest
from urllib import parse

from c8y_api import CumulocityRestApi
from c8y_api.model import Inventory
from c8y_api.model._util import _QueryUtil
from tests.utils import isolate_last_call_arg


@pytest.mark.parametrize('test, expected', [
    ('string', 'string'),
    ('with spaces', 'with spaces'),
    ('quote\'s', 'quote\'\'s')
])
def test_encode_odata_query_value(test, expected):
    """Verify that the query value encoding works as expected."""
    assert _QueryUtil.encode_odata_query_value(test) == expected


@pytest.mark.parametrize('name, expected', [
    ('some name', 'query=name eq \'some name\''),
    ('some\'s name', 'query=name eq \'some\'\'s name\'')
])
def test_select_by_name(name, expected):
    """Verify that the inventory's select function can filter by name."""

    # In the end, the select function should result in a GET request; the
    # result of this is not important, we simulate an empty result set.
    c8y: CumulocityRestApi = Mock()
    c8y.get = Mock(return_value={'managedObjects': []})

    inventory = Inventory(c8y)
    inventory.get_all(name=name)

    assert c8y.get.call_count == 1
    url = parse.unquote_plus(isolate_last_call_arg(c8y.get, 'resource', 0))
    assert expected in url


def test_select_by_name_plus():
    """Verify that the inventory's select function will put all filters
    as parts of a complex query."""

    c8y: CumulocityRestApi = Mock()
    c8y.get = Mock(return_value={'managedObjects': []})

    inventory = Inventory(c8y)
    inventory.get_all(name='NAME', fragment='FRAGMENT', type='TYPE', owner='OWNER')

    # we expect that the following strings are part of the resource string
    expected = [
        'query=$filter=(',
        'has(FRAGMENT)',
        'name eq \'NAME\'',
        'owner eq \'OWNER\'',
        'type eq \'TYPE\'']

    assert c8y.get.call_count == 1
    url = parse.unquote_plus(isolate_last_call_arg(c8y.get, 'resource', 0))

    for e in expected:
        assert e in url
