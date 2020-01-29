"""
OAuth2 client models. Wherever applicable, field names and sizes are aligned
with `oauth2_provider's` ones, to ensure smooth interoperability.
"""
from datetime import timedelta

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import model_to_dict
from django.utils import timezone


class Application(models.Model):
    """
    Application model used by the Client
    """
    GRANT_CLIENT_CREDENTIALS = "client-credentials"
    GRANT_JWT_BEARER = "jwt-bearer"
    GRANT_TYPES = (
        (GRANT_CLIENT_CREDENTIALS, "Client credentials"),
        (GRANT_JWT_BEARER, "JWT bearer"),
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Application name"
    )
    client_id = models.CharField(
        max_length=100,
        help_text="ID string of the application"
    )
    client_secret = models.CharField(
        max_length=255,
        help_text="Secret string of this application"
    )
    authorization_grant_type = models.CharField(
        max_length=32,
        choices=GRANT_TYPES,
        help_text="The type of authorization grant to be used"
    )
    # URLField isn't used because it doesn't accept docker-to-docker domains
    service_host = models.CharField(
        max_length=200,
        help_text="Service host. For example: http://service-a:8000 or https://serive-a.labster.com"
    )
    token_uri = models.CharField(
        max_length=200,
        help_text="Token URL. For example: http://service-a:8000/o/token/"
    )
    scope = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Scope to be requested from provider, as a series of space delimited strings, "
                  "e.g. `read write`"
    )
    extra_settings = JSONField(
        default=dict,
        blank=True,
        help_text="Custom settings JSON string. For data that didn't fit anywhere else"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        """
        Returns the application name to show in the admin.
        """
        return self.name

    def __str__(self):
        return "<Application, name:{}, pk:{}>".format(self.name, self.pk)

    def validate_jwt_grant_data(self):
        """
        If JWT token bearer grant is used, subject has to be specified.
        Details: https://tools.ietf.org/html/rfc7523#section-3

        Returns:
            None:

        Raises:
            ValidationError: 1) when subject not specified
        """
        # noinspection PyUnresolvedReferences
        subject = self.extra_settings.get('subject')
        if self.authorization_grant_type == Application.GRANT_JWT_BEARER and not subject:
            msg = (
                "grant_type={} requires `subject` to be specified in app.extra_settings['subject']. "
                "See here for more information: https://tools.ietf.org/html/rfc7523#section-3"
                .format(Application.GRANT_JWT_BEARER)
            )
            raise ValidationError(msg)

    def clean(self):
        """
        Django hook to run model validation.

        Raises:
            ValidationError:
        """
        self.validate_jwt_grant_data()


class AccessToken(models.Model):
    """
    Access token to talk to the resource owner
    """

    # Used to prevent the token expiration when the request is processed on the resource owner side.
    # This value is simply subtracted from token's `expiry` when checking validity.
    TIMEOUT_SECONDS = 60.0

    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="The access_token as str"
    )
    raw_token = JSONField(
        default=dict,
        blank=True,
        help_text="Token JSON object returned from provider. This is for debugging purposes and can"
                  " be removed in the future."
    )
    token_type = models.TextField(
        help_text="Token type, most likely Bearer"
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE
    )
    expires = models.DateTimeField(
        blank=True,
        null=True
    )

    scope = models.TextField(
        blank=True,
        default="",
        max_length=100,
        help_text="Scope granted by provider, as a series of space delimited strings, "
                  "e.g. `read write`"
    )

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)

    def is_expired(self):
        """
        The token is expired when 1) expiration info available AND 2) expiration datetime is in the past.
        TIMEOUT_SECONDS margin is used to prevent token expiration issues during long-running
        requests.
        Apart from `expired`, the token could be `valid` or `unknown` (no expiration info available)

        Returns:
            bool: is token expired
        """
        # noinspection PyTypeChecker
        if self.expires and timezone.now() >= self.expires - timedelta(seconds=self.TIMEOUT_SECONDS):
            return True
        return False

    def to_client_dict(self):
        """
        Transform this AccessToken to a dict as expected by `OAuth2Session` class

        :return: dict
        """
        as_dict = model_to_dict(self, fields=["token", "token_type", "expires", "scope"])
        as_dict["access_token"] = as_dict.pop('token')
        if 'expires' in as_dict and as_dict['expires']:
            # expiry info can be used by oauth2_session (client's 3rd party parent class)
            expires_dt = as_dict.pop('expires')
            as_dict["expires_in"] = (expires_dt - timezone.now()).total_seconds()
        return as_dict

    def __unicode__(self):
        """
        Return the application name.
        """
        return "Access token for {}".format(self.application)

    def __str__(self):
        return "<AccessToken, pk:{}, for: {}>".format(self.pk, self.application)
