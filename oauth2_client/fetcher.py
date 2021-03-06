"""
Components used to fetch (obtain) an OAuth2 token from authorization provider.
Fetcher owns authorization flow logic. An `Application` object is bound to a
fetcher and used as a source of credentials.

Supported grant types:
- Client Credentials (e.g. service-to-service communication)
- JWT Bearer token (e.g. Salesforce)

NOTE: by `Application` or `App` we mean an OAuth application and its
    representation in the database, NOT a Django application.
    See here: https://django-oauth-toolkit.readthedocs.io/en/latest/glossary.html#application
"""
import json
import logging
from base64 import urlsafe_b64encode
from datetime import timedelta

import pytz
import requests
from django.utils import timezone
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from oauth2_client.compat import urlsplit
from oauth2_client.models import AccessToken, Application
from oauth2_client.utils.crypto import sign_rs256
from oauth2_client.utils.date_time import datetime_to_float, float_to_datetime

log = logging.getLogger(__name__)


def fetch_token(app):
    """
    Obtain a token from auth provider, using a fetcher specific to application's grant type.

    Args:
        app (oauth2_client.models.Application): app instance you need a token for

    Returns:
        oauth2_client.models.AccessToken: obtained token
    """
    fetcher_grant_dispatcher = {
        Application.GRANT_CLIENT_CREDENTIALS: ClientCredentialsFetcher,
        Application.GRANT_JWT_BEARER: JWTFetcher,
    }
    fetcher = fetcher_grant_dispatcher[app.authorization_grant_type](app)
    return fetcher.fetch_token()


class Fetcher:
    """
    Abstract token Fetcher for all supported grant types.
    Fetch OAuth token from auth provider and return as `oauth2_client.models.AccessToken` object.
    Specific type of fetcher is derived from `app.authorization_grant_type`

    You don't have to use this class directly, use the `fetch_token(app)` function instead.
    """

    def __init__(self, app):
        """
        Construct Fetcher.

        Args:
            app (oauth2_client.models.Application): app instance the Fetcher uses
        """
        self.app = app

    def fetch_token(self):
        """
        Top-level method, that runs the auth flow and returns the token. This is most likely
        what you are looking for.

        Returns:
            oauth2_client.models.AccessToken:
        """
        raw_token = self.fetch_raw_token()
        return self.access_token_from_raw_token(raw_token)

    def fetch_raw_token(self):
        """
        Fetch a token from auth provider. Exact object type and available properties are
        provider specific.
        """
        raise NotImplementedError('Subclasses of Fetcher must implement fetch_raw_token() method.')

    def access_token_from_raw_token(self, raw_token):
        """
        Parse provider-specific `raw_token` to `AccessToken`. Provider-specific logic
        is accounted for in utility functions used for parsing.

        Args:
            raw_token (OAuth2Token(dict) or plain dict): token returned from auth provider

        Returns:
            oauth2_client.models.AccessToken: token in standardized format

        Raises:
            KeyError: When the data received from auth server does not contain access token.
                This probably means authentication issues on our side, e.g. bad auth request.
        """
        try:
            return AccessToken(
                application=self.app,
                token=raw_token['access_token'],
                scope=self.received_scope(raw_token),
                raw_token=raw_token,
                token_type=raw_token['token_type'],
                expires=expiry_date(raw_token),
            )
        except KeyError:
            log.error(
                'Error when parsing an access token obtained from auth provider. This can mean: '
                '1) temporary issues, try again just in case; 2) auth provider has changed '
                'specification - this can require logic changes on our side. Data received: %s',
                raw_token
            )
            raise

    def requested_scope(self):
        """
        Get the scope to be requested from the provider in the auth flow.
        """
        scope = self.app.scope
        return scope.split() if scope else []

    def received_scope(self, token, default=""):
        """
        Extract scope granted by the provider from the token. The RFC isn't
        strict about the scope, so aren't we.

        Reference:
            > The authorization server MAY fully or partially ignore the scope
            > requested by the client, based on the authorization server policy or
            > the resource owner's instructions.  If the issued access token scope
            > is different from the one requested by the client, the authorization
            > server MUST include the "scope" response parameter to inform the
            > client of the actual scope granted.
            Source: https://tools.ietf.org/html/rfc6749#page-23

        Args:
            token: token object or dict returned from auth provider
            default: value to return when no scope info found

        Returns:
            str: scope as one string or default
        """
        # This accounts for all required cases and assigns a default properly,
        # don't change unless real issues caused.
        received = getattr(token, "scope", None)
        if received is None:
            received = token.get('scope', default)

        # check if we got what we asked for
        requested_list = self.requested_scope()
        requested_set = set(requested_list)
        received_set = set(received.split())
        if requested_set != received_set:
            log.warning(
                'Received different scope than requested. Requested: %s, received: %s. '
                'Just a heads-up, ignore this unless you are debugging permission issues.',
                requested_list, received.split()
            )

        return received


class JWTFetcher(Fetcher):
    """
    Token fetcher for the JWT token bearer flow.
    See for more: https://tools.ietf.org/html/rfc7523
    """

    def fetch_raw_token(self):
        """
        Fetch token using JWT Bearer flow.

        Returns:
            dict: raw token from provider

        Raises:
            ValidationError: if the Application object we are fetching token
                for doesn't provide all required input data
            RequestException: from `requests` library
            JSONDecodeError: unparseable data received
        """
        self.app.validate_jwt_grant_data()
        payload = self.auth_payload()
        response = requests.post(self.app.token_uri, data=payload)
        data = json.loads(response.text)
        return data

    def auth_payload(self):
        """
        Prepare authorization request payload according to RFC 7523.
        Generated claim has to be signed using RSA with SHA256.
        Application's X509 certificate's key is used as the signing key.
        Key's location is specified in `Application.client_secret` and has
        to be available for reading on the server machine.

        Returns:
            dict: payload as a dict
        """
        claim = self.jwt_claim()
        claim_signature = sign_rs256(claim.encode(), self.app.client_secret)
        claim_signature = urlsafe_b64encode(claim_signature).decode()

        auth_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": claim + "." + claim_signature
        }
        return auth_payload

    def jwt_claim(self, expiration_s=150):
        """
        Build a JWT claim used to obtain token from auth provider.
        Logic and naming explained here:
        https://help.salesforce.com/articleView?id=remoteaccess_oauth_jwt_flow.html
        https://tools.ietf.org/html/rfc7523

        Args:
            expiration_s (int): value for `exp` claim field. Per RFC has to be <= 180s

        Returns:
            str: claim as base64 string
        """
        claim = urlsafe_b64encode('{"alg":"RS256"}'.encode()).decode()
        claim += "."
        expiration_ts = int(datetime_to_float(timezone.now() + timedelta(seconds=expiration_s)))
        claim_template = '{{"iss": "{iss}", "sub": "{sub}", "aud": "{aud}", "exp": {exp}}}'
        payload = claim_template.format(
            iss=self.app.client_id,  # issuer
            sub=self.app.extra_settings['subject'],
            aud=self._audience(),
            exp=expiration_ts
        )
        log.debug("JWT flow claim payload: %s", payload)
        claim += urlsafe_b64encode(payload.encode()).decode()
        return claim

    def _audience(self):
        """
        Dynamically derive claim audience (`aud:`) from `app.token_uri`.

        E.g. https://login.salesforce.com/services/oauth2/token -> https://login.salesforce.com
        """
        scheme, netloc, _, _, _ = urlsplit(self.app.token_uri)
        return "{}://{}".format(scheme, netloc)


class ClientCredentialsFetcher(Fetcher):
    """
    Token fetcher for Client Credentials flow (AKA Backend Application flow).
    See for more: https://oauthlib.readthedocs.io/en/latest/oauth2/grants/credentials.html
    """

    def fetch_raw_token(self):
        """
        Fetch token using Client Credentials Flow

        Returns:
            dict: raw token from provider
        """
        client = BackendApplicationClient(client_id=self.app.client_id)
        oauth = OAuth2Session(client=client)
        return oauth.fetch_token(
            token_url=self.app.token_uri,
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            scope=self.requested_scope()
        )


def expiry_date(raw_token):
    """
    Determine token's expiry date if available. The RFC isn't strict about this,
    so aren't we. JWT Bearer grant type doesn't return expiration info at all.

    The preference of the source of this data is:
        1. `expires_in`, interpreted as seconds from now
        2. `expires_at`, interpreted as a timestamp from epoch in UTC

    From RFC:
        > expires_in
        >   RECOMMENDED.  The lifetime in seconds of the access token.  For
        >   example, the value "3600" denotes that the access token will
        >   expire in one hour from the time the response was generated.
        >   If omitted, the authorization server SHOULD provide the
        >   expiration time via other means or document the default value.
        Source: https://tools.ietf.org/html/rfc6749#section-4.2.2

    This is not critical, worst case we will just refresh the token too often.
    Hence the best-effort approach.

    Args:
        raw_token (dict):

    Returns:
        datetime: a timezone-aware datetime object or None

    Raises:
        ValueError: when received token already expired
    """
    if 'expires_in' in raw_token:
        expires = timezone.now() + timedelta(seconds=raw_token['expires_in'])
    elif 'expires_at' in raw_token:
        expires = float_to_datetime(raw_token['expires_at'], tzinfo=pytz.UTC)
    else:
        expires = None

    if expires and expires <= timezone.now():
        raise ValueError(
            'Received token already expired. This means either parsing issue on our side or auth '
            'provider gone insane. Received token: {}'.format(raw_token)
        )

    return expires
