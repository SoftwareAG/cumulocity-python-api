import os
import pytest

import logging
from dotenv import load_dotenv

from c8y_api.app import CumulocityApi


@pytest.fixture(scope='session')
def logger():
    """Provide a logger for testing."""
    return logging.getLogger(__name__ + '.test')


@pytest.fixture(scope='session')
def test_environment(logger):
    """Prepare the environment, i.e. read a .env file if found."""
    # check if there is a .env file
    if os.path.exists('.env'):
        logger.info("Environment file (.env) exists and will be considered.")
        # check if any C8Y_ variable is already defined
        predefined_keys = [key for key in os.environ.keys() if 'C8Y_' in key]
        if predefined_keys:
            logger.fatal("The following environment variables are already defined and may be overridden: "
                         + ', '.join(predefined_keys))
        load_dotenv()
    # list C8Y_* keys
    defined_keys = [key for key in os.environ.keys() if 'C8Y_' in key]
    logger.info(f"Found the following keys: {', '.join(defined_keys)}.")


@pytest.fixture(scope='session')
def live_c8y(test_environment) -> CumulocityApi:
    """Provide a live CumulocityApi instance as defined by the environment."""
    if 'C8Y_BASEURL' not in os.environ.keys():
        raise RuntimeError("Missing Cumulocity environment variables (C8Y_*). Cannot create CumulocityApi instance. "
                           "Please define the required variables directly or setup a .env file.")
    return CumulocityApi()


@pytest.fixture(scope='function')
def factory(logger, live_c8y: CumulocityApi):
    """Provides a generic object factory function which ensures that created
    objects are removed after testing."""

    created = []

    def factory_fun(obj):
        o = obj.create()
        logger.info(f'Created object #{o.id}, ({o.__class__.__name__})')
        created.append(o)
        return o

    yield factory_fun

    for u in created:
        u.delete()
