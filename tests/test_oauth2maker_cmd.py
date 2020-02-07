"""
Test cases for the `oauth2_app_maker` abstract django  parent command.

Use `tests.app_maker_testing.py` as a simple test-only extension, to turn an
abstract command into a specific one for testing. Test models are defined in
`tests.models.py`, to decouple test logic of the abstract command from specific
Application classes that are used in production.
"""
from datetime import datetime

import six
from django.core.exceptions import ValidationError
from django.core.management import call_command
from faker import Factory
from pytz import timezone
from testfixtures import LogCapture

from test_case import StandaloneAppTestCase
from tests.management.commands.app_maker_testing import Command as TestedCommand
from tests.test_compat import patch

faker = Factory.create()


def command_type_with_model(model_type):
    """
    Convenience function for testing. Create `oauth2_app_maker` extension
    class bound to the specified model type.
    """
    from tests.ide_test_compat import AbstractAppMaker

    class Command(AbstractAppMaker):
        @classmethod
        def app_model(cls):
            return model_type
    return Command


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
        from tests.ide_test_compat import NoRequiredFieldsApp

        cmd = command_type_with_model(NoRequiredFieldsApp)()
        with six.assertRaisesRegex(
                self, ValidationError, "Your app model does not provide all required fields"
        ):
            cmd.handle()

    @patch('oauth2_client.fetcher.timezone.now')
    @patch.object(TestedCommand, 'app_model')
    def test_create(self, model_mock, now_mock):
        """
        Ensure Application gets created in the DB.
        """
        from tests.ide_test_compat import fake_app_name, TestApplication

        model_mock.return_value = TestApplication
        now = datetime(2020, 1, 1, tzinfo=timezone('CET'))  # arbitrary datetime
        now_mock.return_value = now
        app_name = fake_app_name()

        cmd_args = [
            'app_maker_testing',
            '--name=%s' % app_name,
            '--required-property=hello',
            '--optional-property=world',
            ]
        call_command(*cmd_args)

        check_app = TestApplication.objects.get(name=app_name)
        self.assertEqual(check_app.required_property, "hello")
        self.assertEqual(check_app.optional_property, "world")
        self.assertEqual(check_app.created, now)
        self.assertIsNotNone(check_app.updated, now)

    @patch.object(TestedCommand, 'app_model')
    def test_create_validation(self, model_mock):
        """
        Ensure model validation works when creating an application.
        Creation should be aborted upon validation error.
        """
        from tests.ide_test_compat import fake_app_name, TestApplication

        model_mock.return_value = TestApplication
        app_name = fake_app_name()

        # one required property is missing
        cmd_args = [
            'app_maker_testing',
            '--name=%s' % app_name,
            ]
        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)

        check_app = TestApplication.objects.filter(name=app_name).first()
        self.assertFalse(check_app)
        self.assertIn("Please correct the following validation errors", str(logs))

    @patch.object(TestedCommand, 'app_model')
    def test_cannot_update_nonexistent_app(self, model_mock):
        """
        Ensure we can't update a nonexistent application.
        """
        from tests.ide_test_compat import fake_app_name, TestApplication

        model_mock.return_value = TestApplication
        app_name = fake_app_name()

        cmd_args = [
            'app_maker_testing',
            '--update',
            '--name=%s' % app_name,
            '--required-property=some_value',
            ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)
        self.assertIn("must exist to be updated", str(logs))

    @patch.object(TestedCommand, 'app_model')
    def test_update(self, model_mock):
        """
        Ensure update functionality works fine.
        """
        from tests.ide_test_compat import fake_app_name, TestApplication

        model_mock.return_value = TestApplication
        app_name = fake_app_name()
        initial_value = 'good morning'

        cmd_args = [
            'app_maker_testing',
            '--name=%s' % app_name,
            '--required-property=%s' % initial_value,
            '--optional-property=opt'
        ]

        call_command(*cmd_args)

        check_app = TestApplication.objects.get(name=app_name)
        upd_time_1 = check_app.updated
        create_time_1 = check_app.created
        self.assertEqual(check_app.required_property, initial_value)

        updated_value = 'good bye'
        cmd_args = [
            'app_maker_testing',
            '--update',
            '--name=%s' % app_name,
            '--required-property=%s' % updated_value,
            ]

        call_command(*cmd_args)

        check_app.refresh_from_db()
        upd_time_2 = check_app.updated
        create_time_2 = check_app.created

        self.assertEqual(check_app.required_property, updated_value)
        self.assertEqual(check_app.optional_property, 'opt')
        self.assertGreater(upd_time_2, upd_time_1)
        self.assertEqual(create_time_1, create_time_2)

    @patch.object(TestedCommand, 'app_model')
    def test_update_validation(self, model_mock):
        """
        Check if update functionality validates the data in update mode.
        Update should be aborted upon validation errors.
        """
        from tests.ide_test_compat import fake_app_name, TestApplication

        model_mock.return_value = TestApplication
        app_name = fake_app_name()

        cmd_args = [
            'app_maker_testing',
            '--name=%s' % app_name,
            '--required-property=hello',
            '--optional-property=opt',
            ]

        call_command(*cmd_args)

        check_app = TestApplication.objects.get(name=app_name)
        upd_time_1 = check_app.updated
        create_time_1 = check_app.created

        # attempt to make a forbidden change
        cmd_args = [
            'app_maker_testing',
            '--update',
            '--name=%s' % app_name,
            '--required-property='
        ]

        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)

        self.assertIn("Please correct the following validation errors", str(logs))

        # make sure values didn't change (update aborted)
        check_app.refresh_from_db()
        self.assertEqual(check_app.required_property, "hello")
        self.assertEqual(check_app.optional_property, "opt")
        self.assertEqual(upd_time_1, check_app.updated)
        self.assertEqual(create_time_1, check_app.created)

    @patch.object(TestedCommand, 'app_model')
    def test_create_enforce_unique_name(self, model_mock):
        """
        Ensure name uniqueness is enforced upon Application creation, even when
        not defined on the model.
        """
        from tests.ide_test_compat import fake_app_name, TestApplicationNoUnique

        model_mock.return_value = TestApplicationNoUnique
        app_name = fake_app_name()

        cmd_args = [
            'app_maker_testing',
            '--name=%s' % app_name,
            '--required-property=hello'
        ]
        call_command(*cmd_args)

        # try to create same thing again
        with LogCapture() as logs:
            with self.assertRaises(ValidationError):
                call_command(*cmd_args)
        self.assertIn("Application already exists", str(logs))
        self.assertIn(app_name, str(logs))

    @patch.object(TestedCommand, 'app_model')
    def test_model_with_name_blank(self, model_mock):
        """
        Ensure an Application object without name won't get created.
        """
        from tests.ide_test_compat import NameNotMandatoryApp

        model_mock.return_value = NameNotMandatoryApp

        cmd_args = [
            'app_maker_testing',
            '--name=',
        ]

        with six.assertRaisesRegex(self, ValidationError, "This field cannot be blank"):
            call_command(*cmd_args)
