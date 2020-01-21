[![Build Status](https://drone.labster.com/api/badges/Livit/Labster.OAuth2Client/status.svg)](https://drone.labster.com/Livit/Labster.OAuth2Client)

Extensive docs: [confluence](https://liv-it.atlassian.net/wiki/spaces/WEB/pages/891191387/OAuth2Client+documentation)

What is it
=====
It is a Django application without a full Django project.
This application enables authenticated communication between HTTP(s)-capable
clients and servers. Identification is by means of OAuth token. Tokens are
acquired by presentation of credentials, and may be refreshed by repeating
the authorization flow.

Supported grant types:
- Client Credentials - used for internal service-to-service communication. On the receiver
side there is a standard 3rd party oauth2_provider library from django-oauth-utils package.
- JWT Bearer - currently used for communication with Salesforce

Supported versions
------------------
Python 2.7 and Django 1.11,
Python 3.7 and Django 2.2

Python and Django compatibility is maintained in `compat.py` and `test_compat.py`

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

4. On the client side, create oauth2_client.Application model instance, and populate it.
You can get help by calling `python manage.py oauth2client_app -h` .

5. Instantiate the client via library calls, and use it for all api calls.


Test
----

#### automated tox run
- `pip install tox`
- get your test postgres instance running, see points below
- (optional, if you want custom settings) export variables for tox
- run `tox`

#### running tests in IDE (tested with Pycharm)
- run `make setup` - this creates a venv inside a `.venv` dir and installs basic dev dependencies
- run `pip install -r requirements/tox_requirements{27|37}.txt` depending on your version of python
- get your test postgres instance running, see points below
- point your IDE at `.venv` as the python installation to be used
- tests should work in the IDE

### More info
As it is a Django app without a Django project, custom `manage.py` created: `test_manage.py`. It is
a cut-down framework to provide sufficient Django context for testing and uses test settings file.
Without tox, to run tests, install requirements for needed python version(see `tox_requirements{27|37}txt`)
and then run `python test_manage.py test`. Test settings live in `test_settings.py`.
Tests use PostgresDb. See the `PostgreSQL` section for setup instructions.

#### Codestyle

Tox runs pycodestyle, but not pylint, because pylint checks for Django dependencies, which are not
part of this project.

### Nuances

#### PostgreSQL

##### Dockerized PostgreSQL setup
1. `make docker_setup`
2. `make start`

##### Quick standalone PostgreSQL setup
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
2. If tox does not get your code, delete ./.tox folder and sometimes .egg-info folder.

#### Coverage
If coverage is installed globally, it can take wrong version inside virtualenv, so better uninstall it.

### Migrations
To create migrations run ```python test_manage.py makemigrations```
