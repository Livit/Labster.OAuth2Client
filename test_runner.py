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
import django, sys

from django.conf import settings


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'oauth2_client',
    )
)

# Django 1.8
django.setup()
from django.test.runner import DiscoverRunner
test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['oauth2_client'])
if failures:
    sys.exit(failures)
