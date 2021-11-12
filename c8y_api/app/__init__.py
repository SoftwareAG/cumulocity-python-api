# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import dataclasses
import logging
import os

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
    def get_tenant_instance(cls, tenant_id) -> CumulocityApi:
        """Provide access to a tenant-specific instance in a multi-tenant
        application setup.

        Args:
            tenant_id (str):  ID of the tenant to get access to

        Returns:
            A CumulocityApi instance authorized for a tenant user
        """
        if tenant_id not in cls._tenant_instances:
            cls._tenant_instances[tenant_id] = CumulocityApp(tenant_id)
        return cls._tenant_instances[tenant_id]
