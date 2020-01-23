"""
Test cases for django model utils.

Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown.
"""
from random import randint

from oauth2_client.utils.django.model import help_text
from test_case import StandaloneAppTestCase


def test_model():
    """
    Get model class for tests. Implemented as a function to avoid global
    model import.
    """
    from django.db import models

    class SimpleModel(models.Model):
        class Meta:
            # random app_label prevents a warning saying that we register duplicated models
            app_label = 'test_app_{}'.format(randint(0, 100))

        my_property = models.CharField(
            help_text="good morning"
        )
        another_property = models.CharField()
    return SimpleModel


class TestModelUtils(StandaloneAppTestCase):
    """
    Test cases for django model utils.
    """

    def test_help_text(self):
        """
        Get help text from a django model's field.
        """
        actual = help_text('my_property', test_model())
        self.assertEqual(actual, "good morning")
