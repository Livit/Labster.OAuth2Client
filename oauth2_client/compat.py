"""
Support for python 2.7 and 3.x
"""
try:
    # python 3
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

try:
    # python 3
    from unittest.mock import patch
except ImportError:
    from mock import patch
