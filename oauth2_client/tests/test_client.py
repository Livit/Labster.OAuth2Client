"""
Client tests.
"""
import time

from django.utils import timezone

from test_case import StandaloneAppTestCase
from .test_compat import patch


class CreateAccessTokenTest(StandaloneAppTestCase):
    """
    Ouath2 client test cases.
    Local imports of model-related files are required for in-IDE test runs.
    Otherwise an import will be attempted before django.setup() call and
    an exception is thrown.
    """

    @patch('oauth2_client.client._get_token')
    def test_no_token(self, get_token_mock):
        """
        Ensure new token is created if there is no token.
        """
        from oauth2_client.models import AccessToken
        from oauth2_client.client import get_client
        from .factories import ApplicationFactory

        app = ApplicationFactory()
        token = {'access_token': 'my_token', 'expires_at': time.time()}
        get_token_mock.return_value = token

        client = get_client(app.name)
        self.assertIsNotNone(client)
        access_token = AccessToken.objects.get(application=app)
        self.assertEqual(token, access_token.token)
        get_token_mock.assert_called_once_with(app)

    @patch('oauth2_client.client._get_token')
    def test_token_exists(self, get_token_mock):
        """
        Ensure no token is created if there is no expired one.
        """
        from oauth2_client.models import AccessToken
        from oauth2_client.client import get_client, TIMEOUT_SECONDS
        from .factories import AccessTokenFactory, ApplicationFactory

        app = ApplicationFactory()
        token = {'access_token': 'my_token', 'expires_at': time.time() + TIMEOUT_SECONDS + 1}
        access_token = AccessTokenFactory(token=token, application=app)

        client = get_client(app.name)
        self.assertIsNotNone(client)
        get_token_mock.assert_not_called()
        self.assertFalse(AccessToken.objects.filter(application=app).exclude(id=access_token.id).exists())

    @patch('oauth2_client.client._get_token')
    def test_token_expired(self, get_token_mock):
        """
        Ensure new token is created if there is expired one.
        """
        from oauth2_client.models import AccessToken
        from oauth2_client.client import get_client
        from .factories import ApplicationFactory, AccessTokenFactory
        from oauth2_client.client import TIMEOUT_SECONDS

        app = ApplicationFactory()
        curr_token = {'access_token': 'curr_token', 'expires_at': time.time() + TIMEOUT_SECONDS - 1}
        AccessTokenFactory(
            token=curr_token,
            application=app,
            created_at=timezone.now() - timezone.timedelta(seconds=30)
        )

        new_token = {'access_token': 'new_token', 'expires_at': time.time()}
        get_token_mock.return_value = new_token

        client = get_client(app.name)
        self.assertIsNotNone(client)
        access_tokens = AccessToken.objects.filter(application=app)
        self.assertEqual(2, access_tokens.count())
        get_token_mock.assert_called_once_with(app)

        self.assertEqual(new_token, access_tokens.order_by('-created_at').first().token)
