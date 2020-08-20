"""
Client tests.
"""
from datetime import timedelta

import requests_mock
import six
from django.utils import timezone
from pybreaker import CircuitBreakerError

from test_case import StandaloneAppTestCase
from .test_compat import patch


#
# Response used by Salesforce to indicate invalid JWT grant
# https://help.salesforce.com/articleView?id=remoteaccess_oauth_flow_errors.htm
#
JWT_INVALID_RESP = {
    'status_code': 400,
    'headers': {'content-type': 'application/json'},
    'json': {"error": "invalid_grant", "error_description": "This is not important"},
}


class ClientTest(StandaloneAppTestCase):
    """
    OAuth2 client test cases.
    """

    def setUp(self):
        super(ClientTest, self).setUp()
        # ensure the circuit breaker is closed before running a test
        from oauth2_client.client import request_breaker
        request_breaker.close()

    @patch('oauth2_client.client.fetch_token')
    def test_no_token(self, fetch_token_mock):
        """
        Ensure new token is created if there is no token.
        """
        from .ide_test_compat import ApplicationFactory, AccessToken, fake_token, get_client

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
        self.assertEqual(token_from_provider.expires, token_from_db.expires)
        fetch_token_mock.assert_called_once_with(app)

    @patch('oauth2_client.client.fetch_token')
    def test_token_exists(self, fetch_token_mock):
        """
        Ensure no token is fetched if there is a valid one.
        """
        from .ide_test_compat import ApplicationFactory, AccessToken, AccessTokenFactory, fake_token, get_client

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
        self.assertFalse(AccessToken.objects.filter(application=app) .exclude(id=access_token.id).exists())

    @patch('oauth2_client.client.fetch_token')
    @requests_mock.Mocker()
    def test_client_returns_data(self, fetch_token_mock, mock_response):
        """
        Given a valid token, ensure the client returns data
        """
        from .ide_test_compat import ApplicationFactory, AccessTokenFactory, get_client

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        access_token = AccessTokenFactory(application=app)
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
        from .ide_test_compat import ApplicationFactory, AccessTokenFactory, AccessToken, get_client

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
        from .ide_test_compat import ApplicationFactory, AccessTokenFactory, AccessToken, get_client

        access_token = 'curr_token'
        app = ApplicationFactory()
        AccessTokenFactory(token=access_token, application=app)

        tested_client = get_client(app.name)
        self.assertEqual(tested_client.token['access_token'], access_token)

        access_tokens = AccessToken.objects.filter(application=app)
        self.assertEqual(1, access_tokens.count())
        fetch_token_mock.assert_not_called()

    @patch('oauth2_client.client.fetch_and_store_token')
    @requests_mock.Mocker()
    def test_expired_jwt_token_refetched(self, mock_fetch_token, mock_response):
        """
        JWT token expiry detection gets triggered by a bad status code. Ensure token refetch is attempted.
        """
        from .ide_test_compat import ApplicationFactory, AccessTokenFactory, OAuth2Client

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(application=app)
        mock_fetch_token.return_value = token
        tested_client = OAuth2Client(token)
        # MOCK: first response is bad, next token is refetched, second response is 200 OK
        mock_response.get(api_url, [JWT_INVALID_RESP, {'status_code': 200}])
        tested_client.get(api_url)
        mock_fetch_token.assert_called_once_with(app)

    @patch('oauth2_client.client.fetch_and_store_token')
    @requests_mock.Mocker()
    def test_expired_jwt_token_breaks_circuit(self, mock_fetch_token, mock_response):
        """
        Circuit breaker opens when two 400 codes received in a row. 400 status code
        is used as one of the ways of detecting token expiry, for Salesforce JWT grant.
        """
        from .ide_test_compat import ApplicationFactory, AccessTokenFactory, OAuth2Client

        api_url = 'https://some-api.com/api/hello'
        app = ApplicationFactory()
        token = AccessTokenFactory(application=app)
        mock_fetch_token.return_value = token
        tested_client = OAuth2Client(token)
        # MOCK: first response is 400 with error msg, next token is successfully refetched,
        # but second response is 400 with error too. Circuit opens.
        mock_response.get(api_url, [JWT_INVALID_RESP, JWT_INVALID_RESP])
        with six.assertRaisesRegex(self, CircuitBreakerError, "Failures threshold reached"):
            tested_client.get(api_url)
        mock_fetch_token.assert_called_once_with(app)
