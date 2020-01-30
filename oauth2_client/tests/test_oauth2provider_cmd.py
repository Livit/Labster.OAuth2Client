"""
Test cases for `oauth2provider_app` django command. Most of the logic lives
in the parent class and has separate tests, so this one is brief.
"""

from ddt import data, ddt, unpack
from django.core.management import call_command
from faker import Factory
from oauth2_provider.models import Application

from oauth2_client.tests.factories import fake_app_name
from test_case import StandaloneAppTestCase

faker = Factory.create()


@ddt
class TestOauth2ProviderAppCmd(StandaloneAppTestCase):
    """
    Test cases for the `oauth2provider_app` django command.
    """

    @data(
        (Application.CLIENT_PUBLIC, Application.GRANT_CLIENT_CREDENTIALS, False),
        (Application.CLIENT_PUBLIC, Application.GRANT_CLIENT_CREDENTIALS, True),
        (Application.CLIENT_CONFIDENTIAL, Application.GRANT_PASSWORD, True),
        (Application.CLIENT_CONFIDENTIAL, Application.GRANT_PASSWORD, False),
    )
    @unpack
    def test_oauth2provider_app_command(self, client_type, grant_type, skip_auth):
        """
        Test creating and updating various oauth applications with different parameters.
        """
        app_name = fake_app_name()
        redirect_uri = faker.url()
        cmd_args = [
            'oauth2provider_app',
            '--name=%s' % app_name,
            '--client-type=%s' % client_type,
            '--authorization-grant-type=%s' % grant_type,
            '--redirect-uris=%s' % redirect_uri,
            '-v 2',
        ]
        if skip_auth:
            cmd_args.append('--skip-authorization')

        call_command(*cmd_args)

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.authorization_grant_type, grant_type)
        self.assertEqual(check_app.skip_authorization, skip_auth)
        self.assertEqual(check_app.client_type, client_type)
        self.assertEqual(check_app.redirect_uris, redirect_uri)
