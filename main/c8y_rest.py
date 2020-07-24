import os
import requests
import collections

from log_util import info, error


class __C8Y:

    def __init__(self):
        self.baseurl = self.__get_env('C8Y_BASEURL')
        self.bootstrap_tenant_id = self.__get_env('C8Y_BOOTSTRAP_TENANT')
        self.bootstrap_username = self.__get_env('C8Y_BOOTSTRAP_USER')
        self.bootstrap_password = self.__get_env('C8Y_BOOTSTRAP_PASSWORD')
        self.bootstrap_auth = self.__build_auth(self.bootstrap_tenant_id, self.bootstrap_username, self.bootstrap_password)
        self.__auth_by_tenant = {}
        self.__tfa_token = os.getenv('C8Y_TFATOKEN')
        self.__appuser = os.getenv('C8Y_USER')

    @staticmethod
    def __get_env(name):
        val = os.getenv(name)
        assert val, "Missing environment variable: " + name
        return val

    @staticmethod
    def __build_auth(tenant_id, username, password):
        return f'{tenant_id}/{username}', password

    def __get_current_tenant(self):
        r = requests.get(self.baseurl + '/tenant/currentTenant', auth=self.bootstrap_auth)
        if r.status_code != 200:
            error("Unable to perform GET request.", ("Status", r.status_code), ("Response", r.text))
        info("get tenant: %s", r.json())
        return r.json()['name']

    def __update_auth_cache(self):
        r = requests.get(self.baseurl + '/application/currentApplication/subscriptions', auth=self.bootstrap_auth)
        if r.status_code != 200:
            error("Unable to perform GET request.", ("Status", r.status_code), ("Response", r.text))
        info("get subscriptions: %s", r.json())
        self.__auth_by_tenant.clear()
        for subscription in r.json()['users']:
            tenant = subscription['tenant']
            username = subscription['name']
            password = subscription['password']
            self.__auth_by_tenant[tenant] = self.__build_auth(tenant, username, password)

    def __get_auth(self):
        if self.__appuser:  # indicating a per_tenant scope
            info("is own app, using bootstrap")
            return self.bootstrap_auth
        else:
            current_tenant = self.__get_current_tenant()
            if current_tenant not in self.__auth_by_tenant:
                self.__update_auth_cache()
            info("is subscribed app, using %s", self.__auth_by_tenant[current_tenant])
            return self.__auth_by_tenant[current_tenant]

    def __ensure_tfa_header(self, headers):
        return headers.update({'tfatoken': self.__tfa_token}) if self.__tfa_token else headers

    def get(self, resource, ordered=False):
        """Generic HTTP GET wrapper, dealing with standard error returning a JSON body object."""
        auth = self.__get_auth()
        headers = self.__ensure_tfa_header({})
        r = requests.get(self.baseurl + resource, auth=auth, headers=headers)
        if r.status_code != 200:
            error("Unable to perform GET request.", ("Status", r.status_code), ("Response", r.text))
        return r.json() if not ordered else r.json(object_pairs_hook=collections.OrderedDict)

    def post(self, resource, json):
        """Generic HTTP POST wrapper, dealing with standard error returning a JSON body object."""
        assert isinstance(json, dict)
        auth = self.__get_auth()
        headers = self.__ensure_tfa_header({'Accept': 'application/json'})
        r = requests.post(self.baseurl + resource, json=json, auth=auth, headers=headers)
        if r.status_code != 201:
            error("Unable to perform POST request.", ("Status", r.status_code), ("Response", r.text))
        return r.json()

    def delete(self, resource):
        """Generic HTTP DELETE wrapper, dealing with standard error returning a JSON body object."""
        auth = self.__get_auth()
        headers = self.__ensure_tfa_header({})
        r = requests.delete(self.baseurl + resource, auth=auth, headers=headers)
        if r.status_code != 204:
            error("Unable to perform DELETE request.", ("Status", r.status_code), ("Response", r.text))


__c8y = __C8Y()


def get(resource, ordered=False):
    return __c8y.get(resource, ordered)


def post(resource, json):
    return __c8y.post(resource, json)


def delete(resource):
    __c8y.delete(resource)
