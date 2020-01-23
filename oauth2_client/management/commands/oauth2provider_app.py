"""
Create an instance of oauth2_provider's Application in DB, from CLI.
"""
from oauth2_client.management.commands.oauth2_app_maker import Command as ParentCommand

try:
    from oauth2_provider.models import Application
except ImportError:
    # to be able to use the Client without `oauth2_provider` package installed
    Application = None


class Command(ParentCommand):
    """
    A command to create a new OAuth2 Application for oauth2_provider from CLI.
    Model imports are local, to keep it possible to run the Client without
    `oauth2_provider` package a

    Usage examples:
    python ./manage.py oauth2provider_app -h  # this help message

    python ./manage.py oauth2provider_app \\
        --name my_new_app \\
        --client-type  confidential \\
        --authorization-grant-type  client-credentials \\
        --redirect-uris 'https://xyz.com/callback' \\
        --verbosity 2
    """
    help = __doc__

    @classmethod
    def app_model(cls):
        """
        Application model type to be used
        """
        return Application

    def add_arguments(self, parser):
        """
        Arguments for fields we need populated in the resulting Application instance.
        Follow a convention that `argument name == model property name`
        """
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--client-type',
            choices=[c[0] for c in Application.CLIENT_TYPES],
            help='Oauth2 client type'
        )
        parser.add_argument(
            '--authorization-grant-type',
            choices=[g[0] for g in Application.GRANT_TYPES],
            help='Grant type'
        )
        parser.add_argument(
            '--skip-authorization',
            action="store_true",
            help='Skip authorization (default False)'
        )
        parser.add_argument(
            '--redirect-uris',
            help='Allowed redirect URIs, space-separated if more than one'
        )
