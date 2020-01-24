"""
OAuth2 client for following grant types:
- Client Credentials (e.g. service-to-service communication)
- JWT Bearer token (e.g. Salesforce)
"""
import logging
from datetime import timedelta

from django.utils import timezone
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session

from oauth2_client.compat import urljoin
from oauth2_client.fetcher import fetch_token
from oauth2_client.models import AccessToken, Application

log = logging.getLogger(__name__)


class OAuth2Client(OAuth2Session):
    """
    OAuth2 client to make authorized HTTP(S) requests with OAuth2 token.

    Wrapper around OAuth2Session to cache service host on the class instantiation and use it to transform
    relative urls to absolute ones.

    Example:
        > # get OAuth2Client instance for the application
        > client = get_client('license')
        > # make API HTTP call by URL without host
        > r = client.get('/api/license/1/detail/')
    """

    """
    If token re-fetch happens more than once in this period, raise an exception. Something is wrong,
    don't spam the provider.
    """
    REAUTH_LIMIT_SECONDS = 10

    def __init__(self, token, expired_callback=None):
        """
        Create OAuth2Client

        :param token: oauth2_client.model.AccessToken object
        :param expired_callback: (optional) function accepting one parameter, `Application`. It is
            called when TokenExpiredError is detected or 403 Forbidden status code received.
            It should return a valid (not expired) oauth2_client.model.AccessToken object for
            communication with Resource Owner specified by `Application`.
            Explanation: The parent class, OAuth2Session already implements automated token refresh,
            but their solution works only for flows that issue a refresh_token. Both currently
            supported flows, JWT and Client Credentials don't provide the refresh_token, so we have
            to handle the refresh ourselves. (Client Credentials MAY issue refresh_token but it
            doesn't in case of the `oauth2_provider` we use). If the token expiry is detected more
            than once within `REAUTH_LIMIT_SECONDS` period, `oauthlib.oauth2.TokenExpiredError`
            is raised (safety fuse approach).
        """
        self.app = token.application  # Application this client talks to
        self.last_token_fetch_time = None  # used for the safety fuse preventing too often re-authorization
        self.service_host = self.app.service_host  # used to transform relative URLs to absolute
        self.expired_callback = self._install_callback(expired_callback) if expired_callback else None
        super(OAuth2Client, self).__init__(client_id=self.app.client_id, token=token.to_client_dict())

    def _install_callback(self, expired_callback):
        """
        Wraps provided expiry callback into a safety fuse, so we won't spam the provider with token
        requests in case of problems with the client.

        :param expired_callback: a function taking one argument, `oauth2_client.models.Application`.
            It has to fetch and store new AccessToken.
        :return:  a wrapped callback function
        """
        def wrapped_callback(app):
            if self.last_token_fetch_time \
                    and self.last_token_fetch_time + timedelta(seconds=self.REAUTH_LIMIT_SECONDS) >= timezone.now():
                raise TokenExpiredError(
                    description="More than one token re-fetch attempt in %ss period. This means "
                                "either: 1) your authorization provider issues very short-living tokens, "
                                "you should raise the REAUTH_LIMIT_SECONDS value; 2) problem with the client"
                                % self.REAUTH_LIMIT_SECONDS
                )
            new_token = expired_callback(app)
            self.last_token_fetch_time = timezone.now()
            return new_token

        return wrapped_callback

    def request(self, method, url, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Intercepts all requests, transforms relative URL to absolute and add the OAuth 2 token if present.

        Arguments:
            method (str): HTTP method f.e. POST, GET.
            url (str): relative request URL.

        Returns:
            Response object.

        Raises:
            TokenExpiredError: 1) when token expiry detected and `expired_callback` not specified;
                2) when 403 Forbidden status code received and `expired_callback` not specified;
                3) when `expired_callback` is specified and more than one token re-fetch happens
                within `REAUTH_LIMIT_SECONDS` period.
        """
        absolute_url = urljoin(self.service_host, url)
        try:
            # super().request may raise `TokenExpiredError`
            resp = super(OAuth2Client, self).request(method, absolute_url, *args, **kwargs)
            if resp.status_code == 403:
                raise TokenExpiredError(description="403 Forbidden status code response received")
            else:
                return resp
        except TokenExpiredError:
            log.debug("Access Token for app=%s expired.", self.app.name)
            if not self.expired_callback:
                raise
            new_token = self.expired_callback(self.app)
            self.token = new_token.to_client_dict()
            log.debug("Obtained new token. Retrying request.")
            return self.request(method, url, *args, **kwargs)


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

    return OAuth2Client(token, expired_callback=fetch_and_store_token)


def fetch_and_store_token(app):
    """
    Obtain a new token from auth provider and store in database.

    Arguments:
        app (oauth2_client.models.Application): oauth application instance

    Returns:
        oauth2_client.models.AccessToken: access token
    """
    token = fetch_token(app)
    token.save()
    return token
