# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import base64
import os
from unittest.mock import patch

import jwt
import pytest
import responses
from unittest import mock

from c8y_api import CumulocityApi
from c8y_api.app import CumulocityApp


env_per_tenant = {
    'C8Y_BASEURL': 'http://baseurl',
    'C8Y_TENANT': 'tenant_id',
    'C8Y_USER': 'tenant_user',
    'C8Y_PASSWORD': 'tenant_password'
}

env_multi_tenant = {
    'C8Y_BASEURL': 'http://baseurl',
    'C8Y_BOOTSTRAP_TENANT': 'tenant_id',
    'C8Y_BOOTSTRAP_USER': 'tenant_user',
    'C8Y_BOOTSTRAP_PASSWORD': 'tenant_password'

}


@mock.patch.dict(os.environ, env_per_tenant, clear=True)
def test_per_tenant():
    """Verify that the instance will be created properly within a
    per tenant environment"""

    c8y = CumulocityApp()

    assert c8y.tenant_id == env_per_tenant['C8Y_TENANT']
    assert c8y.username == env_per_tenant['C8Y_USER']
    assert c8y.password == env_per_tenant['C8Y_PASSWORD']

    with responses.RequestsMock() as rsps:
        rsps.add(method='GET',
                 url=env_per_tenant['C8Y_BASEURL'] + '/xyz',
                 status=200,
                 json={})
        c8y.get('/xyz')


@mock.patch.dict(os.environ, env_multi_tenant, clear=True)
def test_multi_tenant__invalid_call():
    """Verify that calling the constructor without arguments in a multi-tenant
    environment will result in an ValueError."""

    with pytest.raises(ValueError) as e:
        CumulocityApp()

    assert 'C8Y' in str(e)


@mock.patch.dict(os.environ, env_multi_tenant, clear=True)
def test_multi_tenant__bootstrap_instance():
    """Verify that the bootstrap instance will be created propertly within a
    multi-tenant environment."""

    c8y = CumulocityApp.get_bootstrap_instance()

    assert c8y.tenant_id == env_multi_tenant['C8Y_BOOTSTRAP_TENANT']
    assert c8y.username == env_multi_tenant['C8Y_BOOTSTRAP_USER']
    assert c8y.password == env_multi_tenant['C8Y_BOOTSTRAP_PASSWORD']

    with responses.RequestsMock() as rsps:
        rsps.add(method='GET',
                 url=env_multi_tenant['C8Y_BASEURL'] + '/xyz',
                 status=200,
                 json={})
        c8y.get('/xyz')


@mock.patch.dict(os.environ, env_multi_tenant, clear=True)
def test_multi_tenant__cached_instances():
    """Verify that instances are cached by their tenant ID and the cache
    is evaluated propertly."""
    # pylint: disable=protected-access

    # prepare a mock instance cache
    cached_tenants = {'t12345': CumulocityApi('baseurl', 't12345', 'user', 'password')}

    with patch.object(CumulocityApp, '_get_tenant_auth') as get_auth_mock:
        get_auth_mock.return_value = CumulocityApp.Auth('username', 'password')

        # when the instance of the requested ID is in the cache it will be
        # retured and no further calls are necessary
        with patch.dict(CumulocityApp._tenant_instances, cached_tenants):
            c8y = CumulocityApp.get_tenant_instance('t12345')
            # -> attributes reflect what's in the mock cache
            assert c8y.tenant_id == 't12345'
            assert c8y.username == 'user'
            assert c8y.password == 'password'
        # -> the tenant auth info was not refreshed
        get_auth_mock.assert_not_called()

        # when the constructor is called an new instance is created in an case
        # here this will result in the mock being called
        c8y = CumulocityApp('t12345')
        # -> the tenant auth info was read
        get_auth_mock.assert_called()
        # -> the attributes reflect what the auth call returned
        assert c8y.tenant_id == 't12345'
        assert c8y.base_url == env_multi_tenant['C8Y_BASEURL']
        assert c8y.username == 'username'
        assert c8y.password == 'password'


@mock.patch.dict(os.environ, env_multi_tenant, clear=True)
def test_multi_tenant__caching_instances():
    """Verify that a uncached instance is build using the """
    # pylint: disable=protected-access

    with patch.object(CumulocityApp, '_read_subscriptions') as read_subscriptions:
        read_subscriptions.return_value = {'t12345': CumulocityApp.Auth('username', 'password')}

        c8y = CumulocityApp.get_tenant_instance('t12345')

        # -> auth cache was rebuild
        read_subscriptions.assert_called()
        # -> instance is now in cache
        assert 't12345' in CumulocityApp._tenant_instances
        # -> attributes reflect was was returned by the subscriptions mock
        assert c8y.tenant_id == 't12345'
        assert c8y.username == 'username'
        assert c8y.password == 'password'


@mock.patch.dict(os.environ, env_multi_tenant, clear=True)
def test_read_subscriptions():
    """Verify that the subscriptions are read and parsed properly."""
    # pylint: disable=protected-access

    mock_response = {'users': [
        {'tenant': 't12345',
         'name': 'user12345',
         'password': 'pass12345'},
        {'tenant': 't54321',
         'name': 'user54321',
         'password': 'pass54321'},
    ]}

    with responses.RequestsMock() as rsps:
        rsps.add(method='GET',
                 url=env_multi_tenant['C8Y_BASEURL'] + '/application/currentApplication/subscriptions',
                 status=200,
                 json=mock_response)

        subscriptions = CumulocityApp._read_subscriptions()
        assert 't12345' in subscriptions
        assert 't54321' in subscriptions
        assert subscriptions['t12345'].password == 'pass12345'
        assert subscriptions['t54321'].username == 'user54321'


def test_get_tenant_instance_from_headers():
    """Verify that the authorization header is parsed and passed correctly
    when the tenant ID is resolved from the request headers."""

    # we setup the internal resolve function to return a proper tenant ID
    with patch('c8y_api.app.CumulocityApp._resolve_tenant_id_from_auth_header') as resolve_mock:
        resolve_mock.return_value = 't12345'

        # we intercept all calls to the internal _get function
        with patch('c8y_api.app.CumulocityApp._get_tenant_instance') as get_mock:
            CumulocityApp.get_tenant_instance(headers={'auTHOrization': 'auth_header'})
            # -> the resolve function is called with the parsed auth header
            resolve_mock.assert_called_once_with('auth_header')
            # -> the get function is called with the tenant ID returned
            #    by the resolve function
            get_mock.assert_called_once_with('t12345')


def b64encode(auth_string: str) -> str:
    """Encode a string with base64. This uses UTF-8 encoding."""
    return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')


@pytest.mark.parametrize('auth_string, tenant_id', [
    ('t12345/some@domain.com:password', 't12345'),
    ('t12345/some@domain.com', 't12345')])
def test_resolve_tenant_basic(auth_string: str, tenant_id: str):
    """Verify that parsing of an Basic authentication string works as expected."""
    # pylint: disable=protected-access
    assert tenant_id == CumulocityApp._resolve_tenant_id_basic(b64encode(auth_string))


@pytest.mark.parametrize('auth_string, hint', [
    ('some@domain.com:password', 'tenant')])
def test_resolve_tenant_basic_bad(auth_string: str, hint: str):
    """Verify that parsing of an Basic authentication string works as expected."""
    # pylint: disable=protected-access
    with pytest.raises(ValueError) as e:
        CumulocityApp._resolve_tenant_id_basic(b64encode(auth_string))
    assert hint in str(e)


def test_resolve_tenant_token():
    """Verify that parsing of an Bearer authentication string works as expected."""
    # pylint: disable=protected-access
    payload = {
        'jti': None,
        'iss': 't12345.cumulocity.com',
        'aud': 't12345.cumulocity.com',
        'sub': 'some.user@softwareag.com',
        'tci': '0722ff7b-684f-4177-9614-3b7949b0b5c9',
        'iat': 1638281885,
        'nbf': 1638281885,
        'exp': 1639491485,
        'tfa': False,
        'ten': 't12345',
        'xsrfToken': 'something'}
    encoded = jwt.encode(payload, key='key')
    assert CumulocityApp._resolve_tenant_id_token(encoded) == 't12345'
