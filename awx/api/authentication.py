# Copyright (c) 2025 Ansible, Inc.
# All Rights Reserved.

import logging
from django.conf import settings
from django.utils.encoding import smart_str
from rest_framework import authentication
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from social_core.backends.google import GoogleOAuth2
from social_core.backends.saml import SAMLAuth
from social_core.exceptions import AuthException

# Logging configuration
logger = logging.getLogger('awx.api.authentication')

# SAML-specific keys to check in settings
SAML_KEYS = [
    'SOCIAL_AUTH_SAML_SP_ENTITY_ID',
    'SOCIAL_AUTH_SAML_ENABLED_IDPS',
]

# Google-OAuth2-specific keys to check in settings
GoogleOAuth2_KEYS = [
    'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY',
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET',
]

# Global variables
sso_authentication_method = "none"
_last_detected_config = None  # Tracks the last detected configuration for change detection


def fetch_enabled_idps():
    """Fetch the latest enabled_idps dynamically."""
    return getattr(settings, 'SOCIAL_AUTH_SAML_ENABLED_IDPS', {})


def fetch_saml_idp_name():
    """Fetch the latest SAML IdP name dynamically."""
    enabled_idps = fetch_enabled_idps()
    if isinstance(enabled_idps, dict) and enabled_idps:
        return next(iter(enabled_idps.keys()), None)
    return None


def fetch_google_oauth2_key():
    """Fetch the latest google_oauth2_key dynamically."""
    return getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None)


def fetch_google_oauth2_secret():
    """Fetch the latest google_oauth2_secret dynamically."""
    return getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None)


def detect_backend_config():
    """
    Detect the current backend configuration relevant to SSO methods.
    Returns a tuple representing the detected configuration.
    """
    saml_detected = all(getattr(settings, key, None) for key in SAML_KEYS)
    google_detected = all(getattr(settings, key, None) for key in GoogleOAuth2_KEYS)
    return saml_detected, google_detected


def update_sso_authentication_method():
    """
    Dynamically determine and update the global SSO authentication method only if
    a change in the backend configuration is detected.
    """
    global sso_authentication_method, _last_detected_config

    # Detect the current backend configuration
    current_config = detect_backend_config()

    # Update only if there is a change in the configuration
    if current_config != _last_detected_config:
        _last_detected_config = current_config  # Update the last detected configuration
        saml_detected, google_detected = current_config

        if saml_detected:
            sso_authentication_method = 'saml'
        elif google_detected:
            sso_authentication_method = 'google'
        else:
            sso_authentication_method = 'none'

        logger.info(f"SSO Authentication Method updated to: {sso_authentication_method}")

    return sso_authentication_method


def log_enabled_authentication_methods():
    """Log and retrieve the enabled authentication methods and current SSO method."""
    enabled_idps = fetch_enabled_idps()
    saml_idp_name = fetch_saml_idp_name()
    current_sso_method = update_sso_authentication_method()

    logger.info(f"Enabled SAML IDPs: {enabled_idps}")
    logger.info(f"SAML IdP Name: {saml_idp_name}")
    logger.info(f"Current SSO Authentication Method: {current_sso_method}")

    return saml_idp_name, enabled_idps, current_sso_method


# Initialize the SSO method dynamically
update_sso_authentication_method()

# Retrieve dynamically updated variables
AWX_SAML_IdP_NAME, enabled_idps, current_sso_method = log_enabled_authentication_methods()

# Export the SSO method globally and allow for updates in real time
if __name__ == "__main__":
    print(f"SSO Authentication Method: {sso_authentication_method}")


class LoggedBasicAuthentication(authentication.BasicAuthentication):
    def authenticate(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        ret = super().authenticate(request)
        if ret:
            username = ret[0].username if ret[0] else '<none>'
            logger.info(smart_str(f"User {username} performed a {request.method} to {request.path} through the API"))
        return ret

    def authenticate_header(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        return super().authenticate_header(request)


class LoggedOAuth2Authentication(OAuth2Authentication):
    def authenticate(self, request):
        user_auth = super().authenticate(request)
        if user_auth:
            user, _ = user_auth
            logger.info(f"User {user.username} authenticated via OAuth2")
        return user_auth


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate_header(self, request):
        return 'Session'


class SocialMediaAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if not settings.SOCIAL_AUTH_ENABLED and not settings.SOCIAL_AUTH_SAML_ENABLED:
            return None

        auth_header = request.META.get('HTTP_AUTHORIZATION', None)
        if not auth_header:
            return None

        token = self._extract_token(auth_header)
        if not token:
            return None

        user = self._authenticate_social_user_or_saml_user(token)
        if user:
            return (user, token)
        return None

    def authenticate_header(self, request):
        return 'Bearer'

    def _extract_token(self, auth_header):
        if auth_header.lower().startswith('bearer '):
            return auth_header[7:].strip()
        return None

    def _authenticate_social_user_or_saml_user(self, token):
        try:
            if settings.SOCIAL_AUTH_SAML_ENABLED:
                backend = SAMLAuth()
                user = backend.do_auth(token)
                if user:
                    logger.info(f"User {user.username} authenticated via SAML login")
                    return user

            backend = GoogleOAuth2()
            user = backend.do_auth(token)
            if user:
                logger.info(f"User {user.username} authenticated via social media login")
                return user
        except AuthException as e:
            logger.error(f"Authentication failed: {str(e)}")
        return None


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'awx.api.authentication.LoggedBasicAuthentication',
        'awx.api.authentication.LoggedOAuth2Authentication',
        'awx.api.authentication.SessionAuthentication',
        'awx.api.authentication.SocialMediaAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
