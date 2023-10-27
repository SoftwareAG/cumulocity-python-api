# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from dataclasses import dataclass
import logging
import requests
import time
import yaml

from c8y_api._base_api import CumulocityRestApi
from c8y_api._main_api import CumulocityApi


class CumulocityDeviceRegistry(CumulocityRestApi):
    """Special CumulocityRESTAPI instance handling device registration.

    https://cumulocity.com/guides/users-guide/device-management/#connecting-devices
    """

    __log = logging.getLogger(__name__ + '.CumulocityDeviceRegistry')

    @dataclass
    class Credentials:
        """Bundles authentication information."""
        tenant_id: str
        username: str
        password: str

    _default_instance = None

    def __init__(self, base_url, tenant_id, username, password):
        super().__init__(base_url, tenant_id, username, password)

    @classmethod
    def _build_default(cls):
        with open('c8y_api.yaml', encoding='utf-8', mode='r') as config_file:
            configuration = yaml.load(config_file, Loader=yaml.BaseLoader)
            base = configuration['base']
            tenant_id = configuration['devicebootstrap']['tenant_id']
            username = configuration['devicebootstrap']['username']
            password = configuration['devicebootstrap']['password']
            return CumulocityDeviceRegistry(base, tenant_id, username, password)

    @classmethod
    def default(cls):
        """Return the default (bootstrap) instance."""
        if not cls._default_instance:
            cls._default_instance = cls._build_default()
        return cls._default_instance

    def await_credentials(self, device_id: str, timeout: str = '60m', pause: str = '1s') -> Credentials:
        """Wait for device credentials.

        The device must have requested credentials already. This function
        awaits the request confirmation and returns the device-specific
        credentials generated by the Cumulocity platform.

        Args:
            device_id (str):  The external ID of the device
                (i.e. IMEI - NOT the Cumulocity ID)
            timeout (str):  How long to wait for the request to be confirmed.
                This is a formatted string in the form <int><unit>, accepted
                units are 'h' (hours), 'm' (minutes), 's' (seconds) and
                'ms' (milliseconds).
                A reasonable value for this depends on application.
            pause (str):  How long to pause between request confirmation checks
                This is a formmated string, see `timeout` parameter.

        Returns:
            Credentials object holding the device credentials

        Raises:
            TimeoutError:  if the request was not confirmed in time.

        See also: https://cumulocity.com/guides/users-guide/device-management/#connecting-devices
        """
        pause_s = CumulocityDeviceRegistry.__parse_timedelta_s(pause)
        timeout_s = CumulocityDeviceRegistry.__parse_timedelta_s(timeout)
        assert pause_s, f"Unable to parse pause string: {pause}"
        assert timeout_s, f"Unable to parse timeout string: {timeout}"
        request_json = {'id': device_id}
        request = self.prepare_request(method='post', resource='/devicecontrol/deviceCredentials', json=request_json)
        session = requests.Session()
        timeout_time = time.time() + timeout_s
        while True:
            if timeout_time < time.time():
                raise TimeoutError
            self.__log.debug("Requesting device credentials for device id '{}' ...", device_id)
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

    def await_connection(self, device_id: str, timeout: str = '60m', pause: str = '1s') -> CumulocityApi:
        """Wait for device credentials and build corresponding API connection.

        The device must have requested credentials already. This function
        awaits the request confirmation and returns a CumulocityAPI instance
        for the device-specific credentials.

        Args:
            device_id (str):  The external ID of the device
                (i.e. IMEI - NOT the Cumulocity ID)
            timeout (str):  How long to wait for the request to be confirmed.
                This is a formatted string in the form <int><unit>, accepted
                units are 'h' (hours), 'm' (minutes), 's' (seconds) and
                'ms' (milliseconds).
                A reasonable value for this depends on application.
            pause (str):  How long to pause between request confirmation checks
                This is a formmated string, see `timeout` parameter.

        Returns:
            Device-specific CumulocityAPI instance

        Raises:
            TimeoutError:  if the request was not confirmed in time.

        See also: https://cumulocity.com/guides/users-guide/device-management/#connecting-devices
        """
        credentials = self.await_credentials(device_id, timeout, pause)
        return CumulocityApi(self.base_url, credentials.tenant_id, credentials.username, credentials.password)

    @staticmethod
    def __parse_timedelta_s(string):
        return float(string)/1000.0 if string.endswith('ms') \
            else int(string[:-1]) if string.endswith('s') \
            else int(string[:-1])*60 if string.endswith('m') \
            else int(string[:-1])*1440 if string.endswith('h') \
            else None
