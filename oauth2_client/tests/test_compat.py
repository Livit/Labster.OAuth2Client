"""
Support for python 2.7 and 3.x

To avoid install of test requirements in production.
"""
try:
    # python 3
    from unittest.mock import patch
except ImportError:
    from mock import patch
