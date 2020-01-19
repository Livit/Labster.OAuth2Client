"""
Django admin for OAuth2 client models.
"""
from django.contrib import admin

from .models import AccessToken, Application


class ApplicationAdmin(admin.ModelAdmin):
    """
    Admin support for Application model.
    """
    list_display = ("name", )


class AccessTokenAdmin(admin.ModelAdmin):
    """
    Admin support for AccessToken model.
    """
    list_display = ("application", "created")


admin.site.register(Application, ApplicationAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
