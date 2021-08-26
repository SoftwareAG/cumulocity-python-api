import os
import pytest

import logging
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
