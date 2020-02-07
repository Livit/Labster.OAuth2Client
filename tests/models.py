"""
Test Application models used for `test_oauth2maker_cmd.py`
"""
from django.db import models


class TestApplication(models.Model):
    """
    Application model used for testing.
    """
    name = models.CharField(unique=True, max_length=255)
    required_property = models.CharField(max_length=50)
    optional_property = models.CharField(blank=True, max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class TestApplicationNoUnique(models.Model):
    """
    Application model used for testing. Does not define unique constraint on the `name` field.
    `oauth2_provider.Application` does the same, we need to handle this case.
    """
    name = models.CharField(max_length=255)
    required_property = models.CharField(max_length=50)
    optional_property = models.CharField(blank=True, max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class NoRequiredFieldsApp(models.Model):
    """
    Used to test model validation.
    """


class NameNotMandatoryApp(models.Model):
    """
    To ensure the commands will not create application without name.
    """
    name = models.CharField(max_length=50, blank=True)
    updated = models.DateTimeField(auto_now=True)
