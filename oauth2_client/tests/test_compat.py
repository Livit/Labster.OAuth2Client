"""
Support for python 2.7 and 3.x
"""
try:
    # python 3.x
    from unittest.mock import Mock, patch
except ImportError:
    # python 2.7
    from mock import Mock, patch
