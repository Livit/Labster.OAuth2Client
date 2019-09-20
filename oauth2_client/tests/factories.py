"""
Test factories for the application models.
"""
# pylint: disable=old-style-class
from factory.django import DjangoModelFactory


class ApplicationFactory(DjangoModelFactory):
    """
    Test factory for Application model.
    """
    class Meta:
        model = 'oauth2_client.Application'

    client_id = 'test'
    client_secret = 'my_secret'


class AccessTokenFactory(DjangoModelFactory):
    """
    Test factory for AccessToken model.
    """
    class Meta:
        model = 'oauth2_client.AccessToken'
