"""
Test cases for model-related functionality, that didn't fit anywhere else.
"""
from datetime import datetime, timedelta

import pytz

from oauth2_client.tests.test_compat import patch
from test_case import StandaloneAppTestCase


class TestModel(StandaloneAppTestCase):
    """
    Test cases for model-related functionality, that didn't fit anywhere else.
    """

    def test_token_to_dict(self):
        """
        Ensure AccessToken object gets transformed to a dict as expected by
        the `OAuth2Client`
        """
        from .ide_test_compat import AccessTokenFactory, ApplicationFactory

        now = datetime(1970, 1, 1, 0, 0, tzinfo=pytz.UTC)
        expiration_dt = now + timedelta(hours=1)  # expires 1h into epoch for easy testing
        token = AccessTokenFactory(
            token="this-is-token",
            token_type="bearer",
            expires=expiration_dt,
            scope='read write',
            application=ApplicationFactory()
        )
        with patch('oauth2_client.models.timezone.now', return_value=now):
            actual = token.to_client_dict()
            expected = {
                'expires_in': 3600,
                'access_token': 'this-is-token',
                'token_type': 'bearer',
                'scope': 'read write'
            }
            self.assertEqual(actual, expected)
