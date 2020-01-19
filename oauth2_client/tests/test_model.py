"""
Test cases the model-related functionality, that didn't fit anywhere else.
"""
from datetime import datetime, timedelta

import pytz

from labsterutils.date_time import datetime_to_float
from oauth2_client.tests.test_compat import patch
from test_case import StandaloneAppTestCase


class TestModel(StandaloneAppTestCase):
    """
    Test cases the model-related functionality, that didn't fit anywhere else.
    """

    def test_mobile_auth_adapter(self):
        """
        Test simple property remapping in the MobileApplication adapter class
        """
        from oauth2_client.tests.factories import ApplicationFactory
        from oauth2_client.models import MobileApplicationAdapter

        app = ApplicationFactory(name="test_name", client_id="test_id", client_secret="test_secret")
        actual = MobileApplicationAdapter(app)
        self.assertEqual(actual.name, "test_name")
        self.assertEqual(actual.key, "test_id")
        self.assertEqual(actual.secret, "test_secret")

    def test_token_to_dict(self):
        """
        Ensure AccessToken object gets transformed to a dict as expected by the `OAuth2Client`
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
                'expires_at': int(datetime_to_float(datetime(1970, 1, 1, 1, 0, 0))),
                'expires_in': 3600,
                'access_token': 'this-is-token',
                'token_type': 'bearer',
                'scope': 'read write'
            }
            self.assertEqual(actual, expected)
