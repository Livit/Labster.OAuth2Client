"""
Test Fetcher module functionality that was not tested anywhere else
"""
from datetime import timedelta

import six
from ddt import data, ddt
from django.utils import timezone
from testfixtures import LogCapture

from oauth2_client.fetcher import Fetcher, expiry_date
from tests.factories import ApplicationFactory
from tests.test_compat import patch
from oauth2_client.utils.date_time import datetime_to_float
from test_case import StandaloneAppTestCase


class TestToken:
    """
    Dummy token class for scope testing.
    """
    def __init__(self, scope):
        self.scope = scope


@ddt
class FetcherTest(StandaloneAppTestCase):
    """
    Test Fetcher module functionality that was not tested anywhere else
    """

    def test_expires_in_the_past_raises(self):
        """
        Ensure `expires` timestamp (on the token) in the past raises an exception.
        This means either parsing issues on our side, or auth provider gone insane.
        """
        raw_token = {'expires_at': datetime_to_float(timezone.now() - timedelta(hours=40))}
        expected_msg = "This means either parsing issue on our side or auth provider gone insane"
        with six.assertRaisesRegex(self, ValueError, expected_msg):
            expiry_date(raw_token)

    def test_raw_token_parsing_error(self):
        """
        When provider returns unparseable data (probably auth error), make
        sure we show an informative error message.
        """
        fetcher = Fetcher(ApplicationFactory())
        with LogCapture() as logs:
            with self.assertRaises(KeyError):
                fetcher.access_token_from_raw_token({})
        self.assertIn("has changed specification", str(logs))

    @data(TestToken("read write"), {"scope": "read write"})
    @patch.object(Fetcher, 'requested_scope')
    def test_different_scope_granted_object(self, token, mock_requested_scope):
        """
        Provider granted different scope than we requested.
        Received the token as either object or a dict.
        Ensure received scope is parsed properly and an useful warning is printed.
        """
        mock_requested_scope.return_value = ["read"]
        fetcher = Fetcher(ApplicationFactory())
        with LogCapture() as logs:
            received_scope = fetcher.received_scope(token)
            self.assertEqual(received_scope, "read write")
            self.assertIn(
                "Received different scope than requested. Requested: ['read'], received: ['read', 'write'].", str(logs)
            )
