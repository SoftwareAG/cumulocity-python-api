# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import os
import requests
from dataclasses import dataclass

from c8y_api._util import error, info
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
    environment variables injected into the Docker container.

    If the application is executed in MULTITENANT mode, only the so-called
    bootstrap user's authentication information is injected into the Docker
    container. An CumulocityApi instances providing access to a specific
    tenant can be obtained buy the application using the
    `get_tenant_instance` function.
    """
    @dataclass
    class Auth:
        """Bundles authentication information."""
        username: str
        password: str

    __auth_by_tenant = {}
    __bootstrap_instance = None
    __tenant_instances = {}

    def __init__(self, tenant_id=None, application_key=None):
        self.baseurl = self.__get_env('C8Y_BASEURL')
        if tenant_id:
            self.tenant_id = tenant_id
            bootstrap_tenant_id = self.__get_env('C8Y_BOOTSTRAP_TENANT')
            bootstrap_username = self.__get_env('C8Y_BOOTSTRAP_USER')
            bootstrap_password = self.__get_env('C8Y_BOOTSTRAP_PASSWORD')
            self.__bootstrap_auth = self.__build_auth(bootstrap_tenant_id, bootstrap_username, bootstrap_password)
            auth = self.__get_auth(tenant_id)
            self.username = auth.username
            self.__password = auth.password
            super().__init__(self.baseurl, self.tenant_id, auth.username, auth.password,
                             tfa_token=None, application_key=application_key)
        else:
            self.tenant_id = self.__get_env('C8Y_TENANT')
            self.username = self.__get_env('C8Y_USER')
            self.__password = self.__get_env('C8Y_PASSWORD')
            super().__init__(self.baseurl, self.tenant_id, self.username, self.__password,
                             tfa_token=None, application_key=application_key)

    @staticmethod
    def __get_env(name):
        val = os.getenv(name)
        assert val, "Missing environment variable: " + name
        return val

    @staticmethod
    def __build_auth(tenant_id, username, password):
        return f'{tenant_id}/{username}', password

    def __get_auth(self, tenant_id):
        if tenant_id not in self.__auth_by_tenant:
            self.__update_auth_cache()
        return self.__auth_by_tenant[tenant_id]

    def __update_auth_cache(self):
        r = requests.get(self.baseurl + '/application/currentApplication/subscriptions', auth=self.__bootstrap_auth)
        if r.status_code != 200:
            error("Unable to perform GET request.", ("Status", r.status_code), ("Response", r.text))
        info("get subscriptions: %s", r.json())
        self.__auth_by_tenant.clear()
        for subscription in r.json()['users']:
            tenant = subscription['tenant']
            username = subscription['name']
            password = subscription['password']
            self.__auth_by_tenant[tenant] = CumulocityApp.Auth(username, password)

    @classmethod
    def get_bootstrap_instance(cls) -> CumulocityApi:
        """Provide access to the bootstrap instance in a multi-tenant
        application setup.

        Returns:
            A CumulocityApi instance authorized for the bootstrap user
        """
        if not cls.__bootstrap_instance:
            cls.__bootstrap_instance = CumulocityApp()
        return cls.__bootstrap_instance

    @classmethod
    def get_tenant_instance(cls, tenant_id) -> CumulocityApi:
        """Provide access to a tenant-specific instance in a multi-tenant
        application setup.

        Args:
            tenant_id (str):  ID of the tenant to get access to

        Returns:
            A CumulocityApi instance authorized for a tenant user
        """
        if tenant_id not in cls.__tenant_instances:
            cls.__tenant_instances[tenant_id] = CumulocityApp(tenant_id)
        return cls.__tenant_instances[tenant_id]
