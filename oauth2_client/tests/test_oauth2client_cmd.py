"""
Test cases for `oauth2client_app` django command.
"""

from django.core.exceptions import ValidationError
from django.core.management import call_command
from faker import Factory
from testfixtures import LogCapture

from test_case import StandaloneAppTestCase

faker = Factory.create()


class TestClientAppMakerCommand(StandaloneAppTestCase):
    """
    Test cases for the `oauth2client_app` django command.
    """

    def test_app_create(self):
        """
        Test creating various oauth applications with different parameters.
        Not using ddt here to be able to run this in IDE (model imports)
        """
        from .ide_test_compat import Application, fake_app_name, fake_client_id, fake_client_secret

        for grant_type in [grant[0] for grant in Application.GRANT_TYPES]:
            app_name = fake_app_name()
            service_host = faker.url()
            token_uri = faker.url()
            client_id = fake_client_id()
            client_secret = fake_client_secret()
            test_email = faker.email()
            cmd_args = [
                'oauth2client_app',
                '--name=%s' % app_name,
                '--authorization-grant-type=%s' % grant_type,
                '--service-host=%s' % service_host,
                '--client-id=%s' % client_id,
                '--token-uri=%s' % token_uri,
                '--scope=read write',
                '--client-secret=%s' % client_secret,
                '--extra-settings={"subject": "%s"}' % test_email,
                '-v 2'
            ]

            call_command(*cmd_args)

            check_app = Application.objects.get(name=app_name)
            self.assertEqual(check_app.authorization_grant_type, grant_type)
            self.assertEqual(check_app.service_host, service_host)
            self.assertEqual(check_app.token_uri, token_uri)
            self.assertEqual(check_app.client_id, client_id)
            self.assertEqual(check_app.client_secret, client_secret)
            self.assertEqual(check_app.extra_settings['subject'], test_email)
            self.assertEqual(check_app.scope, "read write")

    def test_jwt_flow_validation(self):
        """
        Make sure creating JWT_BEARER application fails, if no subject provided
        """
        from .ide_test_compat import Application, fake_app_name, fake_client_id, fake_client_secret

        app_name = fake_app_name()
        token_uri = faker.url()
        service_host = faker.url()
        client_id = fake_client_id()
        client_secret = fake_client_secret()
        cmd_args = [
            'oauth2client_app',
            '--name=%s' % app_name,
            '--authorization-grant-type=%s' % Application.GRANT_JWT_BEARER,
            '--token-uri=%s' % token_uri,
            '--service-host=%s' % service_host,
            '--client-id=%s' % client_id,
            '--client-secret=%s' % client_secret,
            '-v 2'
        ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)

        check_app = Application.objects.filter(name=app_name).first()
        self.assertFalse(check_app)
        self.assertIn("requires `subject` to be specified", str(logs))
