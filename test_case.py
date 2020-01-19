import os

import django
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase


def setup_django():
    if not settings.configured:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
        # https://docs.djangoproject.com/en/1.11/topics/settings/#calling-django-setup-is-required-for-standalone-django-usage
        django.setup()
        # convenience for IDE runs
        call_command('migrate')
    else:
        # this is the case when the tests are running in a context of some external django application, everything
        # is already set up so we don't have to do anything here
        pass


class StandaloneAppTestCase(TestCase):
    """
    This is project is django app without a django project.
    This class makes developers able to run test cases directly in their
    IDE, bypassing the `test_runner.py` script.
    This does NOT automate the posgres setup.
    """

    @classmethod
    def setUpClass(cls):
        setup_django()
        super(StandaloneAppTestCase, cls).setUpClass()
