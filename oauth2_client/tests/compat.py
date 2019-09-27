"""
Support for python 2.7 and 3.x
"""
try:
    # python 3
    from unittest.mock import patch
except ImportError:
    from mock import patch
