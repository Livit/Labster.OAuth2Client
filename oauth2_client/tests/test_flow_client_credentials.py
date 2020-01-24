"""
Tests for Client Credentials Flow

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
"""
import os
import time
from datetime import timedelta

import pytz
import requests_mock
from django.utils import timezone as tz

from test_case import StandaloneAppTestCase


class ClientCredentialsFlowTest(StandaloneAppTestCase):
    """
    Tests for Client Credentials Flow
    """
    CURR_DIR = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def get_mocked_response_client_credentials_flow():
        """
        Mocked response as one returned by the `oauth2_provider`.
        """
        return """{
        "access_token": "yajNXTGfIy2GevvYKgFDU2TDyy2913",
        "token_type": "Bearer",
        "expires_in": 36000,
        "scope": "read write"
        }
        """

    @requests_mock.Mocker()
    def test_client_credentials_flow(self, m):
        """
        Test client credentials flow (AKA backend flow).
        Scope is present in provider's response.
        """
        from oauth2_client.fetcher import fetch_token
        from oauth2_client.tests.factories import ApplicationFactory

        token_uri = 'http://this-is-fake.region.nip.io:8200/o/token/'
        app_data = {
            'authorization_grant_type': 'client-credentials',
            'token_uri': token_uri,
        }
        app = ApplicationFactory(**app_data)
        # mock provider's response
        m.post(token_uri, text=self.get_mocked_response_client_credentials_flow())

        actual_token = fetch_token(app)
        self.assertEqual(actual_token.token, "yajNXTGfIy2GevvYKgFDU2TDyy2913")
        token_expected_expires = tz.now() + timedelta(seconds=36000)
        self.assertAlmostEqual(actual_token.expires, token_expected_expires, delta=timedelta(seconds=1))
        self.assertEqual(set(actual_token.scope.split()), {"read", "write"})
        self.assertEqual(actual_token.token_type, "Bearer")

    @staticmethod
    def get_mocked_response_client_credentials_flow_no_scope():
        """
        Mocked response as one returned by in-house provider
        """
        return """{
        "access_token": "yajNXTGfIy2GevvYKgFDU2TDyy2913",
        "token_type": "Bearer",
        "expires_in": 36000
        }
        """

    @requests_mock.Mocker()
    def test_client_credentials_flow_no_scope(self, m):
        """
        Test client credentials flow, no scope returned from the provider.
        """
        from oauth2_client.fetcher import fetch_token
        from oauth2_client.tests.factories import ApplicationFactory

        token_uri = 'http://this-is-fake.region.nip.io:8200/o/token/'
        app_data = {
            'authorization_grant_type': 'client-credentials',
            'token_uri': token_uri,
        }
        app = ApplicationFactory(**app_data)
        # mock provider's response
        m.post(token_uri, text=self.get_mocked_response_client_credentials_flow_no_scope())

        actual_token = fetch_token(app)
        self.assertEqual(actual_token.token, "yajNXTGfIy2GevvYKgFDU2TDyy2913")
        token_expected_expires = tz.now() + timedelta(seconds=36000)
        self.assertAlmostEqual(actual_token.expires, token_expected_expires, delta=timedelta(seconds=1))
        self.assertFalse(actual_token.scope)

    @staticmethod
    def get_mocked_response_client_credentials_flow_expires_at():
        """
        Mocked response, with expires_at instead of expires_in. We support both.
        """
        return """{
        "access_token": "yajNXTGfIy2GevvYKgFDU2TDyy2913",
        "token_type": "Bearer",
        "expires_at": %s,
        "scope": "read write"
        }
        """ % (time.time() + 200)

    @requests_mock.Mocker()
    def test_client_credentials_flow_expires_at(self, m):
        """
        Test client credentials flow with `expires_at` returned
        """
        from oauth2_client.fetcher import fetch_token
        from oauth2_client.tests.factories import ApplicationFactory

        token_uri = 'http://this-is-fake.region.nip.io:8200/o/token/'
        app_data = {
            'authorization_grant_type': 'client-credentials',
            'token_uri': token_uri,
        }
        app = ApplicationFactory(**app_data)
        # mock provider's response
        m.post(token_uri, text=self.get_mocked_response_client_credentials_flow_expires_at())

        actual_token = fetch_token(app)
        self.assertEqual(actual_token.token, "yajNXTGfIy2GevvYKgFDU2TDyy2913")
        token_expected_expires = tz.datetime.now(tz.utc) + timedelta(seconds=200)
        # bring to same timezone for comparison
        self.assertAlmostEqual(
            actual_token.expires.astimezone(pytz.UTC),
            token_expected_expires.astimezone(pytz.UTC),
            delta=timedelta(seconds=1)
        )
        self.assertEqual(set(actual_token.scope.split()), {"read", "write"})
