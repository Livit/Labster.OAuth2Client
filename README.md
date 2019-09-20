=====
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



