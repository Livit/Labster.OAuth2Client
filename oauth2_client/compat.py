"""
Support for python 2.7 and 3.x and for multiple versions of Django.
"""
try:
    # python 3.x
    from urllib.parse import urljoin
except ImportError:
    # python 2.7
    from urlparse import urljoin


"""
`HelpTextFormatter` is a best-effort approach to provide readable formatting in
help messages of Django Commands. "Help message" is what you see when add `-h`
to Command invocation. This functionality is not essential, removal will not
break anything.
"""
from argparse import RawTextHelpFormatter  # noqa
try:
    #  available in newer versions of Django
    from django.core.management.base import DjangoHelpFormatter

    class HelpTextFormatter(RawTextHelpFormatter, DjangoHelpFormatter):
        """
        `RawTextHelpFormatter` - ensures new lines are respected in help strings
        `DjangoHelpFormatter` - ensures invocation options that are always added
            automatically by Django appear in the end of help message
        """
        pass
except ImportError:
    # NOTE: this can (and should) be removed once we drop support for Django 1
    class HelpTextFormatter(RawTextHelpFormatter):
        """
        `RawTextHelpFormatter` - ensures new lines are respected in help strings
        """
        pass
