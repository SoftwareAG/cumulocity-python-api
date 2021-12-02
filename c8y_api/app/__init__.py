# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.
import base64
import dataclasses
import json
import logging
import os

from functools import lru_cache

from c8y_api._base_api import c8y_keys
from c8y_api._main_api import CumulocityApi


class CumulocityApp(CumulocityApi):
    """Application-like Cumulocity API.

    Provides usage centric access to a Cumulocity instance.

    Note: In contract to the standard Cumulocity API, this class evaluates
    the environment to resolve the authorization information automatically.
    This class is best used in Cumulocity microservices (applications).

    This class supports two application authentication modes:
        - PER_TENANT
        - MULTITENANT

    If the application is executed in PER_TENANT mode, all necessary
    authentication information is provided directly by Cumulocity as
    environment variables injected into the Docker container. A corresponding
    instance can be created by invoking `CumulocityApp()` (without any parameter).

    If the application is executed in MULTITENANT mode, only the so-called
    bootstrap user's authentication information is injected into the Docker
    container. An CumulocityApi instances providing access to a specific
    tenant can be obtained buy the application using the
    `get_tenant_instance` function or by invoking `CumulocityApp(id)` (with the
    ID of the tenant that should handle the requests).
    """
    @dataclasses.dataclass
    class Auth:
        """Bundles authentication information."""
        username: str
        password: str

    _auth_by_tenant = {}
    _bootstrap_instance = None
    _tenant_instances = {}

    _log = logging.getLogger(__name__)

    def __init__(self, tenant_id: str = None, application_key: str = None):
        """Create a new tenant specific instance.

        Args:
            tenant_id (str|None):  If None, it is assumed that the application
                is running in an PER_TENANT environment and the instance is
                created for the injected tenant information. Otherwise it is
                assumed that the application is running in a MULTITENANT
                environment and the provided ID reflects the ID of a
                subscribed tenant.
            application_key (str|None): An application key to include in
                all requests for tracking purposes.

        Returns:
            A new CumulocityApp instance
        """
        if tenant_id:
            self.tenant_id = tenant_id
            auth = self._get_tenant_auth(tenant_id)
            baseurl = self._get_env('C8Y_BASEURL')
            super().__init__(baseurl, tenant_id, auth.username, auth.password,
                             tfa_token=None, application_key=application_key)
        else:
            baseurl = self._get_env('C8Y_BASEURL')
            tenant_id = self._get_env('C8Y_TENANT')
            username = self._get_env('C8Y_USER')
            password = self._get_env('C8Y_PASSWORD')
            super().__init__(baseurl, tenant_id, username, password,
                             tfa_token=None, application_key=application_key)

    @staticmethod
    def _get_env(name: str) -> str:
        try:
            return os.environ[name]
        except KeyError as e:
            raise ValueError(f"Missing environment variable: {name}. Found {', '.join(c8y_keys())}.") from e

    @classmethod
    def _get_tenant_auth(cls, tenant_id: str) -> Auth:
        if tenant_id not in cls._auth_by_tenant:
            cls._auth_by_tenant = cls._read_subscriptions()
        return cls._auth_by_tenant[tenant_id]

    @classmethod
    def _read_subscriptions(cls):
        """Read subscribed tenant's auth information.

        Returns:
            A dict of tenant auth information by ID
        """
        subscriptions = cls.get_bootstrap_instance().get('/application/currentApplication/subscriptions')
        cache = {}
        for subscription in subscriptions['users']:
            tenant = subscription['tenant']
            username = subscription['name']
            password = subscription['password']
            cache[tenant] = CumulocityApp.Auth(username, password)
        return cache

    @classmethod
    def _create_bootstrap_instance(cls) -> CumulocityApi:
        baseurl = cls._get_env('C8Y_BASEURL')
        tenant_id = cls._get_env('C8Y_BOOTSTRAP_TENANT')
        username = cls._get_env('C8Y_BOOTSTRAP_USER')
        password = cls._get_env('C8Y_BOOTSTRAP_PASSWORD')
        return CumulocityApi(baseurl, tenant_id, username, password)

    @classmethod
    def get_bootstrap_instance(cls) -> CumulocityApi:
        """Provide access to the bootstrap instance in a multi-tenant
        application setup.

        Returns:
            A CumulocityApi instance authorized for the bootstrap user
        """
        if not cls._bootstrap_instance:
            cls._bootstrap_instance = cls._create_bootstrap_instance()
        return cls._bootstrap_instance

    @classmethod
    def get_tenant_instance(cls, tenant_id: str = None, headers: dict = None) -> CumulocityApi:
        """Provide access to a tenant-specific instance in a multi-tenant
        application setup.

        Args:
            tenant_id (str):  ID of the tenant to get access to
            headers (dict):  Inbound request headers, the tenant ID
                is resolved from the Authorization header

        Returns:
            A CumulocityApi instance authorized for a tenant user
        """
        # (1) if the tenant ID is specified we just
        if tenant_id:
            return cls._get_tenant_instance(tenant_id)

        # (2) otherwise, look for the Authorization header
        if not headers:
            raise RuntimeError("At least one of 'tenant_id' or 'headers' must be specified.")

        auth_header = headers[next(filter(lambda k: 'Authorization'.upper() == k.upper(), headers.keys()))]
        if not auth_header:
            raise ValueError("Missing Authentication header. Unable to resolve tenant ID.")

        return cls._get_tenant_instance(cls._resolve_tenant_id_from_auth_header(auth_header))

    @classmethod
    def _get_tenant_instance(cls, tenant_id: str) -> CumulocityApi:
        if tenant_id not in cls._tenant_instances:
            cls._tenant_instances[tenant_id] = CumulocityApp(tenant_id)
        return cls._tenant_instances[tenant_id]

    @classmethod
    @lru_cache(maxsize=128, typed=False)
    def _resolve_tenant_id_from_auth_header(cls, auth_header: str) -> str:
        auth_type, auth_value = auth_header.split(' ')

        if auth_type.upper() == 'BASIC':
            return cls._resolve_tenant_id_basic(auth_value)
        if auth_type.upper() == 'BEARER':
            return cls._resolve_tenant_id_token(auth_value)

        raise ValueError(f"Unexpected authorization header type: {auth_type}")

    @staticmethod
    def _resolve_tenant_id_basic(auth_string: str) -> str:
        decoded = base64.b64decode(bytes(auth_string, 'utf-8'))
        username = decoded.split(b':', 1)[0]
        if b'/' not in username:
            raise ValueError(f"nable to resolve tenant ID. Username '{username}' does not appear to include it.")
        return username.split(b'/', 1)[0].decode('utf-8')

    @classmethod
    def _resolve_tenant_id_token(cls, auth_token: str) -> str:
        # we assume that the token is an JWT token
        jwt_parts = auth_token.split('.')
        if len(jwt_parts) != 3:
            raise ValueError("Unexpected token format (not an JWT?). Unable to resolve tenant ID.")
        jwt_body = json.loads(base64.b64decode(jwt_parts[1].encode('utf-8')))
        if 'ten' not in jwt_body:
            raise ValueError("Unexpected token format (missing 'ten' claim). Unable to resolve tenant ID.")
        return jwt_body['ten']
