"""
Tests for JWT Flow.
"""
import os
from datetime import datetime

import requests_mock
from django.core.exceptions import ValidationError
from pytz import timezone

from test_case import StandaloneAppTestCase
from .test_compat import patch


class TestJWTFlow(StandaloneAppTestCase):
    """
    Tests for JWT Flow
    """
    MOCK_ACCESS_TOKEN = "thisIs.mocked.accessToken"
    CURR_DIR = os.path.dirname(os.path.abspath(__file__))
    TEST_KEY = os.path.join(CURR_DIR, 'resources', 'test.key')

    def get_mocked_response_jwt_flow(self):
        """
        Mocked provider response, like the one Salesforce returns.
        """
        return """{
        "access_token": "%s",
        "scope": "web openid api id",
        "instance_url": "https://yourInstance.salesforce.com",
        "id": "https://yourInstance.salesforce.com/id/00Dxx0000001gPLEAY/005xx000001SwiUAAS",
        "token_type": "Bearer"
        }""" % self.MOCK_ACCESS_TOKEN

    @requests_mock.Mocker()
    def test_jwt_flow(self, m):
        """
        Test JWT Token Bearer flow fetches token
        """
        from .ide_test_compat import ApplicationFactory
        from oauth2_client.client import fetch_token

        app_data = {
            'authorization_grant_type': 'jwt-bearer',
            'client_secret': self.TEST_KEY,
            'extra_settings': {'subject': 'xyz@abx.com.lightning'},
            'token_uri': 'https://test.salesforce.com/services/oauth2/token',
        }
        app = ApplicationFactory(**app_data)
        # mock provider's response
        m.post(
            "https://test.salesforce.com/services/oauth2/token",
            text=self.get_mocked_response_jwt_flow()
        )

        actual_token = fetch_token(app)
        self.assertEqual(actual_token.token, self.MOCK_ACCESS_TOKEN)
        self.assertEqual(set(actual_token.scope.split()), {"web", "openid", "api", "id"})
        self.assertEqual(actual_token.token_type, "Bearer")

    def test_subject_not_specified(self):
        """
        Raise an exception when no subject specified. Subject is always required
        on the Application instance (in extra_settings['subject'])
        """
        from .ide_test_compat import ApplicationFactory

        app_data = {
            'authorization_grant_type': 'jwt-bearer',
        }
        app = ApplicationFactory(**app_data)
        with self.assertRaises(ValidationError):
            app.clean()  # django's interface to trigger validation

    def get_mocked_response_jwt_flow_no_scope(self):
        """
        Mocked response with no scope, similar to the one from Salesforce
        """
        return """{
        "access_token": "%s",
        "instance_url": "https://yourInstance.salesforce.com",
        "id": "https://yourInstance.salesforce.com/id/00Dxx0000001gPLEAY/005xx000001SwiUAAS",
        "token_type": "Bearer"
        }""" % self.MOCK_ACCESS_TOKEN

    @requests_mock.Mocker()
    def test_jwt_flow_no_scope(self, m):
        """
        Test JWT Token Bearer flow. No scope returned from provider.
        """
        from .ide_test_compat import ApplicationFactory
        from oauth2_client.client import fetch_token

        app_data = {
            'authorization_grant_type': 'jwt-bearer',
            'client_secret': self.TEST_KEY,
            'extra_settings': {'subject': 'xyz@abc.com.lightning'},
            'token_uri': 'https://test.salesforce.com/services/oauth2/token',
        }
        app = ApplicationFactory(**app_data)
        # mock provider's response
        m.post(
            "https://test.salesforce.com/services/oauth2/token",
            text=self.get_mocked_response_jwt_flow_no_scope()
        )

        actual_token = fetch_token(app)
        self.assertEqual(actual_token.token, self.MOCK_ACCESS_TOKEN)
        self.assertFalse(actual_token.scope)

    def test_get_audience_prod(self):
        """
        Ensure the `audience` claim parameter is valid for prod SF URL
        """
        from .ide_test_compat import ApplicationFactory, JWTFetcher

        app_data = {
            'authorization_grant_type': 'jwt-bearer',
            'token_uri': 'https://login.salesforce.com/services/oauth2/token',
        }
        app = ApplicationFactory(**app_data)
        fetcher = JWTFetcher(app)
        expected = 'https://login.salesforce.com'
        actual = fetcher._audience()
        self.assertEqual(expected, actual)

    def test_get_audience_sandbox(self):
        """
        Ensure the `audience` claim parameter is valid for sandbox SF URL
        """
        from .ide_test_compat import ApplicationFactory, JWTFetcher

        app_data = {
            'authorization_grant_type': 'jwt-bearer',
            'token_uri': 'https://test.salesforce.com/services/oauth2/token',
        }
        app = ApplicationFactory(**app_data)
        fetcher = JWTFetcher(app)
        expected = 'https://test.salesforce.com'
        actual = fetcher._audience()
        self.assertEqual(expected, actual)

    @patch('oauth2_client.fetcher.timezone.now')
    def test_auth_payload(self, mocked_now):
        """
        Current authorization payload is happily accepted by Salesforce auth
        server. Make sure it doesn't change unintentionally. The payload is a
        function of Application data, signing key, and current time.
        """
        from .ide_test_compat import JWTFetcher, ApplicationFactory

        app_data = {
            'name': 'jwt_app',
            'authorization_grant_type': 'jwt-bearer',
            'client_id': 'fake.long.client.id.string',
            'client_secret': self.TEST_KEY,
            'extra_settings': {'subject': 'xyz@abx.com.lightning'},
            'token_uri': 'https://test.salesforce.com/services/oauth2/token',
        }
        # timezone only to silence a warning of enabled timezone support in django
        mocked_now.return_value = datetime(2020, 1, 1, tzinfo=timezone('GMT'))
        app = ApplicationFactory(**app_data)
        actual_payload = JWTFetcher(app).auth_payload()
        expected_payload = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': 'eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiAiZmFrZS5sb25nLmNsaWVudC5pZC5zdHJpbmciLCAi'
                         'c3ViIjogInh5ekBhYnguY29tLmxpZ2h0bmluZyIsICJhdWQiOiAiaHR0cHM6Ly90ZXN0LnNhb'
                         'GVzZm9yY2UuY29tIiwgImV4cCI6IDE1Nzc4MzY5NTB9.TTZ_pzkm7QdNZlNIbzT-hFAW87z5S'
                         'rG3LdptPIYPGAfA1QnnXglKvMtx98yrK5554qI0oV03QwD4DZz9Ly_H-76nsThYm6G2Av_NMF'
                         'UBmsMV2rO5vZRqygIYqP1eb7I-k3ZsoSNhScQ-s5jWx0dupOkn2SIVhOnDjsuzGwx2M90='
        }
        self.assertEqual(expected_payload, actual_payload)
