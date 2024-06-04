# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
# pylint: disable=protected-access

from unittest.mock import Mock

import pytest
from urllib import parse

from c8y_api import CumulocityRestApi, CumulocityApi
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
        'query=',
        'has(FRAGMENT)',
        'name eq \'NAME\'',
        'owner eq \'OWNER\'',
        'type eq \'TYPE\'']

    assert c8y.get.call_count == 1
    url = parse.unquote_plus(isolate_last_call_arg(c8y.get, 'resource', 0))

    for e in expected:
        assert e in url


def _invoke_target_and_isolate_url(target, kwargs):
    """Auxiliary function to invoke a dynamic target function on a
    fake CumulocityApi instance and return the resource of a get call."""
    c8y: CumulocityApi = CumulocityApi('base', 'tenant','user', 'pass')
    c8y.get = Mock(return_value={'managedObjects': [], 'statistics': {'totalPages': 1}})
    api, fun = target.split('.', maxsplit=1)
    getattr(getattr(c8y, api), fun)(**kwargs)
    return parse.unquote_plus(isolate_last_call_arg(c8y.get, 'resource', 0))


@pytest.mark.parametrize(
    'target',
    [
        'inventory.get_all',
        'inventory.get_count',
        'device_inventory.get_all',
        'device_inventory.get_count',
        'group_inventory.get_all',
        'group_inventory.get_count',
    ])
@pytest.mark.parametrize(
    'name, args',
    [
        ('name', {
            'kwargs': {'name': 'NAME'},
            'expected': ["name eq 'NAME'"],
            'not_expected': []
        }),
        ('type', {
            'kwargs': {'type': 'TYPE'},
            'expected': ['type=TYPE'],
            'not_expected': ['and']
        }),
        ('owner', {
            'kwargs': {'owner': 'OWNER'},
            'expected': ['owner=OWNER'],
            'not_expected': ['and']
        }),
        ('text', {
            'kwargs': {'text': 'TEXT'},
            'expected': ['text=TEXT'],
            'not_expected': ['and']
        }),
        ('ids', {
            'kwargs': {'ids': ['id1', 'id2']},
            'expected': ['ids=id1,id2'],
            'not_expected': ['and']
        }),
    ])
def test_all_inventory_filters(target, name, args):
    """Verify that the filter parameters are all forwarded correctly
    end-to-end through all abstract helper methods."""
    kwargs = args['kwargs']
    expected = args['expected']
    not_expected = args['not_expected']
    url = _invoke_target_and_isolate_url(target, kwargs)
    for e in expected:
        assert e in url
    for n in not_expected:
        assert n not in url


def execute_test_device_inventory_filters(target, args):
    """Verify that the filter parameters are all forwarded correctly
    end-to-end through all abstract helper methods."""
    kwargs = args['kwargs']
    expected = args['expected']
    not_expected = args['not_expected']

    c8y: CumulocityApi = CumulocityApi('base', 'tenant', 'user', 'pass')
    c8y.get = Mock(return_value={'managedObjects': [], 'statistics': {'totalPages': 1}})
    api, fun = target.split('.', maxsplit=1)
    getattr(getattr(c8y, api), fun)(**kwargs)

    url = parse.unquote_plus(isolate_last_call_arg(c8y.get, 'resource', 0))
    for e in expected:
        assert e in url
    for n in not_expected:
        assert n not in url


@pytest.mark.parametrize(
    'target',
    [
        'inventory.get_all',
        'inventory.get_count',
    ])
@pytest.mark.parametrize(
    'name, args',
    [
        ('name', {
            'kwargs': {'name': 'NAME'},
            'expected': ["query=name eq 'NAME'"],
            'not_expected': ['and']
        }),
        ('fragment', {
            'kwargs': {'fragment': 'FRAGMENT'},
            'expected': ["fragmentType=FRAGMENT"],
            'not_expected': ['and']
         }),
        ('name+fragment', {
            'kwargs': {'name': 'NAME', 'fragment': 'FRAGMENT'},
            'expected': ["query=", "name eq 'NAME'", " and ", "has(FRAGMENT)"],
            'not_expected': []
         }),
        ('query', {
            'kwargs': {'query': 'SOMETHING'},
            'expected': ['query=SOMETHING'],
            'not_expected': ['and']
         }),
        ('query+type', {
            'kwargs': {'query': 'SOMETHING', 'type': 'TYPE'},
            'expected': ['query=SOMETHING'],
            'not_expected': ['and type=', 'TYPE']
         }),
        ('expression', {
            'kwargs': {'expression': 'SOMETHING'},
            'expected': ['SOMETHING&'],
            'not_expected': ['and']
         }),
        ('expression+type', {
            'kwargs': {'expression': 'SOMETHING', 'type': 'TYPE'},
            'expected': ['SOMETHING&'],
            'not_expected': ['type=', 'TYPE']
         }),
    ])
def test_pure_inventory_filters(target, name, args):
    """Verify that the filter parameters are all forwarded correctly
    end-to-end through all abstract helper methods."""
    execute_test_device_inventory_filters(target, args)


@pytest.mark.parametrize(
    'target',
    [
        'device_inventory.get_all',
        'device_inventory.get_count',
    ])
@pytest.mark.parametrize(
    'name, args',
    [
        ('name', {
            'kwargs': {'name': 'NAME'},
            'expected': ["query=", "has(c8y_IsDevice)", "and", "name eq 'NAME'"],
            'not_expected': []
        }),
    ])
def test_device_inventory_filters(target, name, args):
    """Verify that the filter parameters are all forwarded correctly
    end-to-end through all abstract helper methods."""
    execute_test_device_inventory_filters(target, args)


@pytest.mark.parametrize(
    'target',
    [
        'group_inventory.get_all',
        'group_inventory.get_count',
    ])
@pytest.mark.parametrize(
    'name, args',
    [
        ('parent', {
            'kwargs': {'parent': 'PARENT'},
            'expected': ['query=', 'bygroupid(PARENT)', "type eq 'c8y_DeviceSubGroup'"],
            'not_expected': ['$filter']
        }),
        ('name+parent', {
            'kwargs': {'name': 'NAME', 'parent': 'PARENT'},
            'expected': ['query=', 'bygroupid(PARENT)', "name eq 'NAME'", "type eq 'c8y_DeviceSubGroup'"],
            'not_expected': ['$filter']
        }),
        ('name+parent+query', {
            'kwargs': {'name': 'NAME', 'parent': 'PARENT', 'query': '$func=(QUERY)'},
            'expected': ['query=', '$filter=', 'bygroupid(PARENT)', "name eq 'NAME'",
                         "type eq 'c8y_DeviceSubGroup'", '$func=(QUERY)'],
            'not_expected': []
        }),
    ])
def test_group_inventory_filters(target, name, args):
    """Verify that the filter parameters are all forwarded correctly
    end-to-end through all abstract helper methods."""
    execute_test_device_inventory_filters(target, args)
