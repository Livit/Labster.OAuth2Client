Oauth2 client
=====

It is a Django app for service-to-service communcation.

There is proper wiki page in Service-Ready setup project explaining idea behind it.

Basically it is client to make requests from one service to another.

On the reciever side, there is standard 3rd party oauth2 provider library.

Versions
--------
This repository supports 2.7 and 3.x versions via compat files.

Simlic and region service use python 2.7
License Service and other CoockieCutter template services use python 3.


Quick start
-----------

0. In requirements, add `pip install git+https://git@github.com/Livit/Labster.oauth2_client.git`

1. Add "oauth2_client" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'oauth2_client',
    ]

2. Run `make simlic_manage migrate` to create the oauth2_client models.

3. On the receiver side, create Application model and fill with proper data:

    name="Client name",
    redirect_uris="http://localhost",  # for local development
    client_type=Application.CLIENT_CONFIDENTIAL,
    authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,

4. On the client side, put client and secret from receiver side in .env and instantiate client via library calls, and use it for all api calls.


Test
----
Inspiration: https://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app
As it is Django app without Django project, custom test runnner created: `test_runnner.py`
to run tests, install requirements and then `python test_runnner.py`
Note, to install psycopg2 you need install special packages on Ubuntu and on Mac: http://initd.org/psycopg/docs/install.html
If for mac you will see `ld: library not found for -lssl`, then ` brew upgrade openssl`
and
`export CPPFLAGS="-I/usr/local/opt/openssl/include"`
`export LDFLAGS="-L/usr/local/opt/openssl/lib"`

Test use PostgresDb. Install postgres, create db, put its settings into test_settings.py
If you want, you can set
`export PGDATA='full-path-to/Labster.oauth2_client/psql_data'`
init_db
pg_ctl -D /Users/kry/repos/labster/Labster.oauth2_client/psql_data -l logfile start
createdb "test_oauth2_client"
(So you can ` psql -U your_shell_user test_oauth2_client`)
Then fill data in settings file, just change your user name.
Do not forget to stop pg_ctl when tests ends.




Using tox:
==========
1. Probably do not run tox from virtualenv
2. If tox does not gets your code, delete ./.tox folder

