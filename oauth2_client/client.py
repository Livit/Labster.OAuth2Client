"""
Service to service call with OAuth2 authentication.
"""
import time

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from oauth2_client.compat import urljoin
from .models import AccessToken, Application


# Used to prevent the token expiration when the request is processed on the server if the token is expiring in seconds
# or less at the client request time.
TIMEOUT_SECONDS = 60


class OAuth2Client(OAuth2Session):
    """
    OAuth2 client to make HTTP calls with OAuth2 token.

    Wrapper around OAuth2Session to cache saervice host on the class instatiation and use it to transform
    relative urls to absolute ones.

    Example:
        > # get OAuth2Client instance for the application
        > client = get_client('license')
        > # make API HTTP call by URL without host
        > r = client.get('/api/license/1/detail/')
    """

    def __init__(self, app, token):
        self.service_host = app.service_host  # used to transform relative URLs to absolute
        super(OAuth2Client, self).__init__(client_id=app.client_id, token=token)

    def request(self, method, url, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Intercepts all requests, transforms relative URL to absolute and add the OAuth 2 token if present.

        Arguments:
            method (str): HTTP method f.e. POST, GET.
            url (str): relative request URL.

        Returns:
            Response object.
        """
        absolute_url = urljoin(self.service_host, url)
        return super(OAuth2Client, self).request(method, absolute_url, *args, **kwargs)


def get_client(service_name):
    """
    Returns client to make HTTP requests with OAuth2 access token to the service with the given service_id.

    The access token is loaded from the database if there is an active (not expired) one. It's fetched from the
    provider service by HTTP and stored in the database otherwise.

    Arguments:
        service_name (str): name of the service make requests to f.e. licence.

    Returns:
        Ouath2 client to make HTTP requests.
        The client request could return HTTP 401 for expired token if the request takes too long, and the token
        is expired till the token check.
    """
    access_token = AccessToken.objects.filter(application__name=service_name).order_by('-created_at').first()
    if access_token is None or _expired(access_token.token):
        if access_token is not None:
            app = access_token.application
        else:
            app = Application.objects.get(name=service_name)
        token = _get_token(app)
        AccessToken.objects.create(application=app, token=token)
    else:
        app = access_token.application
        token = access_token.token

    return OAuth2Client(app, token)


def _expired(access_token):
    """
    Indicates if the given access token is almost expired (left less than TIMEOUT_SECONDS till expiration time).

    Arguments:
        access_token (object): oauth2_client.models.AccessToken instance.
    """
    return time.time() > access_token['expires_at'] - TIMEOUT_SECONDS


def _get_token(app):
    """
    Returns authentication token for service call.

    Arguments:
        app (oauth2_client.models.Application): Application settings.

    Returns:
        Access token (dict) used by oua2 client for HTTP calls.
    """
    client_id = app.client_id
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    kwargs = dict(scope=app.scope) if app.scope else {}
    return oauth.fetch_token(token_url=app.token_url, client_id=client_id, client_secret=app.client_secret, **kwargs)
