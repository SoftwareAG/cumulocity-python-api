import os
import pytest

import logging
from requests import request
from dotenv import load_dotenv

from c8y_api.app import CumulocityApi


@pytest.fixture(scope='session')
def logger():
    return logging.getLogger(__name__ + '.test')


@pytest.fixture(scope='session')
def live_c8y(logger):
    # check if there is a .env file
    if os.path.exists('.env'):
        logger.info("Environment file (.env) exists and will be considered.")
        # check if any C8Y_ variable is already defined
        predefined_keys = [key for key in os.environ.keys() if 'C8Y_' in key]
        if predefined_keys:
            logger.fatal("The following environment variables are already defined and may be overridden: "
                         + ', '.join(predefined_keys))
        load_dotenv()
    if 'C8Y_BASEURL' not in os.environ.keys():
        raise RuntimeError("Missing Cumulocity environment variables (C8Y_*). Cannot create CumulocityApi instance. "
                           "Please define the required variables directly or setup a .env file.")
    return CumulocityApi()


class RandomNameGenerator:

    names_cache = []
    names_index = -1

    @classmethod
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
