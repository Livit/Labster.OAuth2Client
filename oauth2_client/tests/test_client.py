"""
Client tests.
"""
import time

from django.test import TestCase
from django.utils import timezone

from oauth2_client.client import get_client, TIMEOUT_SECONDS
from oauth2_client.models import AccessToken
from .compat import patch
from .factories import AccessTokenFactory, ApplicationFactory


class CreateAccessTokenTest(TestCase):
    """
    Ouath2 client test cases.
    """

    @patch('oauth2_client.client._get_token')
    def test_no_token(self, get_token_mock):
        """
        Ensure new token is created if there is no token.
        """
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
