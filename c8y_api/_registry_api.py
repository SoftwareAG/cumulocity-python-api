# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from dataclasses import dataclass
import requests
import time
import yaml

from c8y_api._base_api import CumulocityRestApi
from c8y_api._main_api import CumulocityApi
from c8y_api._util import debug


# noinspection SpellCheckingInspection
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
