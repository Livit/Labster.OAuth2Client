"""
Client tests.

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
"""
from datetime import timedelta

import requests_mock
import six
from django.utils import timezone
from oauthlib.oauth2 import TokenExpiredError

from test_case import StandaloneAppTestCase
from .test_compat import Mock, patch


class ClientTest(StandaloneAppTestCase):
    """
    OAuth2 client test cases.
    """

    @patch('oauth2_client.client.fetch_token')
    def test_no_token(self, fetch_token_mock):
        """
        Ensure new token is created if there is no token.
        """
        from oauth2_client.client import get_client
        from oauth2_client.models import AccessToken
        from .factories import ApplicationFactory, fake_token

        now = timezone.now()
        app = ApplicationFactory()
        # we don't want this one stored in DB, so no Factory Boy here
        token_from_provider = AccessToken(
            application=app,
            token=fake_token(),
            expires=now + timedelta(seconds=AccessToken.TIMEOUT_SECONDS + 10),
            created=now,
        )
        fetch_token_mock.return_value = token_from_provider

        client = get_client(app.name)
        self.assertIsNotNone(client)
        token_from_db = AccessToken.objects.get(application=app)
        self.assertEqual(token_from_provider.token, token_from_db.token)
        self.assertEqual(
            token_from_provider.expires,
            token_from_db.expires
        )
        fetch_token_mock.assert_called_once_with(app)

    @patch('oauth2_client.client.fetch_token')
    def test_token_exists(self, fetch_token_mock):
        """
        Ensure no token is fetched if there is a valid one.
        """
        from oauth2_client.models import AccessToken
        from oauth2_client.client import get_client
        from .factories import AccessTokenFactory, ApplicationFactory, fake_token

        now = timezone.now()
        app = ApplicationFactory()
        access_token = AccessTokenFactory(
            application=app,
            token=fake_token(),
            expires=now + timedelta(seconds=AccessToken.TIMEOUT_SECONDS + 10),
            created=now,
        )
        client = get_client(app.name)
        self.assertIsNotNone(client)
        # ensure client uses new token now
        self.assertEqual(access_token.token, client.token['access_token'])
        fetch_token_mock.assert_not_called()
        self.assertFalse(AccessToken.objects.filter(application=app).exclude(id=access_token.id).exists())

    @patch('oauth2_client.client.fetch_token')
    def test_token_expired(self, fetch_token_mock):
        """
        Ensure new token is fetched if the current one is expired
        """
        from oauth2_client.client import get_client
        from oauth2_client.models import AccessToken
        from .factories import ApplicationFactory, AccessTokenFactory

        now = timezone.now()
        app = ApplicationFactory()
        # expired token from the past
        AccessTokenFactory(
            application=app,
            token='expired_token',
            expires=now + timedelta(seconds=AccessToken.TIMEOUT_SECONDS - 1),
            created=now - timezone.timedelta(seconds=30),
        )

        # we don't want this one stored in DB, so no Factory Boy here
        # a valid token created now
        new_token = AccessToken(
            application=app,
            token='valid_token',
            expires=now + timedelta(seconds=AccessToken.TIMEOUT_SECONDS + 10),
            created=now,
        )
        fetch_token_mock.return_value = new_token

        client = get_client(app.name)
        self.assertIsNotNone(client)
        # ensure client uses new token now
        self.assertEqual(new_token.token, client.token['access_token'])
        access_tokens = AccessToken.objects.filter(application=app)
        self.assertEqual(2, access_tokens.count())
        fetch_token_mock.assert_called_once_with(app)

    @patch('oauth2_client.client.fetch_token')
    def test_token_no_expires_field(self, fetch_token_mock):
        """
        A token has no `expires` datetime set.
        Expiration info is not mandated by the RFC, also Salesforce does not return this information.
        Make sure the token is attempted for use by the client.
        """
        from oauth2_client.models import AccessToken
        from oauth2_client.client import get_client
        from .factories import ApplicationFactory, AccessTokenFactory

        access_token = 'curr_token'
        app = ApplicationFactory()
        AccessTokenFactory(
            token=access_token,
            application=app,
        )

        client = get_client(app.name)
        self.assertEqual(client.token['access_token'], access_token)

        access_tokens = AccessToken.objects.filter(application=app)
        self.assertEqual(1, access_tokens.count())
        fetch_token_mock.assert_not_called()

    @requests_mock.Mocker()
    def test_token_expires_in_client_no_callback(self, mocked_request):
        """
        If the client encounters TokenExpiredError when handling a request and
        there is no callback registered, make sure the exception is re-raised.
        """
        from oauth2_client.tests.factories import AccessTokenFactory, ApplicationFactory
        from oauth2_client.client import OAuth2Client

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(
            application=app
        )

        c = OAuth2Client(token)
        mocked_request.get(api_url, status_code=403)
        with self.assertRaises(TokenExpiredError):
            c.get(api_url)

    @requests_mock.Mocker()
    def test_token_expires_in_client_callback_is_present(self, mocked_request):
        """
        If the client encounters TokenExpiredError when handling a request and the
        `expired_callback` is specified, make sure the client tries to fetch new token
        """
        from oauth2_client.tests.factories import AccessTokenFactory, ApplicationFactory
        from oauth2_client.client import OAuth2Client

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(
            application=app
        )

        expired_callback = Mock(return_value=token)
        c = OAuth2Client(token, expired_callback=expired_callback)
        # MOCK: first response is 403 Forbidden, next expired_callback is called, second response is 200 OK
        mocked_request.get(api_url, [{'status_code': 403}, {'status_code': 200}])
        c.get(api_url)
        expired_callback.assert_called_once_with(app)

    @requests_mock.Mocker()
    def test_token_expired_callback_safety_fuse(self, mocked_request):
        """
        If `expired_callback` is called twice within 10s period, that means
        something is wrong and we raise an exception.
        """
        from oauth2_client.client import OAuth2Client
        from oauth2_client.tests.factories import AccessTokenFactory, ApplicationFactory

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(
            application=app,
        )

        expired_callback = Mock(return_value=token)
        c = OAuth2Client(token, expired_callback=expired_callback)
        # MOCK: first response is forbidden, next expired_callback is called, second response is
        # forbidden too
        mocked_request.get(api_url, [{'status_code': 403}, {'status_code': 403}])
        with six.assertRaisesRegex(self, TokenExpiredError, "More than one token re-fetch"):
            c.get(api_url)
        expired_callback.assert_called_once_with(app)
