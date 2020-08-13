import requests
import collections

from log_util import error
from c8y_model import Inventory, Measurements


class C8Y:

    def __init__(self, base_url, tenant_id, username, password, tfa_token=None):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.username = username
        self.password = password
        self.tfa_token = tfa_token
        self.__auth = f'{tenant_id}/{username}', password
        self.__default_headers = {'tfatoken': self.tfa_token} if self.tfa_token else {}
        self.__measurements = Measurements(self)  # todo: lazy?
        self.__inventory = Inventory(self)  # todo: lazy?

    def get(self, resource, ordered=False):
        """Generic HTTP GET wrapper, dealing with standard error returning a JSON body object."""
        r = requests.get(self.base_url + resource, auth=self.__auth, headers=self.__default_headers)
        if r.status_code != 200:
            error("Unable to perform GET request.", ("Status", r.status_code), ("Response", r.text))
        return r.json() if not ordered else r.json(object_pairs_hook=collections.OrderedDict)

    def post(self, resource, json):
        """Generic HTTP POST wrapper, dealing with standard error returning a JSON body object."""
        assert isinstance(json, dict)
        headers = {'Accept': 'application/json', **self.__default_headers}
        r = requests.post(self.base_url + resource, json=json, auth=self.__auth, headers=headers)
        if r.status_code != 201:
            error("Unable to perform POST request.", ("Status", r.status_code), ("Response", r.text))
        return r.json()

    def put(self, resource, json):
        """Generic HTTP PUT wrapper, dealing with standard error returning a JSON body object."""
        assert isinstance(json, dict)
        headers = {'Accept': 'application/json', **self.__default_headers}
        r = requests.put(self.base_url + resource, json=json, auth=self.__auth, headers=headers)
        if r.status_code != 200:
            error("Unable to perform POST request.", ("Status", r.status_code), ("Response", r.text))
        return r.json()

    def delete(self, resource):
        """Generic HTTP DELETE wrapper, dealing with standard error returning a JSON body object."""
        r = requests.delete(self.base_url + resource, auth=self.__auth, headers=self.__default_headers)
        if r.status_code != 204:
            error("Unable to perform DELETE request.", ("Status", r.status_code), ("Response", r.text))

    @property
    def measurements(self):
        return self.__measurements

    @property
    def inventory(self):
        return self.__inventory
