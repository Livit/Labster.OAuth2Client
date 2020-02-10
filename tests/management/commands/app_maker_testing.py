"""
Test-only extension of `oauth2_app_maker`, the abstract Django management
command that contains logic of create/update. In testing we use only very simple
Application models, defined in `tests/models.py`. This is to decouple tests
from specific Application classes we use in production. The `oauth2_app_maker`
doesn't care what Application model it works on.
"""
from oauth2_client.management.commands.oauth2_app_maker import Command as AbstractAppMaker


class Command(AbstractAppMaker):
    """
    Test-only simple `oauth2_app_maker` extension.
    """
    def app_model(self):
        # this will be mocked in tests
        pass

    def add_arguments(self, parser):
        # keep it simple
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--required-property',
        )
        parser.add_argument(
            '--optional-property',
        )
