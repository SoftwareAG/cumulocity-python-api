import os
import pytest

from requests import request

from c8y_api.app import CumulocityApi


@pytest.fixture
def c8y():
    if 'C8Y_BASEURL' not in os.environ.keys():
        raise RuntimeError('Missing Cumulocity environment variables (C8Y_*). Cannot create CumulocityApi instance.')
    return CumulocityApi()


class RandomNameGenerator:

    names_cache = []
    names_index = -1

    @classmethod
    @pytest.fixture
    def random_name(cls):
        if not cls.names_cache or cls.names_index >= len(cls.names_cache):
            response = request('get', 'http://names.drycodes.com/10',
                               params={'combine': 3, 'case': 'lower'},
                               headers={'Accept': 'application/json'})
            if 200 <= response.status_code <= 299:
                names_cache = response.json()
                names_index = 0
            else:
                raise RuntimeError('Unable to generate random names. Unexpected response from web site: '
                                   f'HTTP {response.status_code} {response.text}')
        names_index = names_index + 1
        return f'c8yapi_{names_cache[names_index-1]}'
