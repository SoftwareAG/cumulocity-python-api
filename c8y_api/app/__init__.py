# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from abc import abstractmethod
import logging
import os

from cachetools import TTLCache
from requests.auth import HTTPBasicAuth, AuthBase

from c8y_api._auth import AuthUtil
from c8y_api._main_api import CumulocityApi
from c8y_api._util import c8y_keys


class _CumulocityAppBase(object):
    """Internal class, base for both Per Tenant and Multi Tenant specifc
    implementation."""

    def __init__(self, log: logging.Logger, cache_size: int = 100, cache_ttl: int = 3600, **kwargs):
        super().__init__(**kwargs)
        self.log = log
        self.user_instances = TTLCache(maxsize=cache_size, ttl=cache_ttl)

    @abstractmethod
    def _build_user_instance(self, auth: AuthBase) -> CumulocityApi:
        """This must be defined by the implementing classes."""

    def get_user_instance(self, headers: dict = None) -> CumulocityApi:
        """Return a user-specific CumulocityApi instance.

        The instance will have user access, based on the Authorization header
        provided in the headers dict. The instance will be build on demand,
        previously created instances are cached.

        Args:
            headers (dict): A dictionarity of HTTP header entries. The user
                access is based on the Authorization header within.

        Returns:
            A CumulocityApi instance authorized for a named user.
        """
        auth_header = self._get_auth_header(headers)
        try:
            return self.user_instances[auth_header]
        except KeyError:
            instance = self._build_user_instance(AuthUtil.parse_auth_string(auth_header))
            self.user_instances[auth_header] = instance
            return instance

    def clear_user_cache(self, username: str = None):
        """Manually clean the user sessions cache.

        Args:
            username (str):  Name of a specific user to remove or None
                to clean the cache completely
        """
        if not username:
            self.user_instances.clear()
            self.log.info("User cache cleared.")
        else:
            for auth_header, item in self.user_instances.items():
                if username == AuthUtil.get_username(AuthUtil.parse_auth_string(auth_header)):
                    del item
                    self.log.info(f"User '{username}' cleared from cache.")

    @staticmethod
    def _get_auth_header(headers: dict) -> str:
        """Extract the Authorization header from a headers dictionary."""
        try:
            return headers[next(filter(lambda k: k.upper() == 'AUTHORIZATION', headers.keys()))]
        except StopIteration as ex:
            keys = ", ".join(headers.keys()) or "None"
            raise KeyError(f"Unable to resolve Authorization header. Found keys: {keys}.") from ex

    @staticmethod
    def _get_env(name: str) -> str:
        """Try to read a specific Cumulocity environment variable.

        Args:
            name (str):  Environment variable key

        Returns:
            The value of the environment variable.

        Raises:
            ValueError (not KeyError!) if the variable is not present.
        """
        try:
            return os.environ[name]
        except KeyError as e:
            keys = ', '.join(c8y_keys()) or "none"
            raise ValueError(f"Missing environment variable: {name}. Found {keys}.") from e


class SimpleCumulocityApp(_CumulocityAppBase, CumulocityApi):
    """Application-like Cumulocity API.

    The SimpleCumulocityApp class is intended to be used as base within
    a single-tenant micro service hosted on Cumulocity. It evaluates the
    environment to teh resolve the authentication information automatically.

    Note: This class should be used in Cumulocity micro services using the
    PER_TENANT authentication mode only. It will not function in environments
    using the MULTITENANT mode.

    The SimpleCumulocityApp class is an enhanced version of the standard
    CumulocityApi class. All Cumulocity functions can be used directly.
    Additionally it can be used to provide CumulocityApi instances for
    specific named users via the `get_user_instance` function.
    """

    _log = logging.getLogger(__name__)

    def __init__(self, application_key: str = None, cache_size: int = 100, cache_ttl: int = 3600):
        """Create a new tenant specific instance.

        Args:
            application_key (str|None): An application key to include in
                all requests for tracking purposes.
            cache_size (int|None): The maximum number of cached user
                instances (if user instances are created at all).
            cache_ttl (int|None): An maximum cache time for user
                instances (if user instances are created at all).

        Returns:
            A new CumulocityApp instance
        """
        baseurl = self._get_env('C8Y_BASEURL')
        tenant_id = self._get_env('C8Y_TENANT')
        username = self._get_env('C8Y_USER')
        password = self._get_env('C8Y_PASSWORD')
        super().__init__(log=self._log, cache_size=cache_size, cache_ttl=cache_ttl,
                         base_url=baseurl, tenant_id=tenant_id, auth=HTTPBasicAuth(f'{tenant_id}/{username}', password),
                         application_key=application_key)

    def _build_user_instance(self, auth) -> CumulocityApi:
        """Build a CumulocityApi instance for a specific user, using the
        same Base URL, Tenant ID and Application Key as the main instance."""
        return CumulocityApi(base_url=self.base_url, tenant_id=self.tenant_id, auth=auth,
                             application_key=self.application_key)


class MultiTenantCumulocityApp(_CumulocityAppBase):
    """Multi-tenant enabled Cumulocity application wrapper.

    The MultiTenantCumulocityApp class is intended to be used as base within
    a multi-tenant micro service hosted on Cumulocity. It evaluates the
    environment to teh resolve the bootstrap authentication information
    automatically.

    Note: This class is intended to be used in Cumulocity micro services
    using the MULTITENANT authentication mode. It will not function in
    PER_TENANT environments.

    The MultiTenantCumulocityApp class serves as a factory. It provides
    access to tenant-specific CumulocityApi instances via the
    `get_tenant_instance` function. A special bootstrap CumulocityApi
    instance is available via the `bootstrap_instance` property.
    """

    _log = logging.getLogger(__name__)

    def __init__(self, application_key: str = None, cache_size: int = 100, cache_ttl: int = 3600):
        super().__init__(log=self._log, cache_size=cache_size, cache_ttl=cache_ttl)
        self.application_key = application_key
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.bootstrap_instance = self._create_bootstrap_instance()
        self._subscribed_auths = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        self._tenant_instances = TTLCache(maxsize=cache_size, ttl=cache_ttl)

    def _get_tenant_auth(self, tenant_id: str) -> AuthBase:
        """Cached access to auth information of subscribed tenants."""
        try:
            return self._subscribed_auths[tenant_id]
        except KeyError:
            self._subscribed_auths = self._read_subscriptions(self.bootstrap_instance)
            return self._subscribed_auths[tenant_id]

    @classmethod
    def _read_subscriptions(cls, bootstrap_instance: CumulocityApi):
        """Read subscribed tenant's auth information.

        Returns:
            A dict of tenant auth information by ID
        """
        subscriptions = bootstrap_instance.get('/application/currentApplication/subscriptions')
        cache = {}
        for subscription in subscriptions['users']:
            tenant = subscription['tenant']
            username = subscription['name']
            password = subscription['password']
            cache[tenant] = HTTPBasicAuth(f'{tenant}/{username}', password)
        return cache

    @classmethod
    def _create_bootstrap_instance(cls) -> CumulocityApi:
        """Build the bootstrap instance from the environment."""
        baseurl = cls._get_env('C8Y_BASEURL')
        tenant_id = cls._get_env('C8Y_BOOTSTRAP_TENANT')
        username = cls._get_env('C8Y_BOOTSTRAP_USER')
        password = cls._get_env('C8Y_BOOTSTRAP_PASSWORD')
        return CumulocityApi(baseurl, tenant_id, username, password)

    def _create_tenant_instance(self, tenant_id: str) -> CumulocityApi:
        """Build a tenant instance."""
        auth = self._get_tenant_auth(tenant_id)
        return CumulocityApi(self.bootstrap_instance.base_url, tenant_id, auth=auth,
                             application_key=self.application_key)

    def _build_user_instance(self, auth) -> CumulocityApi:
        """Build a CumulocityApi instance for a specific user, using the
        same Base URL, Tenant ID and Application Key as the main instance."""
        tenant_id = AuthUtil.get_tenant_id(auth)
        return CumulocityApi(base_url=self.bootstrap_instance.base_url, tenant_id=tenant_id, auth=auth,
                             application_key=self.application_key)

    def get_tenant_instance(self, tenant_id: str = None, headers: dict = None) -> CumulocityApi:
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
            return self._get_tenant_instance(tenant_id)

        # (2) otherwise, look for the Authorization header
        if not headers:
            raise RuntimeError("At least one of 'tenant_id' or 'headers' must be specified.")

        auth_header = headers[next(filter(lambda k: 'Authorization'.upper() == k.upper(), headers.keys()))]
        if not auth_header:
            raise ValueError("Missing Authentication header. Unable to resolve tenant ID.")

        tenant_id = AuthUtil.get_tenant_id(AuthUtil.parse_auth_string(auth_header))
        return self._get_tenant_instance(tenant_id)

    def _get_tenant_instance(self, tenant_id: str) -> CumulocityApi:
        """Cached access to already build tenant instances."""
        try:
            return self._tenant_instances[tenant_id]
        except KeyError:
            instance = self._create_tenant_instance(tenant_id)
            self._tenant_instances[tenant_id] = instance
            return instance
