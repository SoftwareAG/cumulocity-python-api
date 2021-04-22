import pytest
from unittest.mock import Mock, patch, PropertyMock, MagicMock

from c8y_api.app import CumulocityApi


@patch('os.environ')
def test_application_key_header(env):
    # to test the behaviour we quickly implement a 404 response
    # that way we don't have to worry about a proper response
    response_mock = MagicMock()
    type(response_mock).status_code = PropertyMock(return_value=404)
    assert response_mock.status_code == 404

    # (1) testing without application key
    c8y_1 = CumulocityApi()
    c8y_1.session.get = Mock(return_value=response_mock)

    with pytest.raises(KeyError):
        c8y_1.inventory.get('id')

    call_args = c8y_1.session.get.call_args
    assert 'headers' in call_args.kwargs
    assert call_args.kwargs['headers'] == {}

    # (2) testing with application key
    c8y_2 = CumulocityApi(application_key='application_key')
    c8y_2.session.get = Mock(return_value=response_mock)

    with pytest.raises(KeyError):
        c8y_2.inventory.get('id')

    call_args = c8y_2.session.get.call_args
    assert 'headers' in call_args.kwargs
    assert call_args.kwargs['headers'] == {'X-Cumulocity-Application-Key': 'application_key'}
