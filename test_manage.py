#!/usr/bin/env python
"""
An equivalent of `manage.py` to be used for development and testing.
The name is prefixed with `test_` on purpose, to emphasize this is NOT a full Django project.

For example:
python ./test_manage.py makemigrations

python ./test_manage.py migrate

python ./test_manage.py test oauth2_client

python ./test_manage.py oauth2client_app \
    --name my_test_app2 \
    --client-id "my-app-id-string" \
    --client-secret "/certs/my_app_cert.key" \
    --authorization-grant-type  jwt-bearer \
    --service-host 'https://labster--Lightning.cs129.my.salesforce.com' \
    --token-uri 'https://login.salesforce.com/services/oauth2/token' \
    --scope 'read' \
    --extra-settings='{"subject": "xyz@labster.com.lightning"}' \
    -v 2
"""
import os
import sys

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
