# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import pytest
from requests import request


@pytest.fixture(scope='function')
def random_name() -> str:
    """Provide a random name."""
    return RandomNameGenerator.random_name()


class RandomNameGenerator:
    """Provides randomly generated names using a public service."""

    names_cache = []
    names_index = -1

    @classmethod
    def random_name(cls) -> str:
        """Provide a random name."""
        if not cls.names_cache or cls.names_index >= len(cls.names_cache):
            response = request('get', 'http://names.drycodes.com/10',
                               params={'combine': 3, 'case': 'lower'},
                               headers={'Accept': 'application/json'})
            if 200 <= response.status_code <= 299:
                cls.names_cache = response.json()
                cls.names_index = 0
            else:
                raise RuntimeError('Unable to generate random names. Unexpected response from web site: '
                                   f'HTTP {response.status_code} {response.text}')
        cls.names_index = cls.names_index + 1
        return cls.names_cache[cls.names_index-1]
