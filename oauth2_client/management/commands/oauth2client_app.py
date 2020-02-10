"""
Create an instance of OAuth2Client's Application in DB, from CLI.
"""
import json

from oauth2_client.management.commands.oauth2_app_maker import Command as AbstractAppMaker
from oauth2_client.models import Application
from oauth2_client.utils.django.model import help_text


class Command(AbstractAppMaker):
    """
    A command to create/update a new OAuth2 Application for Oauth2Client from CLI.
    `--name` parameter is ensured to be present and unique.

    Usage examples:
    python ./manage.py oauth2client_app -h  # this help message

    python ./manage.py oauth2client_app \\
        --name my_test_app2 \\
        --client-id "my-app-id-string" \\
        --client-secret "/certs/my_app_cert.key" \\
        --authorization-grant-type  jwt-bearer \\
        --service-host 'https://labster--Lightning.cs129.my.salesforce.com' \\
        --token-uri 'https://login.salesforce.com/services/oauth2/token' \\
        --scope 'read' \\
        --extra-settings='{"subject": "xyz@labster.com.lightning"}' \\
        --verbosity 2

    python ./manage.py oauth2client_app \\
        --update \\
        --name my_test_app2 \\
        --extra-settings='{"subject": "abc@labster.com.lightning"}' \\
        --verbosity 2

    python ./manage.py oauth2client_app \\
        --update \\
        --name my_test_app2 \\
        --scope ""   # empty strings allowed in update mode, to clear out a value

    Grant types available:

    1. Client Credentials Grant (AKA Backend Application flow)

    2. OAuth 2.0 JWT Bearer Token Flow
    - in this flow `client_secret` must contain a file path to the App's X509 .pem
      private key.
    - you need to specify the `subject` for this grant type, put a 'subject'
      field in extra_settings: --extra-settings={"subject": "xyz@labster.com"}.
      For details on `subject` go to: https://tools.ietf.org/html/rfc7523#section-3
    - for more on the JWT Bearer flow: https://tools.ietf.org/html/rfc7523
    """
    help = __doc__

    def app_model(self):
        """
        Application model type to be used
        """
        return Application

    def add_arguments(self, parser):
        """
        Arguments for fields we need populated in the resulting Application instance.
        Follow a convention that `argument name == model property name`
        Use help messages defined on the model.
        """
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--client-id',
            type=str,
            help=help_text('client_id', Application)
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help=help_text('client_secret', Application)
        )
        parser.add_argument(
            '--authorization-grant-type',
            type=str,
            help=help_text('authorization_grant_type', Application),
            choices=[g[0] for g in Application.GRANT_TYPES]
        )
        parser.add_argument(
            '--service-host',
            type=str,
            help=help_text('service_host', Application)
        )
        parser.add_argument(
            '--token-uri',
            type=str,
            help=help_text('token_uri', Application)
        )
        parser.add_argument(
            '--scope',
            type=str,
            help=help_text('scope', Application)
        )
        parser.add_argument(
            '--extra-settings',
            type=json.loads,
            help=help_text('extra_settings', Application)
        )
