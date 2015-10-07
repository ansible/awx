# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# flake8: noqa

# Runs after all configuration files have been loaded to fix/check/update
# settings as needed.

if not AUTH_LDAP_SERVER_URI:
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'awx.main.backend.LDAPBackend']

if not RADIUS_SERVER:
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'radiusauth.backends.RADIUSBackend']

if not all([SOCIAL_AUTH_GOOGLE_OAUTH2_KEY, SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET]):
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'social.backends.google.GoogleOAuth2']

if not all([SOCIAL_AUTH_GITHUB_KEY, SOCIAL_AUTH_GITHUB_SECRET]):
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'social.backends.github.GithubOAuth2']

if not all([SOCIAL_AUTH_GITHUB_ORG_KEY, SOCIAL_AUTH_GITHUB_ORG_SECRET, SOCIAL_AUTH_GITHUB_ORG_NAME]):
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'social.backends.github.GithubOrganizationOAuth2']

if not all([SOCIAL_AUTH_GITHUB_TEAM_KEY, SOCIAL_AUTH_GITHUB_TEAM_SECRET, SOCIAL_AUTH_GITHUB_TEAM_ID]):
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'social.backends.github.GithubTeamOAuth2']

if not all([SOCIAL_AUTH_SAML_SP_ENTITY_ID, SOCIAL_AUTH_SAML_SP_PUBLIC_CERT,
            SOCIAL_AUTH_SAML_SP_PRIVATE_KEY, SOCIAL_AUTH_SAML_ORG_INFO,
            SOCIAL_AUTH_SAML_TECHNICAL_CONTACT, SOCIAL_AUTH_SAML_SUPPORT_CONTACT,
            SOCIAL_AUTH_SAML_ENABLED_IDPS]):
    AUTHENTICATION_BACKENDS = [x for x in AUTHENTICATION_BACKENDS if x != 'social.backends.saml.SAMLAuth']

if not AUTH_BASIC_ENABLED:
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [x for x in REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] if x != 'rest_framework.authentication.BasicAuthentication']

