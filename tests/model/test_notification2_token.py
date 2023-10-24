from unittest.mock import Mock
from c8y_api.model.notification2 import Tokens
from util.testing_util import RandomNameGenerator

def test_uri_generator():
    """Verify that parsing a Tenant Option from JSON works."""

    token = RandomNameGenerator.random_name()
    consumer = RandomNameGenerator.random_name()
    c8y = Mock()
    c8y.base_url = "https://test.eu-latest.cumulocity.com/"
    c8y.is_tls = True
    token = Tokens(c8y)
    tsl_uri = token.build_websocket_uri(token)
    tsl_uri_w_consumer = token.build_websocket_uri(token,consumer)
    c8y.is_tls = False
    uri = token.build_websocket_uri(token)
    uri_w_consumer = token.build_websocket_uri(token,consumer)

    assert (tsl_uri == f'wss://test.eu-latest.cumulocity.com/notification2/consumer/?token={token}')
    assert (tsl_uri_w_consumer == f'wss://test.eu-latest.cumulocity.com/notification2/consumer/?token={token}&consumer={consumer}')
    assert (uri == f'ws://test.eu-latest.cumulocity.com/notification2/consumer/?token={token}')
    assert (uri_w_consumer == f'ws://test.eu-latest.cumulocity.com/notification2/consumer/?token={token}&consumer={consumer}')