"""
Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown. This is a (hopefully) temporary fix.
"""
from django.db import models
from oauth2_provider.models import Application as ProviderApplication

from oauth2_client.client import get_client, OAuth2Client
from oauth2_client.fetcher import Fetcher, JWTFetcher
from oauth2_client.management.commands.oauth2_app_maker import Command as AbstractAppMaker
from oauth2_client.models import AccessToken, Application
from tests.factories import (
    ApplicationFactory, AccessTokenFactory, fake_client_secret, fake_token, fake_app_name, fake_client_id
)
from tests.models import NameNotMandatoryApp, NoRequiredFieldsApp, TestApplication, TestApplicationNoUnique
