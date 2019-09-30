"""
Support for python 2.7 and 3.x
"""
try:
    # python 3
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
