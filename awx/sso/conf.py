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
    SocialOrganizationMapField,
    SocialTeamMapField,
)


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
