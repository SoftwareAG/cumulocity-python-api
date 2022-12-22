# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import json as json_lib
from typing import Union, Dict, BinaryIO

import collections
import requests
from requests.auth import AuthBase, HTTPBasicAuth

from c8y_api._auth import HTTPBearerAuth
from c8y_api._jwt import JWT


class CumulocityRestApi:
    """Cumulocity base REST API.

    Provides REST access to a Cumulocity instance.
    """

    MIMETYPE_JSON = 'application/json'
    HEADER_APPLICATION_KEY = 'X-Cumulocity-Application-Key'

    ACCEPT_MANAGED_OBJECT = 'application/vnd.com.nsn.cumulocity.managedobject+json'
    ACCEPT_USER = 'application/vnd.com.nsn.cumulocity.user+json'
    ACCEPT_GLOBAL_ROLE = 'application/vnd.com.nsn.cumulocity.group+json'
    CONTENT_MEASUREMENT_COLLECTION = 'application/vnd.com.nsn.cumulocity.measurementcollection+json'

    def __init__(self, base_url: str, tenant_id: str, username: str = None, password: str = None, tfa_token: str = None,
                 auth: AuthBase = None, application_key: str = None):
        """Build a CumulocityRestApi instance.

        One of `auth` or `username/password` must be provided. The TFA token
        parameter is only sensible for basic authentication.

        Args:
            base_url (str):  Cumulocity base URL, e.g. https://cumulocity.com
            tenant_id (str):  The ID of the tenant to connect to
            username (str):  Username
            password (str):  User password
            tfa_token (str):  Currently valid two factor authorization token
            auth (AuthBase):  Authentication details
            application_key (str):  Application ID to include in requests
                (for billing/metering purposes).
        """
        self.base_url = base_url.rstrip('/')
        self.tenant_id = tenant_id
        self.application_key = application_key

        if auth:
            self.auth = auth
            self.username = self._resolve_username_from_auth(auth)
        elif username and password:
            self.auth = HTTPBasicAuth(f'{tenant_id}/{username}', password)
            self.username = username
        else:
            raise ValueError("One of 'auth' or 'username/password' must be defined.")

        self.__default_headers = {}
        if tfa_token:
            self.__default_headers['tfatoken'] = tfa_token
        if self.application_key:
            self.__default_headers[self.HEADER_APPLICATION_KEY] = self.application_key
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.auth = self.auth
        s.headers = {'Accept': 'application/json'}
        if self.application_key:
            s.headers.update({self.HEADER_APPLICATION_KEY: self.application_key})
        return s

    def prepare_request(self, method: str, resource: str,
                        json: dict = None, additional_headers: Dict[str, str] = None) -> requests.PreparedRequest:
        """Prepare an HTTP request.

        Args:
            method (str):  One of 'GET', 'POST', 'PUT', 'DELETE'
            resource (str):  Path to the HTTP resource
            json (dict):  JSON body (nested dict) to send witht he request
            additional_headers (dict):  Additional non-standard headers to
                include in the request

        Returns:
            A PreparedRequest instance
        """
        hs = self.__default_headers
        if additional_headers:
            hs.update(additional_headers)
        rq = requests.Request(method=method, url=self.base_url + resource, headers=hs, auth=self.auth)
        if json:
            rq.json = json
        return rq.prepare()

    def get(self, resource: str, params: dict = None, accept: str = None, ordered: bool = False) -> dict:
        """Generic HTTP GET wrapper, dealing with standard error returning
        a JSON body object.

        Args:
            resource (str): Resource path
            params (dict): Additional request parameters
            accept (str|None): Custom Accept header to use (default is
                application/json). Specify '' to sent no Accept header.
            ordered (bool): Whether the result JSON needs to be ordered
                (default is False)

        Returns:
            The JSON response (nested dict)

        Raises:
            KeyError if the resources is not found (404)
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 200 is accepted).
        """
        additional_headers = self._prepare_headers(accept=accept)
        r = self.session.get(self.base_url + resource, params=params, headers=additional_headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid GET request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 200:
            raise ValueError(f"Unable to perform GET request. Status: {r.status_code} Response:\n" + r.text)
        if r.content:
            return r.json() if not ordered else r.json(object_pairs_hook=collections.OrderedDict)
        return {}

    def get_file(self, resource: str, params: dict = None) -> bytes:
        """Generic HTTP GET wrapper.

        Used for downloading binary data, i.e. reading binaries from Cumulocity.

        Args:
            resource (str): Resource path
            params (dict): Additional request parameters

        Returns:
            The binary data as bytes.

        Raises:
            KeyError if the resources is not found (404)
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 200 is accepted).
        """
        r = self.session.get(self.base_url + resource, params=params)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid GET request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 200:
            raise ValueError(f"Unable to perform GET request. Status: {r.status_code} Response:\n" + r.text)
        return r.content

    def post(self, resource: str, json: dict, accept: str = None, content_type: str = None) -> dict:
        """Generic HTTP POST wrapper, dealing with standard error returning
        a JSON body object.

        Args:
            resource (str): Resource path
            json (dict): JSON body (nested dict)
            accept (str|None): Custom Accept header to use (default is
                application/json). Specify '' to sent no Accept header.
            content_type (str|None): Custom Content-Type header to use
                (default is application/json)

        Returns:
             The JSON response (nested dict)

        Raises:
            KeyError if the resources is not found (404)
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 200 and 201 are accepted).
        """
        assert isinstance(json, dict)
        additional_headers = self._prepare_headers(accept=accept, content_type=content_type)
        r = self.session.post(self.base_url + resource, json=json, headers=additional_headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid POST request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code not in (200, 201):
            raise ValueError(f"Unable to perform POST request. Status: {r.status_code} Response:\n" + r.text)
        if r.content:
            return r.json()
        return {}

    def post_file(self, resource: str, file: str | BinaryIO, object: dict = None,
                  accept: str = None, content_type: str = 'application/octet-stream'):
        """Generic HTTP POST wrapper.

        Used for posting binary data, i.e. creating binary objects in Cumulocity.

        Args:
            resource (str): Resource path
            file (str|BinaryIO):  File-like object or a file path
            object (dict):  File metadata, stored within Cumulocity
            accept (str|None): Custom Accept header to use (default is
                application/json). Specify '' to sent no Accept header.
            content_type (str): Content type of the file sent
                (default is application/octet-stream)

        Returns:
             The JSON response (nested dict)

        Raises:
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 201 is accepted).
        """

        def perform_post(open_file):
            files = {'file': (None, open_file, content_type or 'application/octet-stream')}
            if object:
                files['object'] = (None, json_lib.dumps(object))
            additional_headers = self._prepare_headers(accept=accept)
            return self.session.post(self.base_url + resource, files=files, headers=additional_headers)

        if isinstance(file, str):
            with open(file, 'rb') as f:
                r = perform_post(f)
        else:
            r = perform_post(file)

        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid POST request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 201:
            raise ValueError(f"Unable to perform POST request. Status: {r.status_code} Response:\n" + r.text)
        if r.content:
            return r.json()
        return {}

    def put(self, resource: str, json: dict, params: dict = None,
            accept: str = None, content_type: str = None) -> dict:
        """Generic HTTP PUT wrapper, dealing with standard error returning
        a JSON body object.

        Args:
            resource (str): Resource path
            json (dict): JSON body (nested dict)
            params (dict): Additional request parameters
            accept (str|None): Custom Accept header to use (default is
                application/json). Specify '' to sent no Accept header.
            content_type (str|None): Custom Content-Type header to use
                (default is application/json)

        Returns:
             The JSON response (nested dict)

        Raises:
            KeyError if the resources is not found (404)
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 200 is accepted).
        """
        assert isinstance(json, dict)
        additional_headers = self._prepare_headers(accept=accept, content_type=content_type)
        r = self.session.put(self.base_url + resource, json=json, params=params, headers=additional_headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid PUT request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 200:
            raise ValueError(f"Unable to perform PUT request. Status: {r.status_code} Response:\n" + r.text)
        if r.content:
            return r.json()
        return {}

    def put_file(self, resource: str, file: str | BinaryIO,
                 accept: str = None, content_type: str = 'application/octet-stream'):
        """Generic HTTP PUT wrapper.

        Used for put'ing binary data, i.e. updating binaries in Cumulocity.

        Args:
            resource (str): Resource path
            file (str|BinaryIO):  File-like object or a file path
            accept (str|None): Custom Accept header to use (default is
                application/json). Specify '' to sent no Accept header.
            content_type (str): Content type of the file sent
                (default is application/octet-stream)

        Returns:
             The JSON response (nested dict)

        Raises:
            KeyError if the resources is not found (404)
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 201 is accepted).
        """

        def read_file_data(f):
            if isinstance(f, str):
                with open(f, 'rb') as fp:
                    return fp.read()
            return f.read()

        # for some reason, the content-type header needs to be set, so
        # this is a reasonable default
        if not content_type:
            content_type = 'application/octet-stream'
        additional_headers = self._prepare_headers(accept=accept, content_type=content_type)
        data = read_file_data(file)
        r = self.session.put(self.base_url + resource, data=data, headers=additional_headers)
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid PUT request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code != 201:
            raise ValueError(f"Unable to perform PUT request. Status: {r.status_code} Response:\n" + r.text)
        if r.content:
            return r.json()
        return {}

    def delete(self, resource: str, json: dict = None, params: dict = None):
        """Generic HTTP POST wrapper, dealing with standard error returning
        a JSON body object.

        Args:
            resource (str): Resource path
            json (dict): JSON body (nested dict)
            params (dict): Additional request parameters

        Returns:
             The JSON response (nested dict)

        Raises:
            KeyError if the resources is not found (404)
            SyntaxError if the request cannot be processes (5xx)
            ValueError if the response is not ok for other reasons
                (only 200 and 204 are accepted).
        """
        if json:
            assert isinstance(json, dict)
        r = self.session.delete(self.base_url + resource, json=json, params=params, headers={'Accept': None})
        if r.status_code == 404:
            raise KeyError(f"No such object: {resource}")
        if 500 <= r.status_code <= 599:
            raise SyntaxError(f"Invalid DELETE request. Status: {r.status_code} Response:\n" + r.text)
        if r.status_code not in (200, 204):
            raise ValueError(f"Unable to perform DELETE request. Status: {r.status_code} Response:\n" + r.text)

    @classmethod
    def _resolve_username_from_auth(cls, auth: AuthBase):
        """Resolve the username from the authentication information.

        For Basic authentication the username will be simply read from the
        provided data, for Bearer authentication the token will be parsed
        and the username resolved from the payload.
        """
        if isinstance(auth, HTTPBasicAuth):
            return auth.username
        if isinstance(auth, HTTPBearerAuth):
            return JWT(auth.token).username
        raise ValueError(f"Unexpected AuthBase instance: {auth.__class__}. Unable to resolve username.")

    @classmethod
    def _prepare_headers(cls, **kwargs) -> Union[dict, None]:
        """Format a set of named arguments into a header dictionary.

        This will format the argument name into Header-Case (from snake_case).

        Args:
            kwargs: A list of named header values, each can be None or ''

        Returns:
            dict: A properly formatted header dictionary for use with requests
                '' values will be returned as `None`
            None: If not of the arguments have an actual value
        """
        if all(v is None for v in kwargs.values()):
            return None

        def format_value(value):
            return None if value == '' else value

        return {cls._format_header_key(key): format_value(value) for key, value in kwargs.items() if value is not None}

    @staticmethod
    def _format_header_key(key: str) -> str:
        """Format a snake_case argument name into a proper Header-Name.

        Args:
            key (str):  A snake_case key

        Returns:
            The provided key in Header-Case
        """
        # split by '_', uppercase the first character, lowercase the rest and join with '-'
        return '-'.join([part[0].upper() + part[1:].lower() for part in key.split('_')])
