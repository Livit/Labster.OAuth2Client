"""
Test cases for `oauth2provider_app` django command. Most of the logic lives
in the parent class and has separate tests, so this one is brief.

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
"""

from ddt import data, ddt, unpack
from django.core.management import call_command
from faker import Factory
from oauth2_provider.models import Application

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
        from oauth2_client.tests.factories import fake_app_name
        app_name = fake_app_name()
        cmd_args = [
            'oauth2provider_app',
            '--name=%s' % app_name,
            '--client-type=%s' % client_type,
            '--authorization-grant-type=%s' % grant_type,
            '-v 2',
        ]
        if skip_auth:
            cmd_args.append('--skip-authorization')

        call_command(*cmd_args)

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.authorization_grant_type, grant_type)
        self.assertEqual(check_app.skip_authorization, skip_auth)
        self.assertEqual(check_app.client_type, client_type)

        redirect_uri = faker.url()
        cmd_args = [
            'oauth2provider_app',
            '--update',
            '--name=%s' % app_name,
            '--redirect-uris=%s' % redirect_uri
        ]

        call_command(*cmd_args)

        check_app.refresh_from_db()
        self.assertIn(redirect_uri, check_app.redirect_uris)
