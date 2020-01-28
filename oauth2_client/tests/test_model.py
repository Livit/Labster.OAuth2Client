"""
Test cases for model-related functionality, that didn't fit anywhere else.

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
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
        from oauth2_client.tests.factories import AccessTokenFactory, ApplicationFactory
        now = datetime(1970, 1, 1, 0, 0, tzinfo=pytz.UTC)
        expiration_dt = now + timedelta(hours=1)  # expires 1h into epoch for easy testing
        app = ApplicationFactory()
        token = AccessTokenFactory(
            token="this-is-token",
            token_type="bearer",
            expires=expiration_dt,
            scope='read write',
            application=app
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
