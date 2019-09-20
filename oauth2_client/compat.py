"""
Support for python 2.7 and 3.x
"""
import sys

from django.conf import settings
from django.views.generic import View


# # django.contrib.postgres requires psycopg2
# try:
#     from django.contrib.postgres import fields as postgres_fields
# except ImportError:
#     postgres_fields = None

try:
    # python 3
    from mock import patch
except ImportError:
    from unittest.mock import patch
