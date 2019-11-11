"""
Test runnner for oauth2_client.

Django versions:
We have services with different versions of Django:
Django > 1.1 for Simlic and >1.8 for License Service.
oauth2_code does have features that are mainly similar with regarding to these django versions.

Python versions:
We have services with different versions of Python:
Python 2.7 for Simlic and Python3 for License Service.
We have wrapper in `compat.py` that allows module to work in given python versions,
"""
import sys

from test_case import setup_django

setup_django()

try:
    # Django < 1.8
    from django.test.simple import DjangoTestSuiteRunner
    test_runner = DjangoTestSuiteRunner(verbosity=1)
except ImportError:
    # Django >= 1.8
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['oauth2_client'])
if failures:
    sys.exit(failures)
