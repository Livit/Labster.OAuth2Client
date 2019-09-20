DEBUG=False,
DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test_oauth2_client',
        'USER': 'kry',
        'PASSWORD': '',
        'HOST': 'localhost',
        'POST': '5435'
    }
},
INSTALLED_APPS=(
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.admin',
    'oauth2_client',
)
SECRET_KEY = 'test'
