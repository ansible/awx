# Python
import collections
import urllib.parse as urlparse

# Django
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# AWX
from awx.conf import register, fields
from awx.sso.fields import (
    AuthenticationBackendsField,
    SAMLContactField,
    SAMLEnabledIdPsField,
    SAMLOrgAttrField,
    SAMLOrgInfoField,
    SAMLSecurityField,
    SAMLTeamAttrField,
    SAMLUserFlagsAttrField,
    SocialOrganizationMapField,
    SocialTeamMapField,
)
from awx.main.validators import validate_private_key, validate_certificate


class SocialAuthCallbackURL(object):
    def __init__(self, provider):
        self.provider = provider

    def __call__(self):
        path = reverse('social:complete', args=(self.provider,))
        return urlparse.urljoin(settings.TOWER_URL_BASE, path)


SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT = _(
    '''\
Mapping to organization admins/users from social auth accounts. This setting
controls which users are placed into which organizations based on their
username and email address. Configuration details are available in the
documentation.\
'''
)

# FIXME: /regex/gim (flags)

SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER = collections.OrderedDict(
    [
        ('Default', collections.OrderedDict([('users', True)])),
        ('Test Org', collections.OrderedDict([('admins', ['admin@example.com']), ('auditors', ['auditor@example.com']), ('users', True)])),
        (
            'Test Org 2',
            collections.OrderedDict(
                [
                    ('admins', ['admin@example.com', r'/^tower-[^@]+*?@.*$/']),
                    ('remove_admins', True),
                    ('users', r'/^[^@].*?@example\.com$/i'),
                    ('remove_users', True),
                ]
            ),
        ),
    ]
)

SOCIAL_AUTH_TEAM_MAP_HELP_TEXT = _(
    '''\
Mapping of team members (users) from social auth accounts. Configuration
details are available in the documentation.\
'''
)

SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER = collections.OrderedDict(
    [
        ('My Team', collections.OrderedDict([('organization', 'Test Org'), ('users', [r'/^[^@]+?@test\.example\.com$/']), ('remove', True)])),
        ('Other Team', collections.OrderedDict([('organization', 'Test Org 2'), ('users', r'/^[^@]+?@test2\.example\.com$/i'), ('remove', False)])),
    ]
)

if settings.ALLOW_LOCAL_RESOURCE_MANAGEMENT:
    ###############################################################################
    # AUTHENTICATION BACKENDS DYNAMIC SETTING
    ###############################################################################

    register(
        'AUTHENTICATION_BACKENDS',
        field_class=AuthenticationBackendsField,
        label=_('Authentication Backends'),
        help_text=_('List of authentication backends that are enabled based on license features and other authentication settings.'),
        read_only=True,
        depends_on=AuthenticationBackendsField.get_all_required_settings(),
        category=_('Authentication'),
        category_slug='authentication',
    )

    register(
        'SOCIAL_AUTH_ORGANIZATION_MAP',
        field_class=SocialOrganizationMapField,
        allow_null=True,
        default=None,
        label=_('Social Auth Organization Map'),
        help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
        category=_('Authentication'),
        category_slug='authentication',
        placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
    )

    register(
        'SOCIAL_AUTH_TEAM_MAP',
        field_class=SocialTeamMapField,
        allow_null=True,
        default=None,
        label=_('Social Auth Team Map'),
        help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
        category=_('Authentication'),
        category_slug='authentication',
        placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
    )

    register(
        'SOCIAL_AUTH_USER_FIELDS',
        field_class=fields.StringListField,
        allow_null=True,
        default=None,
        label=_('Social Auth User Fields'),
        help_text=_(
            'When set to an empty list `[]`, this setting prevents new user '
            'accounts from being created. Only users who have previously '
            'logged in using social auth or have a user account with a '
            'matching email address will be able to login.'
        ),
        category=_('Authentication'),
        category_slug='authentication',
        placeholder=['username', 'email'],
    )

    register(
        'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL',
        field_class=fields.BooleanField,
        default=False,
        label=_('Use Email address for usernames'),
        help_text=_('Enabling this setting will tell social auth to use the full Email as username instead of the full name'),
        category=_('Authentication'),
        category_slug='authentication',
    )

    ###############################################################################
    # SAML AUTHENTICATION SETTINGS
    ###############################################################################

    def get_saml_metadata_url():
        return urlparse.urljoin(settings.TOWER_URL_BASE, reverse('sso:saml_metadata'))

    def get_saml_entity_id():
        return settings.TOWER_URL_BASE

    register(
        'SAML_AUTO_CREATE_OBJECTS',
        field_class=fields.BooleanField,
        default=True,
        label=_('Automatically Create Organizations and Teams on SAML Login'),
        help_text=_('When enabled (the default), mapped Organizations and Teams will be created automatically on successful SAML login.'),
        category=_('SAML'),
        category_slug='saml',
    )

    register(
        'SOCIAL_AUTH_SAML_CALLBACK_URL',
        field_class=fields.CharField,
        read_only=True,
        default=SocialAuthCallbackURL('saml'),
        label=_('SAML Assertion Consumer Service (ACS) URL'),
        help_text=_(
            'Register the service as a service provider (SP) with each identity '
            'provider (IdP) you have configured. Provide your SP Entity ID '
            'and this ACS URL for your application.'
        ),
        category=_('SAML'),
        category_slug='saml',
        depends_on=['TOWER_URL_BASE'],
    )

    register(
        'SOCIAL_AUTH_SAML_METADATA_URL',
        field_class=fields.CharField,
        read_only=True,
        default=get_saml_metadata_url,
        label=_('SAML Service Provider Metadata URL'),
        help_text=_('If your identity provider (IdP) allows uploading an XML metadata file, you can download one from this URL.'),
        category=_('SAML'),
        category_slug='saml',
    )

    register(
        'SOCIAL_AUTH_SAML_SP_ENTITY_ID',
        field_class=fields.CharField,
        allow_blank=True,
        default=get_saml_entity_id,
        label=_('SAML Service Provider Entity ID'),
        help_text=_(
            'The application-defined unique identifier used as the '
            'audience of the SAML service provider (SP) configuration. '
            'This is usually the URL for the service.'
        ),
        category=_('SAML'),
        category_slug='saml',
        depends_on=['TOWER_URL_BASE'],
    )

    register(
        'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT',
        field_class=fields.CharField,
        allow_blank=True,
        validators=[validate_certificate],
        label=_('SAML Service Provider Public Certificate'),
        help_text=_('Create a keypair to use as a service provider (SP) and include the certificate content here.'),
        category=_('SAML'),
        category_slug='saml',
    )

    register(
        'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY',
        field_class=fields.CharField,
        allow_blank=True,
        validators=[validate_private_key],
        label=_('SAML Service Provider Private Key'),
        help_text=_('Create a keypair to use as a service provider (SP) and include the private key content here.'),
        category=_('SAML'),
        category_slug='saml',
        encrypted=True,
    )

    register(
        'SOCIAL_AUTH_SAML_ORG_INFO',
        field_class=SAMLOrgInfoField,
        label=_('SAML Service Provider Organization Info'),
        help_text=_('Provide the URL, display name, and the name of your app. Refer to the documentation for example syntax.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict(
            [('en-US', collections.OrderedDict([('name', 'example'), ('displayname', 'Example'), ('url', 'http://www.example.com')]))]
        ),
    )

    register(
        'SOCIAL_AUTH_SAML_TECHNICAL_CONTACT',
        field_class=SAMLContactField,
        allow_blank=True,
        label=_('SAML Service Provider Technical Contact'),
        help_text=_('Provide the name and email address of the technical contact for your service provider. Refer to the documentation for example syntax.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict([('givenName', 'Technical Contact'), ('emailAddress', 'techsup@example.com')]),
    )

    register(
        'SOCIAL_AUTH_SAML_SUPPORT_CONTACT',
        field_class=SAMLContactField,
        allow_blank=True,
        label=_('SAML Service Provider Support Contact'),
        help_text=_('Provide the name and email address of the support contact for your service provider. Refer to the documentation for example syntax.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict([('givenName', 'Support Contact'), ('emailAddress', 'support@example.com')]),
    )

    register(
        'SOCIAL_AUTH_SAML_ENABLED_IDPS',
        field_class=SAMLEnabledIdPsField,
        default={},
        label=_('SAML Enabled Identity Providers'),
        help_text=_(
            'Configure the Entity ID, SSO URL and certificate for each identity'
            ' provider (IdP) in use. Multiple SAML IdPs are supported. Some IdPs'
            ' may provide user data using attribute names that differ from the'
            ' default OIDs. Attribute names may be overridden for each IdP. Refer'
            ' to the Ansible documentation for additional details and syntax.'
        ),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict(
            [
                (
                    'Okta',
                    collections.OrderedDict(
                        [
                            ('entity_id', 'http://www.okta.com/HHniyLkaxk9e76wD0Thh'),
                            ('url', 'https://dev-123456.oktapreview.com/app/ansibletower/HHniyLkaxk9e76wD0Thh/sso/saml'),
                            ('x509cert', 'MIIDpDCCAoygAwIBAgIGAVVZ4rPzMA0GCSqGSIb3...'),
                            ('attr_user_permanent_id', 'username'),
                            ('attr_first_name', 'first_name'),
                            ('attr_last_name', 'last_name'),
                            ('attr_username', 'username'),
                            ('attr_email', 'email'),
                        ]
                    ),
                ),
                (
                    'OneLogin',
                    collections.OrderedDict(
                        [
                            ('entity_id', 'https://app.onelogin.com/saml/metadata/123456'),
                            ('url', 'https://example.onelogin.com/trust/saml2/http-post/sso/123456'),
                            ('x509cert', 'MIIEJjCCAw6gAwIBAgIUfuSD54OPSBhndDHh3gZo...'),
                            ('attr_user_permanent_id', 'name_id'),
                            ('attr_first_name', 'User.FirstName'),
                            ('attr_last_name', 'User.LastName'),
                            ('attr_username', 'User.email'),
                            ('attr_email', 'User.email'),
                        ]
                    ),
                ),
            ]
        ),
    )

    register(
        'SOCIAL_AUTH_SAML_SECURITY_CONFIG',
        field_class=SAMLSecurityField,
        allow_null=True,
        default={'requestedAuthnContext': False},
        label=_('SAML Security Config'),
        help_text=_(
            'A dict of key value pairs that are passed to the underlying python-saml security setting https://github.com/onelogin/python-saml#settings'
        ),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict(
            [
                ("nameIdEncrypted", False),
                ("authnRequestsSigned", False),
                ("logoutRequestSigned", False),
                ("logoutResponseSigned", False),
                ("signMetadata", False),
                ("wantMessagesSigned", False),
                ("wantAssertionsSigned", False),
                ("wantAssertionsEncrypted", False),
                ("wantNameId", True),
                ("wantNameIdEncrypted", False),
                ("wantAttributeStatement", True),
                ("requestedAuthnContext", True),
                ("requestedAuthnContextComparison", "exact"),
                ("metadataValidUntil", "2015-06-26T20:00:00Z"),
                ("metadataCacheDuration", "PT518400S"),
                ("signatureAlgorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1"),
                ("digestAlgorithm", "http://www.w3.org/2000/09/xmldsig#sha1"),
            ]
        ),
    )

    register(
        'SOCIAL_AUTH_SAML_SP_EXTRA',
        field_class=fields.DictField,
        allow_null=True,
        default=None,
        label=_('SAML Service Provider extra configuration data'),
        help_text=_('A dict of key value pairs to be passed to the underlying python-saml Service Provider configuration setting.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict(),
    )

    register(
        'SOCIAL_AUTH_SAML_EXTRA_DATA',
        field_class=fields.ListTuplesField,
        allow_null=True,
        default=None,
        label=_('SAML IDP to extra_data attribute mapping'),
        help_text=_('A list of tuples that maps IDP attributes to extra_attributes.' ' Each attribute will be a list of values, even if only 1 value.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=[('attribute_name', 'extra_data_name_for_attribute'), ('department', 'department'), ('manager_full_name', 'manager_full_name')],
    )

    register(
        'SOCIAL_AUTH_SAML_ORGANIZATION_MAP',
        field_class=SocialOrganizationMapField,
        allow_null=True,
        default=None,
        label=_('SAML Organization Map'),
        help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
        category=_('SAML'),
        category_slug='saml',
        placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
    )

    register(
        'SOCIAL_AUTH_SAML_TEAM_MAP',
        field_class=SocialTeamMapField,
        allow_null=True,
        default=None,
        label=_('SAML Team Map'),
        help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
        category=_('SAML'),
        category_slug='saml',
        placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
    )

    register(
        'SOCIAL_AUTH_SAML_ORGANIZATION_ATTR',
        field_class=SAMLOrgAttrField,
        allow_null=True,
        default=None,
        label=_('SAML Organization Attribute Mapping'),
        help_text=_('Used to translate user organization membership.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict(
            [
                ('saml_attr', 'organization'),
                ('saml_admin_attr', 'organization_admin'),
                ('saml_auditor_attr', 'organization_auditor'),
                ('remove', True),
                ('remove_admins', True),
                ('remove_auditors', True),
            ]
        ),
    )

    register(
        'SOCIAL_AUTH_SAML_TEAM_ATTR',
        field_class=SAMLTeamAttrField,
        allow_null=True,
        default=None,
        label=_('SAML Team Attribute Mapping'),
        help_text=_('Used to translate user team membership.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=collections.OrderedDict(
            [
                ('saml_attr', 'team'),
                ('remove', True),
                (
                    'team_org_map',
                    [
                        collections.OrderedDict([('team', 'Marketing'), ('organization', 'Red Hat')]),
                        collections.OrderedDict([('team', 'Human Resources'), ('organization', 'Red Hat')]),
                        collections.OrderedDict([('team', 'Engineering'), ('organization', 'Red Hat')]),
                        collections.OrderedDict([('team', 'Engineering'), ('organization', 'Ansible')]),
                        collections.OrderedDict([('team', 'Quality Engineering'), ('organization', 'Ansible')]),
                        collections.OrderedDict([('team', 'Sales'), ('organization', 'Ansible')]),
                    ],
                ),
            ]
        ),
    )

    register(
        'SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR',
        field_class=SAMLUserFlagsAttrField,
        allow_null=True,
        default=None,
        label=_('SAML User Flags Attribute Mapping'),
        help_text=_('Used to map super users and system auditors from SAML.'),
        category=_('SAML'),
        category_slug='saml',
        placeholder=[
            ('is_superuser_attr', 'saml_attr'),
            ('is_superuser_value', ['value']),
            ('is_superuser_role', ['saml_role']),
            ('remove_superusers', True),
            ('is_system_auditor_attr', 'saml_attr'),
            ('is_system_auditor_value', ['value']),
            ('is_system_auditor_role', ['saml_role']),
            ('remove_system_auditors', True),
        ],
    )

    register(
        'LOCAL_PASSWORD_MIN_LENGTH',
        field_class=fields.IntegerField,
        min_value=0,
        default=0,
        label=_('Minimum number of characters in local password'),
        help_text=_('Minimum number of characters required in a local password. 0 means no minimum'),
        category=_('Authentication'),
        category_slug='authentication',
    )

    register(
        'LOCAL_PASSWORD_MIN_DIGITS',
        field_class=fields.IntegerField,
        min_value=0,
        default=0,
        label=_('Minimum number of digit characters in local password'),
        help_text=_('Minimum number of digit characters required in a local password. 0 means no minimum'),
        category=_('Authentication'),
        category_slug='authentication',
    )

    register(
        'LOCAL_PASSWORD_MIN_UPPER',
        field_class=fields.IntegerField,
        min_value=0,
        default=0,
        label=_('Minimum number of uppercase characters in local password'),
        help_text=_('Minimum number of uppercase characters required in a local password. 0 means no minimum'),
        category=_('Authentication'),
        category_slug='authentication',
    )

    register(
        'LOCAL_PASSWORD_MIN_SPECIAL',
        field_class=fields.IntegerField,
        min_value=0,
        default=0,
        label=_('Minimum number of special characters in local password'),
        help_text=_('Minimum number of special characters required in a local password. 0 means no minimum'),
        category=_('Authentication'),
        category_slug='authentication',
    )
