"""
Test cases for the `oauth2_app_maker` abstract django  parent command.

These tests are a little clunky, as we have to turn an abstract tested
command into a functional one on the fly. Due to the way Django registers
commands upon startup, there seems to be no other (easy) way to do that.
Using `tested_command.run_from_argv(...)` is not a good idea, as this would not
test the entire django's invocation path. This command constitutes an important
functionality of this package, so we want to use `call_command(...)` to invoke,
as that exercises entire execution flow.

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
"""
import six
from django.core.exceptions import ValidationError
from django.core.management import call_command
from faker import Factory
from testfixtures import LogCapture

from oauth2_client.management.commands.oauth2_app_maker import Command as TestedCommand
from oauth2_client.tests.test_compat import patch
from test_case import StandaloneAppTestCase

faker = Factory.create()


def command_type_with_model(model_type):
    """
    Convenience function for testing. Create `oauth2_app_maker`
    class bound to the specified model type.
    """
    class Command(TestedCommand):
        @classmethod
        def app_model(cls):
            return model_type
    return Command


def test_add_arguments(parser):
    """
    To make tested command runnable, we need it to be able to accept input arguments.
    Add only a few, for we don't need everything here. This is used for mocking.
    """
    parser.add_argument(
        '--update',
        action='store_true',
    )
    parser.add_argument(
        '--name',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--client-id',
        type=str,
    )
    parser.add_argument(
        '--client-secret',
        type=str,
    )
    parser.add_argument(
        '--authorization-grant-type',
        type=str,
    )
    parser.add_argument(
        '--service-host',
        type=str,
    )
    parser.add_argument(
        '--token-uri',
        type=str,
    )


class TestOauth2AppMakerCmd(StandaloneAppTestCase):
    """
    Test cases for the `oauth2_app_maker` abstract django parent command.
    """

    def test_model_validation_bad_type(self):
        """
        Test validation: model type is as expected.
        """
        class BadAppModel:
            pass

        cmd = command_type_with_model(BadAppModel)()
        with six.assertRaisesRegex(self, ValidationError, "must extend django.db.models.Model"):
            cmd.handle()

    def test_model_validation_no_fields(self):
        """
        Test validation: model provides required fields.
        """
        from django.db import models

        class ModelWithoutFields(models.Model):
            class Meta:
                app_label = 'test_app_model_1'

        cmd = command_type_with_model(ModelWithoutFields)()
        with six.assertRaisesRegex(
                self, ValidationError, "Your app model does not provide all required fields"
        ):
            cmd.handle()

    @patch.object(TestedCommand, 'add_arguments', side_effect=test_add_arguments)
    @patch.object(TestedCommand, 'app_model')
    def test_create(self, model_mock, _add_arguments_mock):
        """
        Ensure Application gets created in the DB.
        """
        from oauth2_client.tests.factories import fake_app_name, fake_client_id, fake_client_secret
        from oauth2_client.models import Application
        model_mock.return_value = Application
        app_name = fake_app_name()
        client_id = fake_client_id()
        client_secret = fake_client_secret()
        service_host = faker.url()
        token_uri = faker.url()

        cmd_args = [
            'oauth2_app_maker',
            '--name=%s' % app_name,
            '--client-id=%s' % client_id,
            '--authorization-grant-type=client-credentials',
            '--client-secret=%s' % client_secret,
            '--service-host=%s' % service_host,
            '--token-uri=%s' % token_uri
        ]
        call_command(*cmd_args)

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.authorization_grant_type, 'client-credentials')
        self.assertEqual(check_app.client_id, client_id)
        self.assertEqual(check_app.client_secret, client_secret)
        self.assertEqual(check_app.service_host, service_host)
        self.assertEqual(check_app.token_uri, token_uri)

    @patch.object(TestedCommand, 'add_arguments', side_effect=test_add_arguments)
    @patch.object(TestedCommand, 'app_model')
    def test_create_validation(self, model_mock, _add_arguments_mock):
        """
        Ensure model validation works when creating an application.
        Creation should be aborted upon validation error.
        """
        from oauth2_client.tests.factories import fake_app_name, fake_client_id
        from oauth2_client.models import Application
        model_mock.return_value = Application
        app_name = fake_app_name()
        client_id = fake_client_id()

        cmd_args = [
            'oauth2_app_maker',
            '--name=%s' % app_name,
            '--client-id=%s' % client_id,
            '--authorization-grant-type=client-credentials'
        ]
        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)

        check_app = Application.objects.filter(name=app_name).first()
        self.assertFalse(check_app)
        self.assertIn("Please correct the following validation errors", str(logs))

    @patch.object(TestedCommand, 'add_arguments', side_effect=test_add_arguments)
    @patch.object(TestedCommand, 'app_model')
    def test_cannot_update_nonexistent_app(self, model_mock, _add_arguments_mock):
        """
        Ensure we can't update a nonexistent application.
        """
        from oauth2_client.tests.factories import fake_app_name, fake_client_id
        from oauth2_client.models import Application
        model_mock.return_value = Application
        app_name = fake_app_name()
        client_id = fake_client_id()

        cmd_args = [
            'oauth2_app_maker',
            '--update',
            '--name=%s' % app_name,
            '--client-id=%s' % client_id,
            '-v 2'
        ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)
                self.assertIn("must exist to be updated", str(logs))

    @patch.object(TestedCommand, 'add_arguments', side_effect=test_add_arguments)
    @patch.object(TestedCommand, 'app_model')
    def test_update(self, model_mock, _add_arguments_mock):
        """
        Ensure update functionality works fine.
        """
        from oauth2_client.tests.factories import fake_app_name, fake_client_id, fake_client_secret
        from oauth2_client.models import Application
        model_mock.return_value = Application
        app_name = fake_app_name()
        client_id = fake_client_id()
        client_secret = fake_client_secret()
        service_host = faker.url()
        token_uri = faker.url()
        cmd_args = [
            'oauth2_app_maker',
            '--name=%s' % app_name,
            '--authorization-grant-type=client-credentials',
            '--client-id=%s' % client_id,
            '--client-secret=%s' % client_secret,
            '--service-host=%s' % service_host,
            '--token-uri=%s' % token_uri,
            '-v 2'
        ]

        call_command(*cmd_args)

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.client_id, client_id)
        upd_time_1 = check_app.updated
        create_time_1 = check_app.created
        grant_type_1 = check_app.authorization_grant_type
        client_secret_1 = check_app.client_secret
        service_host_1 = check_app.service_host
        token_uri_1 = check_app.token_uri

        client_id_2 = fake_client_id()
        cmd_args = [
            'oauth2_app_maker',
            '--update',
            '--name=%s' % app_name,
            '--client-id=%s' % client_id_2,
            '-v 2'
        ]

        call_command(*cmd_args)

        check_app.refresh_from_db()
        upd_time_2 = check_app.updated
        create_time_2 = check_app.created
        self.assertEqual(check_app.client_id, client_id_2)
        self.assertNotEqual(client_id, client_id_2)
        self.assertGreater(upd_time_2, upd_time_1)
        self.assertEqual(create_time_1, create_time_2)

        # verify other existing properties didn't change
        self.assertEqual(grant_type_1, check_app.authorization_grant_type)
        self.assertEqual(client_secret_1, check_app.client_secret)
        self.assertEqual(service_host_1, check_app.service_host)
        self.assertEqual(token_uri_1, check_app.token_uri)

    @patch.object(TestedCommand, 'add_arguments', side_effect=test_add_arguments)
    @patch.object(TestedCommand, 'app_model')
    def test_update_validation(self, model_mock, _add_arguments_mock):
        """
        Check if update functionality validates the data in update mode.
        Update should be aborted on validation errors.
        """
        from oauth2_client.tests.factories import fake_app_name, fake_client_id, fake_client_secret
        from oauth2_client.models import Application
        model_mock.return_value = Application
        app_name = fake_app_name()
        client_id = fake_client_id()
        client_secret = fake_client_secret()
        service_host = faker.url()
        token_uri = faker.url()
        cmd_args = [
            'oauth2_app_maker',
            '--name=%s' % app_name,
            '--authorization-grant-type=client-credentials',
            '--client-id=%s' % client_id,
            '--client-secret=%s' % client_secret,
            '--service-host=%s' % service_host,
            '--token-uri=%s' % token_uri,
            ]

        call_command(*cmd_args)

        check_app = Application.objects.get(name=app_name)
        self.assertEqual(check_app.client_id, client_id)
        upd_time_1 = check_app.updated
        create_time_1 = check_app.created
        grant_type_1 = check_app.authorization_grant_type
        service_host_1 = check_app.service_host
        token_uri_1 = check_app.token_uri

        # attempt to make a forbidden change
        cmd_args = [
            'oauth2_app_maker',
            '--update',
            '--name=%s' % app_name,
            '--token-uri='
            ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(
                    *cmd_args
                )
        self.assertIn("Please correct the following validation errors", str(logs))

        # make sure values didn't change (update failed)
        check_app.refresh_from_db()
        self.assertEqual(check_app.client_id, client_id)
        self.assertEqual(upd_time_1, check_app.updated)
        self.assertEqual(create_time_1, check_app.created)
        self.assertEqual(grant_type_1, check_app.authorization_grant_type)
        self.assertEqual(service_host_1, check_app.service_host)
        self.assertEqual(token_uri_1, check_app.token_uri)
