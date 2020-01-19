"""
Support for python 2.7 and 3.x
"""
try:
    # python 3
    from urllib.parse import urljoin, urlsplit
except ImportError:
    # python 2.7
    from urlparse import urljoin, urlsplit
