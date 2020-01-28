"""
HTTP(S) Session client, capable of running an OAuth2 authentication flow to
obtain a token from an authorization provider.

Enables authenticated communication between HTTP(s)-capable clients and servers.
Identification is by means of OAuth token. Tokens are acquired by presentation
of credentials, and may be refreshed by repeating the authorization flow.

Supported OAuth2 grant types:
- Client Credentials (e.g. service-to-service communication)
- JWT Bearer token (e.g. Salesforce)
"""
import logging

import pybreaker
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session

from oauth2_client.compat import urljoin
from oauth2_client.fetcher import fetch_token
from oauth2_client.models import AccessToken, Application

log = logging.getLogger(__name__)

# Protect integration point with authorization provider
token_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

# Protect integration point with communication receiver (resource owner)
request_breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=10)


class OAuth2Client(OAuth2Session):
    """
    OAuth2 client to make authorized HTTP(S) requests with OAuth2 token.

    Wrapper around OAuth2Session to cache service host on the class instantiation and use it to transform
    relative urls to absolute ones.

    Expired OAuth2 token can be refreshed by repeating the authorization flow. Token refresh
    functionality is protected with circuit breakers, to avoid spamming authorization provider
    and resource owner in case of system failure. Token expiry detection uses best-effort approach,
    as there is no standardized way of informing the client of token expiry. The mechanism tries
    to fetch new token and retries the request once. If unsuccessful - CircuitBreakerError is raised.

    Explanation:
        The parent class, OAuth2Session already implements automated token refresh,
        but their solution works only for flows that issue a refresh_token. Both currently
        supported flows, JWT and Client Credentials don't provide the refresh_token, so we have
        to handle the refresh ourselves. (Client Credentials MAY issue refresh_token but it
        doesn't in case of the `oauth2_provider` we use).

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

    @request_breaker
    def make_request(self, method, url, *args, **kwargs):
        """
        Make HTTP(S) request. Make best effort to detect token expiry.

        Two mechanisms are used for expiry detection:
        1) check expiration datetime on the token itself. This is baked into the call to 3rd party's
            super().request. Tokens are not guaranteed to contain this information.
        2) interpret 4xx status code received as token expiry error. Based on discussion in
            referenced thread.

        Reference:
            > Since different services can use different error codes for expired tokens,
            > you can either keep track of the code for each service or an easy way to
            > refresh tokens across services is to simply try a single refresh upon encountering
            > a 4xx error.
            Source: https://stackoverflow.com/questions/30826726/how-to-identify-if-the-oauth-token-has-expired

        Raises:
            TokenExpiredError: upon token expiry detection
        """
        resp = super(OAuth2Client, self).request(method, url, *args, **kwargs)
        if 400 <= resp.status_code < 500:
            raise TokenExpiredError(description="4xx status code received. Assuming expired token.")
        return resp

    def request(self, method, url, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Intercepts all requests, transforms relative URL to absolute and add the OAuth 2 token if present.

        Arguments:
            method (str): HTTP method f.e. POST, GET.
            url (str): relative request URL.

        Returns:
            Response object.

        Raises:
            CircuitBreakerError:
                1) token re-fetch circuit opens due to failure threshold reached;
                2) request circuit opens due to failure threshold reached;
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

    The client may occasionally return HTTP 401 when token expires during request processing on
    Resource Owner side.

    Arguments:
        app_name (str): name of the OAuth client application to make requests to f.e. license.

    Returns:
        client (oauth2_client.OAuth2Client): OAuth2 client for authenticated HTTP(S) communication
    """
    token = AccessToken.objects.filter(application__name=app_name).order_by('-created').first()
    if not token or token.is_expired():
        app = token.application if token else Application.objects.get(name=app_name)
        token = fetch_and_store_token(app)
    return OAuth2Client(token)


@token_breaker
def fetch_and_store_token(app):
    """
    Obtain a new token from auth provider and store in database.

    Arguments:
        app (oauth2_client.models.Application): oauth application instance

    Returns:
        oauth2_client.models.AccessToken: access token

    Raises:
        KeyError: when Fetcher is unable to parse received data as an AccessToken
    """
    token = fetch_token(app)
    token.save()
    log.debug('Fetched and stored %s', token)
    return token
