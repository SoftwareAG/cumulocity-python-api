# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import sys
import requests
import collections
import time
import yaml
from dataclasses import dataclass

from c8y_api._util import debug
from c8y_api.model.inventory import Inventory, Identity, Binary, DeviceGroupInventory, DeviceInventory
from c8y_api.model.administration import Users, GlobalRoles, InventoryRoles
from c8y_api.model.measurements import Measurements
from c8y_api.model.applications import Applications
from c8y_api.model.events import Events
from c8y_api.model.alarms import Alarms


class CumulocityRestApi:

    def __init__(self, base_url, tenant_id, username, password, tfa_token=None, application_key=None):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.username = username
        self.password = password
        self.tfa_token = tfa_token
        self.application_key = application_key
        self.__auth = f'{tenant_id}/{username}', password
        self.__default_headers = {}
        if self.tfa_token:
            self.__default_headers['tfatoken'] = self.tfa_token
        if self.application_key:
            self.__default_headers['X-Cumulocity-Application-Key'] = self.application_key
        self.session = requests.Session()

    def prepare_request(self, method, resource, body=None, additional_headers=None):
        hs = self.__default_headers
        if additional_headers:
            hs.update(additional_headers)
        rq = requests.Request(method=method, url=self.base_url + resource, headers=hs, auth=self.__auth)
        if body:
            rq.json = body
        return rq.prepare()

    def get(self, resource, ordered=False):
        """Generic HTTP GET wrapper, dealing with standard error returning a JSON body object."""
        r = self.session.get(self.base_url + resource, auth=self.__auth, headers=self.__default_headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid GET request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 200:
            raise ValueError(f"Unable to perform GET request. Status: {r.status_code} Response:\n" + r.text)
        return r.json() if not ordered else r.json(object_pairs_hook=collections.OrderedDict)

    def post(self, resource, json, accept='application/json', content_type=None):
        """Generic HTTP POST wrapper, dealing with standard error returning a JSON body object."""
        assert isinstance(json, dict)
        headers = self.__default_headers.copy()
        if accept:
            headers['Accept'] = accept
        if content_type:
            headers['Content-Type'] = content_type
        r = self.session.post(self.base_url + resource, json=json, auth=self.__auth, headers=headers)
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid POST request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 201 and r.status_code != 200:
            raise ValueError(f"Unable to perform POST request. Status: {r.status_code} Response:\n" + r.text)
        return r.json()

    def post_file(self, resource, file, binary_meta_information):
        assert isinstance(binary_meta_information, Binary)
        assert file is not None

        headers = {'Accept': 'application/json', **self.__default_headers}

        payload = {
            'object': (None, str(binary_meta_information._to_full_json()).replace("'", '"')),
            'filesize': (None, sys.getsizeof(file)),
            'file': (None, file.read())
        }

        r = self.session.post(self.base_url + resource, files=payload, auth=self.__auth, headers=headers)
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid POST request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 201:
            raise ValueError("Unable to perform POST request.", ("Status", r.status_code), ("Response", r.text))
        return r.json()

    def put(self, resource, json, accept='application/json', content_type=None):
        """Generic HTTP PUT wrapper, dealing with standard error returning a JSON body object."""
        assert isinstance(json, dict)
        headers = self.__default_headers.copy()
        if accept:
            headers['Accept'] = accept
        if content_type:
            headers['Content-Type'] = content_type
        r = self.session.put(self.base_url + resource, json=json, auth=self.__auth, headers=headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid PUT request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 200:
            raise ValueError(f"Unable to perform PUT request. Status: {r.status_code} Response:\n" + r.text)
        return r.json()

    def put_file(self, resource, file, media_type):
        headers = {'Content-Type': media_type, **self.__default_headers}
        r = self.session.put(self.base_url + resource, data=file.read(), auth=self.__auth, headers=headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid PUT request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 201:
            raise ValueError(f"Unable to perform PUT request. Status: {r.status_code} Response:\n" + r.text)

    def delete(self, resource):
        """Generic HTTP DELETE wrapper, dealing with standard error returning a JSON body object."""
        r = self.session.delete(self.base_url + resource, auth=self.__auth, headers=self.__default_headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid DELETE request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 204:
            raise ValueError(f"Unable to perform DELETE request. Status: {r.status_code} Response:\n" + r.text)


class CumulocityApi(CumulocityRestApi):

    def __init__(self, base_url, tenant_id, username, password, tfa_token=None, application_key=None):
        super().__init__(base_url, tenant_id, username, password, tfa_token, application_key)
        self.__measurements = Measurements(self)
        self.__inventory = Inventory(self)
        self.__group_inventory = DeviceGroupInventory(self)
        self.__device_inventory = DeviceInventory(self)
        self.__identity = Identity(self)
        self.__users = Users(self)
        self.__global_roles = GlobalRoles(self)
        self.__inventory_roles = InventoryRoles(self)
        self.__applications = Applications(self)
        self.__events = Events(self)
        self.__alarms = Alarms(self)

    @property
    def measurements(self):
        return self.__measurements

    @property
    def inventory(self):
        return self.__inventory

    @property
    def group_inventory(self):
        return self.__group_inventory

    @property
    def device_inventory(self):
        return self.__device_inventory

    @property
    def identity(self):
        return self.__identity

    @property
    def users(self):
        return self.__users

    @property
    def global_roles(self):
        return self.__global_roles

    @property
    def inventory_roles(self):
        return self.__inventory_roles

    @property
    def applications(self):
        return self.__applications

    @property
    def events(self):
        return self.__events

    @property
    def alarms(self):
        return self.__alarms


class CumulocityDeviceRegistry(CumulocityRestApi):

    @dataclass
    class Credentials:
        tenant_id: str
        username: str
        password: str

    __default_instance = None

    def __init__(self, base_url, tenant_id, username, password):
        super().__init__(base_url, tenant_id, username, password)

    @classmethod
    def __build_default(cls):
        with open('c8y_api.yaml') as config_file:
            configuration = yaml.load(config_file, Loader=yaml.BaseLoader)
            base = configuration['base']
            tenant_id = configuration['devicebootstrap']['tenant_id']
            username = configuration['devicebootstrap']['username']
            password = configuration['devicebootstrap']['password']
            return CumulocityDeviceRegistry(base, tenant_id, username, password)

    @classmethod
    def default(cls):
        if not cls.__default_instance:
            cls.__default_instance = cls.__build_default()
        return cls.__default_instance

    def await_credentials(self, device_id, timeout='60m', pause='1s'):
        pause_s = CumulocityDeviceRegistry.__parse_timedelta_s(pause)
        timeout_s = CumulocityDeviceRegistry.__parse_timedelta_s(timeout)
        assert pause_s, f"Unable to parse pause string: {pause}"
        assert timeout_s, f"Unable to parse timeout string: {timeout}"
        request_json = {'id': device_id}
        request = self.prepare_request(method='post', resource='/devicecontrol/deviceCredentials', body=request_json)
        session = requests.Session()
        timeout_time = time.time() + timeout_s
        while True:
            if timeout_time < time.time():
                raise TimeoutError
            debug("Requesting device credentials for device id '%s'", device_id)
            response: requests.Response = session.send(request)
            if response.status_code == 404:
                # This is the expected response until the device registration request got accepted
                # from within Cumulocity. It will be recognized as an inbound request, though and
                # trigger status 'pending' if it was 'awaiting connection'.
                time.sleep(pause_s)
            elif response.status_code == 201:
                response_json = response.json()
                return CumulocityDeviceRegistry.Credentials(response_json['tenantId'],
                                                            response_json['username'],
                                                            response_json['password'])
            else:
                raise RuntimeError(f"Unexpected response code: {response.status_code}")

    def await_connection(self, device_id, timeout='60m', pause='1s'):
        credentials = self.await_credentials(device_id, timeout, pause)
        return CumulocityApi(self.base_url, credentials.tenant_id, credentials.username, credentials.password)

    @staticmethod
    def __parse_timedelta_s(string):
        return float(string)/1000.0 if string.endswith('ms') \
            else int(string[:-1]) if string.endswith('s') \
            else int(string[:-1])*60 if string.endswith('m') \
            else int(string[:-1])*1440 if string.endswith('h') \
            else None
