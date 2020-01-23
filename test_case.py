"""
Parent test case class for Django Applications that live without a parent
Django project. Provides developers with ability to run unit tests within IDE.
(Tested with Pycharm). Tests ran in already existing django context are not
affected. (e.g. tox, manage.py)

Implementation is loosely based on:
# https://docs.djangoproject.com/en/1.11/topics/settings/#calling-django-setup-is-required-for-standalone-django-usage
"""
import os

import django
from django.conf import settings
from django.test import TestCase


def setup_django():
    if not settings.configured:
        # This is the case when we run tests from IDE (e.g. the green `play`
        # button in Pycharm), we need to set up in-memory django instance, so
        # the tested app runs within its context.
        os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
        django.setup()
    else:
        # This is the case when the tests are running in a context of some
        # external django application, everything is already set up so we
        # don't have to do anything here. This is the case when you run
        # `./manage.py test` or use `tox`
        pass


class StandaloneAppTestCase(TestCase):
    """
    Parent test case class for apps that don't belong to any django projects,
    e.g. oauth2_client. This class makes developers able to run test cases
    directly in their IDE. This does NOT automate the DB setup, neither generates
    nor applies your migrations.
    """

    @classmethod
    def setUpClass(cls):
        setup_django()
        super(StandaloneAppTestCase, cls).setUpClass()
