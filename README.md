[![Build Status](https://drone.labster.com/api/badges/Livit/Labster.OAuth2Client/status.svg)](https://drone.labster.com/Livit/Labster.OAuth2Client)

What is it
=====

It is a Django app for service-to-service communication, a client to make requests from one service to another.
On the receiver side, there is standard 3rd party oauth2_provider library.

Versions
--------
Python 2.7 and Django 1.11,
Python 3.7 and Django 2.2

Python and Django compatibility is maintained in `compat.py` and `test_runner.py`

Quick start
-----------

0. In requirements, add `pip install git+https://git@github.com/Livit/Labster.OAuth2Client.git@0.1.3`

1. Add "oauth2_client" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'oauth2_client',
    ]

2. Run migrate to create the oauth2_client models.

3. On the receiver side, create Application model and fill with proper data:

    {
        name="Client name",
        redirect_uris="http://localhost",  # for local development
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    }

4. On the client side, put client and secret from receiver side in .env and instantiate client via library calls, and use it for all api calls.


Test
----
- Create .env file with following data (feel free to change as rquired):
```shell script
export POSTGRES_DB=test
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testPass
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5435
```

- pip install tox
- get your test postgres instnce running, see points below
- source .env
- tox

### More info
As it is Django app without Django project, custom test runnner created: `test_runnner.py`
Without tox, to run tests, install requirements from needed python version (see `tox_requirements....txt`) and then `python test_runnner.py`. Inspiration: https://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app

Tests use PostgresDb. Install postgres, create db, put its settings into test_runnner.py

#### Codestyle

Tox runs pycodestyle, but not pylint, because pylint checks for Django dependencies, which are not part of this project.

### Nuances

#### PostgreSQL

##### Dockerized PosgreSQL setup
1. remember to fill out your .env file
3. run `./test_run_postgres.sh`

##### Quick standalone PostreSQL setup
To install `psycopg2` you need install special packages on Ubuntu and on Mac: http://initd.org/psycopg/docs/install.html

If on mac you will see `ld: library not found for -lssl`, then `brew upgrade openssl`
and `export CPPFLAGS="-I/usr/local/opt/openssl/include"`, `export LDFLAGS="-L/usr/local/opt/openssl/lib"`.

1. You can set `export PGDATA='full-path-to/Labster.oauth2_client/psql_data'`
2. init_db
3. pg_ctl -D /Users/kry/repos/labster/Labster.oauth2_client/psql_data -l logfile start
4. createdb "test_oauth2_client"
5. check : `psql -U your_shell_user test_oauth2_client`
6. Then fill data in settings file, just change your user name.
7. `stop pg_ctl` when tests ends.


#### Using tox
1. Do not run tox from virtualenv
2. If tox does not gets your code, delete ./.tox folder and sometimes .egg-info folder.

#### Coverage
If coverage is installed globally, it can take wrong version inside virtualenv, so better uninstall it.

### Migrations
To create migrations run ```python make_migrations.py```
