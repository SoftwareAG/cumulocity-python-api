import os
import requests
from dataclasses import dataclass
from log_util import error, info
from c8y_api import C8Y as PURE_C8Y


class C8Y(PURE_C8Y):
    @dataclass
    class Auth:
        username: str
        password: str

    __auth_by_tenant = {}
    __bootstrap_instance = None
    __tenant_instances = {}

    def __init__(self, tenant_id=None):
        self.baseurl = self.__get_env('C8Y_BASEURL')
        self.bootstrap_tenant_id = self.__get_env('C8Y_BOOTSTRAP_TENANT')
        self.bootstrap_username = self.__get_env('C8Y_BOOTSTRAP_USER')
        self.__bootstrap_password = self.__get_env('C8Y_BOOTSTRAP_PASSWORD')
        self.__bootstrap_auth = self.__build_auth(self.bootstrap_tenant_id, self.bootstrap_username,
                                                  self.__bootstrap_password)
        self.tenant_id = tenant_id
        if tenant_id:
            auth = self.__get_auth(tenant_id)
            super().__init__(self.baseurl, self.tenant_id, auth.username, auth.password)
        else:
            super().__init__(self.baseurl, self.bootstrap_tenant_id, self.bootstrap_username, self.__bootstrap_password)

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
            self.__auth_by_tenant[tenant] = C8Y.Auth(username, password)

    @classmethod
    def get_bootstrap_instance(cls):
        if not cls.__bootstrap_instance:
            cls.__bootstrap_instance = C8Y()
        return cls.__bootstrap_instance

    @classmethod
    def get_tenant_instance(cls, tenant_id):
        if tenant_id not in cls.__tenant_instances:
            cls.__tenant_instances[tenant_id] = C8Y(tenant_id)
        return cls.__tenant_instances[tenant_id]
