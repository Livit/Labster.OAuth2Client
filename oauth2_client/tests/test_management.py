"""
Tests for Management package.

Local imports of model-related files are required for in-IDE test runs.
Otherwise an import will be attempted before django.setup() call and
an exception is thrown.
"""
from django.core.exceptions import ValidationError
from django.core.management import call_command
from faker import Factory
from testfixtures import LogCapture

from oauth2_client.tests.factories import fake_app_name, fake_client_id, fake_client_secret
from test_case import StandaloneAppTestCase

faker = Factory.create()


class TestClientAppMakerCommand(StandaloneAppTestCase):
    """
    Test cases for the `oauth2client_app` django command.
    """

    def test_oauth2client_app_create(self):
        """
        Test creating various oauth applications with different parameters.
        Not using ddt here to be able to run this in IDE (model imports)
        """
        from oauth2_client.models import Application
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
                '--client-secret=%s' % client_secret,
                '--extra-settings={"subject": "%s"}' % test_email,
                '-v 2'
            ]

            call_command(
                *cmd_args
            )

            check_app = Application.objects.get(name=app_name)

            self.assertEqual(check_app.authorization_grant_type, grant_type)
            self.assertEqual(check_app.service_host, service_host)
            self.assertEqual(check_app.token_uri, token_uri)
            self.assertEqual(check_app.client_id, client_id)
            self.assertEqual(check_app.client_secret, client_secret)
            self.assertEqual(check_app.extra_settings['subject'], test_email)

    def test_oauth2_client_app_cannot_update_nonexistent(self):
        """
        Ensure we can't update nonexistent application
        """
        app_name = fake_app_name()
        client_id = faker.pystr(min_chars=10, max_chars=20)
        cmd_args = [
            'oauth2client_app',
            '--update',
            '--name=%s' % app_name,
            '--client-id=%s' % client_id,
            '-v 2'
        ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(
                    *cmd_args
                )
                self.assertIn("must exist to be updated", str(logs))

    def test_oauth2_client_app_update(self):
        """
        Check if update functionality works.
        """
        from oauth2_client.models import Application
        app_name = fake_app_name()
        service_host = faker.url()
        client_id = fake_client_id()
        client_secret = fake_client_secret()
        token_uri = faker.url()
        cmd_args = [
            'oauth2client_app',
            '--name=%s' % app_name,
            '--authorization-grant-type=%s' % Application.GRANT_CLIENT_CREDENTIALS,
            '--token-uri=%s' % token_uri,
            '--service-host=%s' % service_host,
            '--client-id=%s' % client_id,
            '--client-secret=%s' % client_secret,
            '-v 2'
        ]

        call_command(
            *cmd_args
        )

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.client_id, client_id)
        upd_time_1 = check_app.updated
        create_time_1 = check_app.created
        grant_type_1 = check_app.authorization_grant_type
        service_host_1 = check_app.service_host

        client_id_2 = fake_client_id()
        cmd_args = [
            'oauth2client_app',
            '--update',
            '--name=%s' % app_name,
            '--client-id=%s' % client_id_2,
            '-v 2'
        ]

        call_command(
            *cmd_args
        )

        check_app.refresh_from_db()
        upd_time_2 = check_app.updated
        create_time_2 = check_app.created
        self.assertEqual(check_app.client_id, client_id_2)
        self.assertNotEqual(client_id, client_id_2)
        self.assertGreater(upd_time_2, upd_time_1)
        self.assertEqual(create_time_1, create_time_2)

        # verify other existing properties didn't change
        self.assertEqual(grant_type_1, check_app.authorization_grant_type)
        self.assertEqual(service_host_1, check_app.service_host)

    def test_oauth2_client_app_update_validation_works(self):
        """
        Check if update functionality validates the data in update mode.
        Update should be aborted on validation errors.
        """
        from oauth2_client.models import Application
        app_name = fake_app_name()
        service_host = faker.url()
        test_email = faker.email()
        client_id = fake_client_id()
        client_secret = fake_client_secret()
        token_uri = faker.url()
        cmd_args = [
            'oauth2client_app',
            '--name=%s' % app_name,
            '--authorization-grant-type=%s' % Application.GRANT_JWT_BEARER,
            '--token-uri=%s' % token_uri,
            '--service-host=%s' % service_host,
            '--client-id=%s' % client_id,
            '--client-secret=%s' % client_secret,
            '--extra-settings={"subject": "%s"}' % test_email,
        ]

        call_command(
            *cmd_args
        )

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.client_id, client_id)
        upd_time_1 = check_app.updated
        create_time_1 = check_app.created
        grant_type_1 = check_app.authorization_grant_type
        service_host_1 = check_app.service_host

        # attempt to clear `subject` key from `extra_settings`, what is forbidden in this flow
        cmd_args = [
            'oauth2client_app',
            '--update',
            '--name=%s' % app_name,
            '--extra-settings={}',
        ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(
                    *cmd_args
                )
        self.assertIn("requires `subject` to be specified", str(logs))

        # make sure values didn't change (update failed)
        check_app.refresh_from_db()
        self.assertEqual(test_email, check_app.extra_settings['subject'])
        self.assertEqual(check_app.client_id, client_id)
        self.assertEqual(upd_time_1, check_app.updated)
        self.assertEqual(create_time_1, check_app.created)
        self.assertEqual(grant_type_1, check_app.authorization_grant_type)
        self.assertEqual(service_host_1, check_app.service_host)

    def test_oauth2client_app_jwt_flow_validation_error(self):
        """
        Make sure creating JWT_BEARER application fails, if no subject provided
        """
        from oauth2_client.models import Application
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
                call_command(
                    *cmd_args
                )

        check_app = Application.objects.filter(name=app_name).first()
        self.assertFalse(check_app)
        self.assertIn("requires `subject` to be specified", str(logs))
