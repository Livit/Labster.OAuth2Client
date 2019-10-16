"""
Make migrations

Partly inspired by
https://stackoverflow.com/questions/37528286/how-to-make-migrations-for-a-reusable-django-app

Run as `python make_migrations.py` in venv with Django installed.
"""
import sys

from django.conf import settings

if __name__ == "__main__":
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'oauth2_client',
        )
    )
    from django.core.management import execute_from_command_line
    args = sys.argv + ["makemigrations", "oauth2_client"]
    execute_from_command_line(args)
