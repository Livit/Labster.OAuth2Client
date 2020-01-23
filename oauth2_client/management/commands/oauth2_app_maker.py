"""
Abstract parent class for Django commands for
creating/updating OAuth Application data records in database.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from oauth2_client.utils.django.base_cmd import LoggingBaseCommand


class Command(LoggingBaseCommand):
    """
    NOTE: by `Application` or `App` we mean an OAuth application and its representation in the
        database, NOT a Django application.
        See here: https://django-oauth-toolkit.readthedocs.io/en/latest/glossary.html#application

    Abstract parent class for commands for creating OAuth2 Applications. Provides `create` and
    `update` logic. To extend, you have to provide the application model class to be used, and
    input arguments.

    Current descendants:
        oauth2provider_app  - create/update Application on Provider side
        oauth2client_app    - create/update Application on Client side

    See the extending classes for usage examples in CLI. Per default Django mechanism,
    every Command provides also a `--help/-h` option.

    Some conventions you need to follow when creating a new command for a new type of Application:
    - make your new command extend OAuth2AppMaker
    - `name` field on you model is mandatory and has to be unique
    - `updated` DateTimeField on your model is mandatory
    - please follow naming conventions of oauth2_provider.Application model class
    - field names on your model have to match parameter names in the command. For example, if your
      model has a field called `my_model.authorization_grant_type`, your command has to specify a
      parameter named: '--authorization-grant-type' or 'authorization_grant_type'. This is because
      both create and update dynamically map command arguments to model field names
    """

    @classmethod
    def app_model(cls):
        """
        Specify model class to use.

        Returns:
            type: Application model type to be used
        """
        raise NotImplementedError(
            'subclasses of OAuth2AppMaker must provide an app_model() method'
        )

    def add_arguments(self, parser):
        """
        Add common arguments required for all extending commands.
        """
        parser.add_argument(
            '--update',
            action='store_true',
            help='A flag to update an existing application. Defaults to `False`'
        )
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Application name',
        )

    @staticmethod
    def _filter_cmd_argument(argument_name, argument_value, model_fields, update_mode):
        """
        Command arguments always include a lot of ones added by Django, that we don't want to use to
        determine properties of our model object, e.g. `verbosity`, `settings`, `pythonpath` etc.
        This utility determines if we should use a command's input argument and pass its value to
        the App model instance that is being created/updated, or not.

        Some extra logic applies to argument's value, depending on `update` parameter value:

        Create mode (update==False):
        Use only arguments that have specified values. Don't pass any input Nones to the Application
        instance, so model's defaults are used.

        Update mode (update==True):
        Empty strings are allowed, to clear a value with the update (hence comparison to None)
        This is for example, when you have a `redirect_uri` specified on an Application and you
        want to erase it. (--redirect-uri="")

        Args:
            argument_name: str
            argument_value: Any
            model_fields: list of strings, names of all the fields appearing in the Application model
            update_mode: bool

        Returns:
            bool: shall the argument and it's value be used
        """

        if update_mode:
            return bool(argument_name in model_fields and argument_value is not None)
        else:
            return bool(argument_name in model_fields and argument_value)

    @staticmethod
    def _validate(model_type):
        """
        Validate provided application model type.

        Args:
            model_type (type): e.g. oauth2_client.models.Application

        Returns:
            None:

        Raises:
            ValidationError: 1) when model type is wrong; 2) when not all required fields available
            on the model type
        """
        if not issubclass(model_type, models.Model):
            raise ValidationError('The model class must extend django.db.models.Model')
        app_fields = [field.name for field in model_type._meta.fields]  # get field names
        required_fields = {'name', 'updated'}
        if any([required_field not in app_fields for required_field in required_fields]):
            raise ValidationError(
                'Your app model does not provide all required fields. Required fields: {} '
                'Found fields: {}'.format(required_fields, app_fields)
            )

    def handle(self, *args, **options):
        """
        Django hook to run the command.
        Dynamically extract all command's parameters related to the application, based on the model's
        type metadata. This works now and in the future, with any Application models. Run the logic,
        report errors if any, re-raise so user gets a non-zero exit code if execution fails.
        """
        app_model = self.app_model()
        self._validate(app_model)
        application_fields = [field.name for field in app_model._meta.fields]  # get field names
        application_data = {}
        is_update = options.pop('update')
        for arg_name, arg_value in options.items():
            if self._filter_cmd_argument(arg_name, arg_value, application_fields, is_update):
                application_data[arg_name] = arg_value

        try:
            if is_update:
                self._update(application_data)
            else:
                self._create(application_data)
        except ValidationError as exc:
            errors = "\n".join(
                ["- {}: {}".format(err_key, err_value) for err_key, err_value in exc.message_dict.items()]
            )
            self.logger.error('Please correct the following validation errors:\n %s', errors)
            raise

    def _update(self, application_data):
        """
        Updates an existing application, if model validation successful.

        Args:
            application_data (dict): key-values to update the App with

        Returns:
            None:

        Raises:
            ValidationError:  1) when app does not exist; 2) when multiple apps exist with same name;
            3) when data constraints defined on the model violated
        """
        app_name = application_data.pop('name')
        app_model = self.app_model()
        application_data['updated'] = timezone.now()
        try:
            app = app_model.objects.get(name=app_name)
            changed = False
            for key, target_val in application_data.items():
                current_val = getattr(app, key)
                if current_val != target_val:
                    setattr(app, key, target_val)
                    changed = True
            if changed:
                app.full_clean(validate_unique=False)  # validation
                app.save()
            self.logger.info('Application %s successfully updated.', app_name)
        except (app_model.MultipleObjectsReturned, app_model.DoesNotExist) as e:
            msg = (
                'Exactly one application with name={} must exist to be updated. Original error: {}'
                .format(app_name, e)
            )
            raise ValidationError({'name': msg})

    def _create(self, application_data):
        """
        Creates an application, if model validation successful.

        Args:
            application_data (dict): key-values for the new Application record

        Returns:
            None:

        Raises:
            ValidationError: 1) when app with this name already exist; 2) when data constraints
            defined on the model violated
        """
        app_model = self.app_model()
        target_application = app_model(**application_data)
        target_application.full_clean()  # validation
        target_application.save()
        self.logger.info('Application %s successfully created.', application_data['name'])
