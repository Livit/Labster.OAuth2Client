"""
BaseCommand extension adding logger.
"""
import logging

from django.core.management import BaseCommand

from oauth2_client.compat import HelpTextFormatter


class LoggingBaseCommand(BaseCommand):
    """
    Extends BaseCommand with a logger whose level is
    set from the `--verbosity` option.

    Verbosity to log level mapping:
    0: error
    1: warning (default)
    2: info
    3: debug
    """

    def __init__(self, log_name=None, mapping=None, *args, **kwargs):
        BaseCommand.__init__(self, *args, **kwargs)
        if mapping is None:
            lg = logging
            mapping = [lg.ERROR, lg.WARNING, lg.INFO, lg.DEBUG]
        self.mapping = mapping
        self.logger = logging.getLogger(log_name or self.__class__.__name__)

    def create_parser(self, *args, **kwargs):
        """
        Enable multiline command help text.
        https://stackoverflow.com/questions/35470680/django-command-how-to-insert-newline-in-the-help-text
        """
        parser = BaseCommand.create_parser(self, *args, **kwargs)
        parser.formatter_class = HelpTextFormatter
        return parser

    def execute(self, *args, **options):
        verbosity = self.mapping[int(options["verbosity"])]
        self.logger.setLevel(verbosity)
        return super(LoggingBaseCommand, self).execute(*args, **options)
