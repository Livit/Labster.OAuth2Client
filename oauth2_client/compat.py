"""
Support for python 2.7 and 3.x
"""
import sys

from django.conf import settings
from django.views.generic import View


try:
    # python 3
    from unittest.mock import patch
except ImportError:
    from mock import patch


try:
    # python 3
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
