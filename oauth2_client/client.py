"""
HTTP(S) Session client, capable of running an OAuth2 authentication flow to
obtain a token from an authorization provider.

Supported OAuth2 grant types:
- Client Credentials (e.g. service-to-service communication)
- JWT Bearer token (e.g. Salesforce)

Enables authenticated communication between HTTP(s)-capable clients and servers.
Identification is by means of OAuth token. Tokens are acquired by presentation
of credentials, and are refreshed by repeating the authorization flow, when
token expiry detected. See the docstrings for details on token expiry detection
and design choices. Token refresh mechanism is transparent to the code using the
OAuth2Client.

The OAuth2Client utilizes a circuit breaker pattern, to avoid spamming
communication receiver upon an unexpected system failure on either side.
The circuit breaker resets 10s after a failure and the client code can resume
communication attempts. Circuit breakage indicates a failure by raising a
`CircuitBreakerError`.

Token refresh algorithm:
1) token expiry detected, request failed
2) fetch and store a new token (this may be internally repeated too, 1 error is allowed)
3) repeat the request once
4) if the request still fails (for whatever reason): break the circuit

Any exception from the 3rd party code handling the request will also cause the
breaker to open the circuit.
"""
import logging

import pybreaker
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session
from retrying import retry

from oauth2_client.compat import urljoin
from oauth2_client.fetcher import fetch_token
from oauth2_client.models import AccessToken, Application

log = logging.getLogger(__name__)


# Protect integration point with resource owner and authorization provider
request_breaker = pybreaker.CircuitBreaker(fail_max=1, reset_timeout=10)


class OAuth2Client(OAuth2Session):
    """
    OAuth2 client to make authorized HTTP(S) requests with OAuth2 token.

    Wrapper around OAuth2Session to cache service host on the class instantiation and use it to
    transform relative urls to absolute ones.

    Expired OAuth2 token are refreshed by repeating the authorization flow.

    Why implement custom token refresh mechanism:
        The parent class, OAuth2Session already implements automated token refresh,
        but their solution works only for flows that issue a refresh_token. Both currently
        supported flows, JWT and Client Credentials don't provide the refresh_token, so we have
        to handle the refresh ourselves. (Client Credentials MAY issue refresh_token but it
        doesn't in case of the `oauth2_provider` we use as a reference auth provider).

    Example:
        > # get OAuth2Client instance for the application
        > client = get_client('license')
        > # make API HTTP call by URL without host
        > r = client.get('/api/license/1/detail/')
    """
    def __init__(self, token):
        """
        Create OAuth2Client

        :param token: oauth2_client.model.AccessToken
        """
        self.app = token.application  # Application this client talks to
        self.service_host = self.app.service_host  # used to transform relative URLs to absolute
        super(OAuth2Client, self).__init__(client_id=self.app.client_id, token=token.to_client_dict())

    def make_request(self, method, url, *args, **kwargs):
        """
        Make HTTP(S) request. Make best effort to detect token expiry.

        Two mechanisms are used for expiry detection:
        1) `oauth_provider`: check expiration datetime on the token itself. This is baked into
            the call to 3rd party's `super().request`. Other tokens are not guaranteed to contain
            this information.
        2) Salesforce: interpret 400 status code along with `invalid_grant` error as token expiry

        Raises:
            TokenExpiredError: upon token expiry detection
        """
        # 1 oauth_provider
        resp = super(OAuth2Client, self).request(method, url, *args, **kwargs)
        # 2 salesforce
        if self.app.authorization_grant_type == Application.GRANT_JWT_BEARER and is_invalid_jwt_grant(resp):
            raise TokenExpiredError(description="400 status code received in JWT flow. Assuming expired token.")
        return resp

    @request_breaker
    def request(self, method, url, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Intercepts all requests, transforms relative URL to absolute and add the OAuth 2 token if present.
        Any communication issues are indicated by raising `CircuitBreakerError`. In this case communication
        can be reattempted in 10s, after the breaker resets.

        Arguments:
            method (str): HTTP method e.g. POST, GET.
            url (str): relative request URL.

        Returns:
            Response object.

        Raises:
            CircuitBreakerError:
                1) token expiry was detected and new token fetched, but we still get errors in
                    communication upon retrying request
                2) any unexpected error when handling the request
        """
        absolute_url = urljoin(self.service_host, url)
        try:
            return self.make_request(method, absolute_url, *args, **kwargs)
        except TokenExpiredError:
            log.debug("Attempting to fetch a new token for %s", self.app)
            new_token = fetch_and_store_token(self.app)
            self.token = new_token.to_client_dict()
            return self.make_request(method, absolute_url, *args, **kwargs)


def get_client(app_name):
    """
    Returns HTTP(S) client for authenticated communication with Resource Owner specified by the
    `app_name` parameter. Identification is by means of OAuth token.

    The access token is loaded from the database, if there is a valid one.
    Otherwise - new token is fetched from the auth provider by HTTP(S) and stored in the database.
    The new token is then used for communication. Tokens are automatically refreshed by repeating
    the authorization flow.

    Arguments:
        app_name (str): name of the OAuth client application to make requests to e.g. license.

    Returns:
        client (oauth2_client.OAuth2Client): OAuth2 client for authenticated HTTP(S) communication
    """
    token = AccessToken.objects.filter(application__name=app_name).order_by('-created').first()
    if not token or token.is_expired():
        app = token.application if token else Application.objects.get(name=app_name)
        token = fetch_and_store_token(app)
    return OAuth2Client(token)


@retry(wait_fixed=2000, stop_max_attempt_number=2)
def fetch_and_store_token(app):
    """
    Obtain a new token from auth provider and store in database. If unable to
    parse received data as an AccessToken - wait 2s and try to fetch again. If
    still unable - raise KeyError.

    Arguments:
        app (oauth2_client.models.Application): oauth application instance

    Returns:
        oauth2_client.models.AccessToken: access token

    Raises:
        KeyError:
    """
    token = fetch_token(app)
    token.save()
    log.debug('Fetched and stored %s', token)
    return token


def is_invalid_jwt_grant(resp):
    """
    Detect invalid OAuth 2.0 JWT token response returned from Salesforce (e.g. expired token)

    Reference:
        https://help.salesforce.com/articleView?id=remoteaccess_oauth_flow_errors.htm&type=5
    """
    if resp.status_code == 400 \
            and resp.headers.get('content-type') == 'application/json' \
            and resp.json().get('error') == 'invalid_grant':
        return True
    return False
