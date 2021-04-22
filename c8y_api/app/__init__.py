# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import os
import requests
from dataclasses import dataclass
from c8y_api._util import error, info
from c8y_api import CumulocityApi as NativeCumulocityApi


class CumulocityApi(NativeCumulocityApi):

    @dataclass
    class Auth:
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
            self.__auth_by_tenant[tenant] = CumulocityApi.Auth(username, password)

    @classmethod
    def get_bootstrap_instance(cls):
        if not cls.__bootstrap_instance:
            cls.__bootstrap_instance = CumulocityApi()
        return cls.__bootstrap_instance

    @classmethod
    def get_tenant_instance(cls, tenant_id):
        if tenant_id not in cls.__tenant_instances:
            cls.__tenant_instances[tenant_id] = CumulocityApi(tenant_id)
        return cls.__tenant_instances[tenant_id]
