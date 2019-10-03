"""
Ouath2 client models.
"""
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone


class Application(models.Model):
    """
    Client credentials for the service provider.
    """
    name = models.CharField(max_length=50, help_text="Example: licence")
    # base definitions copied from oauth2_provider.Application
    client_id = models.CharField(max_length=100)
    client_secret = models.CharField(max_length=100)
    # URLField isn't used because it doesn't accept docker-to-docker domains
    service_host = models.CharField(
        max_length=200,
        help_text="Service host. For example: http://service-a:8000 or https://serive-a.labster.com")
    # URLField isn't used because it doesn't accept docker-to-docker domains
    token_url = models.CharField(
        max_length=200,
        help_text="Token URL. For example: http://service-a:8000/o/token/"
    )

    scope = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Custom permissions string. Empty value is allowed, and set by default."
    )

    updated_at = models.DateTimeField(auto_now=timezone.now)
    created_at = models.DateTimeField(auto_now_add=timezone.now)

    def __unicode__(self):
        """
        Returns the application name to show in the admin.
        """
        return self.name


class AccessToken(models.Model):
    """
    Access token for the service provider.
    """
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    # store in JSON because OAuth2Session and BackendApplicationClient require it in this format
    token = JSONField()
    created_at = models.DateTimeField(auto_now_add=timezone.now, db_index=True)

    def __unicode__(self):
        """
        Return the application name.
        """
        return "Access token for {}".format(self.application)
