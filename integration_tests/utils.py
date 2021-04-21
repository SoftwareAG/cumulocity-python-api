import pytest

from c8y_api.app import CumulocityApi


@pytest.fixture
def c8y():
    return CumulocityApi()
