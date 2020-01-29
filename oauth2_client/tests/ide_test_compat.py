"""
Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown. This is a (hopefully) temporary fix.
"""
from django.db import models

from oauth2_client.client import get_client, OAuth2Client, fetch_token, fetch_and_store_token
from oauth2_client.fetcher import Fetcher, JWTFetcher
from oauth2_client.models import AccessToken, Application
from oauth2_client.tests.factories import (
    ApplicationFactory, AccessTokenFactory, fake_client_secret, fake_token, fake_app_name, fake_client_id
)
