"""
Test Fetcher module functionality that was not tested anywhere else
"""
from datetime import timedelta

from django.utils import timezone
from testfixtures import LogCapture

from labsterutils.date_time import datetime_to_float
from test_case import StandaloneAppTestCase


class FetcherTest(StandaloneAppTestCase):
    """
    Test Fetcher module functionality that was not tested anywhere else
    """

    def test_expires_in_the_past_ignored(self):
        """
        If the extracted `expires` is already in the past when parsing new token,
        assume this is a mistake and return `None`. This will make the client attempt
        the communication anyway, ignoring theoretically expired token.
        `Expires` field is not guaranteed on the token, so we use best effort approach.
        E.g. token obtained with JWT flow never contains expiry information.
        """
        from oauth2_client.fetcher import expires_or_none
        raw_token = {
            'expires_at': datetime_to_float(timezone.now() - timedelta(hours=40))
        }
        expires_actual = expires_or_none(raw_token)
        self.assertEqual(expires_actual, None)

    def test_raw_token_parsing_error(self):
        """
        When provider returns unparsable data (probably auth error), make 
        sure we show an informative error message.
        """
        from oauth2_client.tests.factories import ApplicationFactory
        from oauth2_client.fetcher import Fetcher
        app = ApplicationFactory()
        fetcher = Fetcher(app)
        with LogCapture() as logs:
            with self.assertRaises(KeyError):
                fetcher.access_token_from_raw_token({})
        self.assertIn("Error when parsing an access token", str(logs))
