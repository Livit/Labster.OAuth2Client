"""
Django settings used for testing and development.
"""
import logging
import os

# log only errors and warnings in testing. We want clean output.
logging.disable(logging.INFO)

# allow HTTP for OAuth in testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SECRET_KEY = 'psst'

DEBUG = True
USE_TZ = True

"""
Defaults are used when running from the IDE.
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', 'test'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'testPass'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5445')
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'oauth2_provider',  # not needed in production, unless you need to create provider's Applications
    'oauth2_client',
    'tests',  # https://docs.djangoproject.com/en/1.11/topics/testing/advanced/#testing-reusable-applications
)
