"""
Client tests.

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
"""
from datetime import timedelta

import requests_mock
import six
from ddt import data, ddt
from django.utils import timezone
from pybreaker import CircuitBreakerError

from test_case import StandaloneAppTestCase
from .test_compat import patch


@ddt
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

        tested_client = get_client(app.name)
        self.assertIsNotNone(tested_client)
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
        tested_client = get_client(app.name)
        self.assertIsNotNone(tested_client)
        # ensure client uses new token now
        self.assertEqual(access_token.token, tested_client.token['access_token'])
        fetch_token_mock.assert_not_called()
        self.assertFalse(
            AccessToken.objects.filter(application=app)  # pylint: disable=maybe-no-member
            .exclude(id=access_token.id).exists()
        )

    @patch('oauth2_client.client.fetch_token')
    @requests_mock.Mocker()
    def test_client_returns_data(self, fetch_token_mock, mock_response):
        """
        Given a valid token, ensure the client returns data
        """
        from oauth2_client.client import get_client
        from .factories import AccessTokenFactory, ApplicationFactory
        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        access_token = AccessTokenFactory(
            application=app,
        )
        fetch_token_mock.return_value = access_token
        mock_response.get(api_url, status_code=200, text='hello world!')
        tested_client = get_client(app.name)
        response = tested_client.get(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'hello world!')

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

        tested_client = get_client(app.name)
        self.assertIsNotNone(tested_client)
        # ensure client uses new token now
        self.assertEqual(new_token.token, tested_client.token['access_token'])
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

        tested_client = get_client(app.name)
        self.assertEqual(tested_client.token['access_token'], access_token)

        access_tokens = AccessToken.objects.filter(application=app)
        self.assertEqual(1, access_tokens.count())
        fetch_token_mock.assert_not_called()

    @patch('oauth2_client.client.fetch_and_store_token')
    @requests_mock.Mocker()
    @data(401, 403)
    def test_expired_token_refetched(self, bad_code, mock_fetch_token, mock_response):
        """
        Token expiry detection gets triggered by a bad status code.
        Ensure token refetch is attempted. 401 is a common way to convey token
        expiry. 403 is what `oauth2_provider` seems to be using.
        More about codes: https://stackoverflow.com/questions/30826726/how-to-identify-if-the-oauth-token-has-expired
        """
        from oauth2_client.tests.factories import AccessTokenFactory, ApplicationFactory
        from oauth2_client.client import OAuth2Client

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(
            application=app
        )
        mock_fetch_token.return_value = token
        tested_client = OAuth2Client(token)
        # MOCK: first response is bad, next token is refetched, second response is 200 OK
        mock_response.get(api_url, [{'status_code': bad_code}, {'status_code': 200}])
        tested_client.get(api_url)
        mock_fetch_token.assert_called_once_with(app)

    @patch('oauth2_client.client.fetch_and_store_token')
    @requests_mock.Mocker()
    def test_expired_tokens_break_circuit(self, mock_fetch_token, mock_response):
        """
        Circuit breaker opens when two 4xx codes received in a row. 4xx status code
        is used as one of the ways of detecting token expiry.
        """
        from oauth2_client.client import OAuth2Client
        from oauth2_client.tests.factories import AccessTokenFactory, ApplicationFactory

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(
            application=app,
        )
        mock_fetch_token.return_value = token
        tested_client = OAuth2Client(token)
        # MOCK: first response is 403 forbidden, next token is successfully refetched,
        # but second response is 403 forbidden too. Circuit opens.
        mock_response.get(api_url, [{'status_code': 403}, {'status_code': 403}])
        with six.assertRaisesRegex(self, CircuitBreakerError, "Failures threshold reached"):
            tested_client.get(api_url)
        mock_fetch_token.assert_called_once_with(app)
