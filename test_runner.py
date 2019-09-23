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
import django, sys, os

from django.conf import settings


# read from env and set in tox.
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['POSTGRES_DB'],
            'USER': os.environ['POSTGRES_USER'],
            'PASSWORD': os.environ['POSTGRES_PASSWORD'],
            'HOST': os.environ['POSTGRES_HOST'],
            'POST': os.environ.get('POSTGRES_PORT', '5432')
        }
    },
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'oauth2_client',
    )
)

try:
    # Django < 1.8
    from django.test.simple import DjangoTestSuiteRunner
    test_runner = DjangoTestSuiteRunner(verbosity=1)
except ImportError:
    # Django >= 1.8
    django.setup()
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['oauth2_client'])
if failures:
    sys.exit(failures)
