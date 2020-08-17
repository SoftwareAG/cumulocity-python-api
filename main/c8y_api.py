import requests
import collections
import time
import yaml
from dataclasses import dataclass

from log_util import error, debug
from c8y_model import Inventory, Measurements


class CumulocityRestApi:

    def __init__(self, base_url, tenant_id, username, password, tfa_token=None):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.username = username
        self.password = password
        self.tfa_token = tfa_token
        self.__auth = f'{tenant_id}/{username}', password
        self.__default_headers = {'tfatoken': self.tfa_token} if self.tfa_token else {}

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


class CumulocityApi(CumulocityRestApi):

    def __init__(self, base_url, tenant_id, username, password, tfa_token=None):
        super().__init__(base_url, tenant_id, username, password, tfa_token)
        self.__measurements = Measurements(self)  # todo: lazy?
        self.__inventory = Inventory(self)  # todo: lazy?

    @property
    def measurements(self):
        return self.__measurements

    @property
    def inventory(self):
        return self.__inventory


class CumulocityDeviceRegistry(CumulocityRestApi):

    @dataclass
    class Credentials:
        tenant_id: str
        username: str
        password: str

    __default_instance = None

    def __init__(self, base_url, tenant_id, username, password):
        super().__init__(base_url, tenant_id, username, password)
        self.__measurements = Measurements(self)  # todo: lazy?
        self.__inventory = Inventory(self)  # todo: lazy?

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
