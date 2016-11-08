# Python
import collections
import urlparse

# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import register
from awx.sso import fields
from awx.main.validators import validate_private_key, validate_certificate
from awx.sso.validators import *  # noqa


class SocialAuthCallbackURL(object):

    def __init__(self, provider):
        self.provider = provider

    def __call__(self):
        path = reverse('social:complete', args=(self.provider,))
        return urlparse.urljoin(settings.TOWER_URL_BASE, path)

SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT = _('''\
Mapping to organization admins/users from social auth accounts. This setting
controls which users are placed into which Tower organizations based on
their username and email address.  Dictionary keys are organization names.
organizations will be created if not present if the license allows for
multiple organizations, otherwise the single default organization is used
regardless of the key.  Values are dictionaries defining the options for
each organization's membership.  For each organization it is possible to
specify which users are automatically users of the organization and also
which users can administer the organization. 

- admins: None, True/False, string or list/tuple of strings.
  If None, organization admins will not be updated.
  If True, all users using social auth will automatically be added as admins
  of the organization.
  If False, no social auth users will be automatically added as admins of
  the organiation.
  If a string or list of strings, specifies the usernames and emails for
  users who will be added to the organization. Strings in the format
  "/<pattern>/<flags>" will be interpreted as regular expressions and may also
  be used instead of string literals; only "i" and "m" are supported for flags.
- remove_admins: True/False. Defaults to True.
  If True, a user who does not match will be removed from the organization's
  administrative list.
- users: None, True/False, string or list/tuple of strings. Same rules apply
  as for admins.
- remove_users: True/False. Defaults to True. Same rules as apply for 
  remove_admins.\
''')

# FIXME: /regex/gim (flags)

SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER = collections.OrderedDict([
    ('Default', collections.OrderedDict([
        ('users', True),
    ])),
    ('Test Org', collections.OrderedDict([
        ('admins', ['admin@example.com']),
        ('users', True),
    ])),
    ('Test Org 2', collections.OrderedDict([
        ('admins', ['admin@example.com', r'/^tower-[^@]+*?@.*$/']),
        ('remove_admins', True),
        ('users', r'/^[^@].*?@example\.com$/i'),
        ('remove_users', True),
    ])),
])

SOCIAL_AUTH_TEAM_MAP_HELP_TEXT = _('''\
Mapping of team members (users) from social auth accounts. Keys are team
names (will be created if not present). Values are dictionaries of options
for each team's membership, where each can contain the following parameters:

- organization: string. The name of the organization to which the team
  belongs.  The team will be created if the combination of organization and
  team name does not exist.  The organization will first be created if it
  does not exist.  If the license does not allow for multiple organizations,
  the team will always be assigned to the single default organization.
- users: None, True/False, string or list/tuple of strings.
  If None, team members will not be updated.
  If True/False, all social auth users will be added/removed as team
  members.
  If a string or list of strings, specifies expressions used to match users.
  User will be added as a team member if the username or email matches.
  Strings in the format "/<pattern>/<flags>" will be interpreted as regular
  expressions and may also be used instead of string literals; only "i" and "m"
  are supported for flags.
- remove: True/False. Defaults to True. If True, a user who does not match
  the rules above will be removed from the team.\
''')

SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER = collections.OrderedDict([
    ('My Team', collections.OrderedDict([
        ('organization', 'Test Org'),
        ('users', [r'/^[^@]+?@test\.example\.com$/']),
        ('remove', True),
    ])),
    ('Other Team', collections.OrderedDict([
        ('organization', 'Test Org 2'),
        ('users', r'/^[^@]+?@test2\.example\.com$/i'),
        ('remove', False),
    ])),
])

###############################################################################
# AUTHENTICATION BACKENDS DYNAMIC SETTING
###############################################################################

register(
    'AUTHENTICATION_BACKENDS',
    field_class=fields.AuthenticationBackendsField,
    label=_('Authentication Backends'),
    help_text=_('List of authentication backends that are enabled based on '
                'license features and other authentication settings.'),
    read_only=True,
    depends_on=fields.AuthenticationBackendsField.get_all_required_settings(),
    category=_('Authentication'),
    category_slug='authentication',
)

register(
    'SOCIAL_AUTH_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
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
    field_class=fields.SocialTeamMapField,
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
    help_text=_('When set to an empty list `[]`, this setting prevents new user '
                'accounts from being created. Only users who have previously '
                'logged in using social auth or have a user account with a '
                'matching email address will be able to login.'),
    category=_('Authentication'),
    category_slug='authentication',
    placeholder=['username', 'email'],
)

###############################################################################
# LDAP AUTHENTICATION SETTINGS
###############################################################################

register(
    'AUTH_LDAP_SERVER_URI',
    field_class=fields.URLField,
    schemes=('ldap', 'ldaps'),
    allow_blank=True,
    default='',
    label=_('LDAP Server URI'),
    help_text=_('URI to connect to LDAP server, such as "ldap://ldap.example.com:389" '
                '(non-SSL) or "ldaps://ldap.example.com:636" (SSL).  LDAP authentication '
                'is disabled if this parameter is empty or your license does not '
                'enable LDAP support.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder='ldaps://ldap.example.com:636',
)

register(
    'AUTH_LDAP_BIND_DN',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    validators=[validate_ldap_bind_dn],
    label=_('LDAP Bind DN'),
    help_text=_('DN (Distinguished Name) of user to bind for all search queries. '
                'Normally in the format "CN=Some User,OU=Users,DC=example,DC=com" '
                'but may also be specified as "DOMAIN\username" for Active Directory. '
                'This is the system user account we will use to login to query LDAP '
                'for other user information.'),
    category=_('LDAP'),
    category_slug='ldap',
)

register(
    'AUTH_LDAP_BIND_PASSWORD',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    label=_('LDAP Bind Password'),
    help_text=_('Password used to bind LDAP user account.'),
    category=_('LDAP'),
    category_slug='ldap',
)

register(
    'AUTH_LDAP_START_TLS',
    field_class=fields.BooleanField,
    default=False,
    label=_('LDAP Start TLS'),
    help_text=_('Whether to enable TLS when the LDAP connection is not using SSL.'),
    category=_('LDAP'),
    category_slug='ldap',
)

register(
    'AUTH_LDAP_CONNECTION_OPTIONS',
    field_class=fields.LDAPConnectionOptionsField,
    default={'OPT_REFERRALS': 0},
    label=_('LDAP Connection Options'),
    help_text=_('Additional options to set for the LDAP connection.  LDAP '
                'referrals are disabled by default (to prevent certain LDAP '
                'queries from hanging with AD). Option names should be strings '
                '(e.g. "OPT_REFERRALS"). Refer to '
                'https://www.python-ldap.org/doc/html/ldap.html#options for '
                'possible options and values that can be set.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=collections.OrderedDict([
        ('OPT_REFERRALS', 0),
    ]),
)

register(
    'AUTH_LDAP_USER_SEARCH',
    field_class=fields.LDAPSearchUnionField,
    default=[],
    label=_('LDAP User Search'),
    help_text=_('LDAP search query to find users.  Any user that matches the given '
                'pattern will be able to login to Tower.  The user should also be '
                'mapped into an Tower organization (as defined in the '
                'AUTH_LDAP_ORGANIZATION_MAP setting).  If multiple search queries '
                'need to be supported use of "LDAPUnion" is possible. See '
                'python-ldap documentation as linked at the top of this section.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=(
        'OU=Users,DC=example,DC=com',
        'SCOPE_SUBTREE',
        '(sAMAccountName=%(user)s)',
    ),
)

register(
    'AUTH_LDAP_USER_DN_TEMPLATE',
    field_class=fields.LDAPDNWithUserField,
    allow_blank=True,
    default='',
    label=_('LDAP User DN Template'),
    help_text=_('Alternative to user search, if user DNs are all of the same '
                'format. This approach will be more efficient for user lookups than '
                'searching if it is usable in your organizational environment. If '
                'this setting has a value it will be used instead of '
                'AUTH_LDAP_USER_SEARCH.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder='uid=%(user)s,OU=Users,DC=example,DC=com',
)

register(
    'AUTH_LDAP_USER_ATTR_MAP',
    field_class=fields.LDAPUserAttrMapField,
    default={},
    label=_('LDAP User Attribute Map'),
    help_text=_('Mapping of LDAP user schema to Tower API user atrributes (key is '
                'user attribute name, value is LDAP attribute name).  The default '
                'setting is valid for ActiveDirectory but users with other LDAP '
                'configurations may need to change the values (not the keys) of '
                'the dictionary/hash-table.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=collections.OrderedDict([
        ('first_name', 'givenName'),
        ('last_name', 'sn'),
        ('email', 'mail'),
    ]),
)

register(
    'AUTH_LDAP_GROUP_SEARCH',
    field_class=fields.LDAPSearchField,
    default=[],
    label=_('LDAP Group Search'),
    help_text=_('Users in Tower are mapped to organizations based on their '
                'membership in LDAP groups. This setting defines the LDAP search '
                'query to find groups. Note that this, unlike the user search '
                'above, does not support LDAPSearchUnion.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=(
        'DC=example,DC=com',
        'SCOPE_SUBTREE',
        '(objectClass=group)',
    ),
)

register(
    'AUTH_LDAP_GROUP_TYPE',
    field_class=fields.LDAPGroupTypeField,
    label=_('LDAP Group Type'),
    help_text=_('The group type may need to be changed based on the type of the '
                'LDAP server.  Values are listed at: '
                'http://pythonhosted.org/django-auth-ldap/groups.html#types-of-groups'),
    category=_('LDAP'),
    category_slug='ldap',
)

register(
    'AUTH_LDAP_REQUIRE_GROUP',
    field_class=fields.LDAPDNField,
    allow_blank=True,
    default='',
    label=_('LDAP Require Group'),
    help_text=_('Group DN required to login. If specified, user must be a member '
                'of this group to login via LDAP. If not set, everyone in LDAP '
                'that matches the user search will be able to login via Tower. '
                'Only one require group is supported.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder='CN=Tower Users,OU=Users,DC=example,DC=com',
)

register(
    'AUTH_LDAP_DENY_GROUP',
    field_class=fields.LDAPDNField,
    allow_blank=True,
    default='',
    label=_('LDAP Deny Group'),
    help_text=_('Group DN denied from login. If specified, user will not be '
                'allowed to login if a member of this group.  Only one deny group '
                'is supported.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder='CN=Disabled Users,OU=Users,DC=example,DC=com',
)

register(
    'AUTH_LDAP_USER_FLAGS_BY_GROUP',
    field_class=fields.LDAPUserFlagsField,
    default={},
    label=_('LDAP User Flags By Group'),
    help_text=_('User profile flags updated from group membership (key is user '
                'attribute name, value is group DN).  These are boolean fields '
                'that are matched based on whether the user is a member of the '
                'given group.  So far only is_superuser is settable via this '
                'method.  This flag is set both true and false at login time '
                'based on current LDAP settings.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=collections.OrderedDict([
        ('is_superuser', 'CN=Domain Admins,CN=Users,DC=example,DC=com'),
    ]),
)

register(
    'AUTH_LDAP_ORGANIZATION_MAP',
    field_class=fields.LDAPOrganizationMapField,
    default={},
    label=_('LDAP Organization Map'),
    help_text=_('Mapping between organization admins/users and LDAP groups. This '
                'controls what users are placed into what Tower organizations '
                'relative to their LDAP group memberships. Keys are organization '
                'names. Organizations will be created if not present. Values are '
                'dictionaries defining the options for each organization\'s '
                'membership.  For each organization it is possible to specify '
                'what groups are automatically users of the organization and also '
                'what groups can administer the organization.\n\n'
                ' - admins: None, True/False, string or list of strings.\n'
                '   If None, organization admins will not be updated based on '
                'LDAP values.\n'
                '   If True, all users in LDAP will automatically be added as '
                'admins of the organization.\n'
                '   If False, no LDAP users will be automatically added as admins '
                'of the organiation.\n'
                '   If a string or list of strings, specifies the group DN(s) '
                'that will be added of the organization if they match any of the '
                'specified groups.\n'
                ' - remove_admins: True/False. Defaults to True.\n'
                '   If True, a user who is not an member of the given groups will '
                'be removed from the organization\'s administrative list.\n'
                ' - users: None, True/False, string or list/tuple of strings. '
                'Same rules apply as for admins.\n'
                ' - remove_users: True/False. Defaults to True. Same rules apply '
                'as for remove_admins.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=collections.OrderedDict([
        ('Test Org', collections.OrderedDict([
            ('admins', 'CN=Domain Admins,CN=Users,DC=example,DC=com'),
            ('users', ['CN=Domain Users,CN=Users,DC=example,DC=com']),
            ('remove_users', True),
            ('remove_admins', True),
        ])),
        ('Test Org 2', collections.OrderedDict([
            ('admins', 'CN=Administrators,CN=Builtin,DC=example,DC=com'),
            ('users', True),
            ('remove_users', True),
            ('remove_admins', True),
        ])),
    ]),
)

register(
    'AUTH_LDAP_TEAM_MAP',
    field_class=fields.LDAPTeamMapField,
    default={},
    label=_('LDAP Team Map'),
    help_text=_('Mapping between team members (users) and LDAP groups. Keys are '
                'team names (will be created if not present). Values are '
                'dictionaries of options for each team\'s membership, where each '
                'can contain the following parameters:\n\n'
                ' - organization: string. The name of the organization to which '
                'the team belongs. The team will be created if the combination of '
                'organization and team name does not exist. The organization will '
                'first be created if it does not exist.\n'
                ' - users: None, True/False, string or list/tuple of strings.\n'
                '   If None, team members will not be updated.\n'
                '   If True/False, all LDAP users will be added/removed as team '
                'members.\n'
                '   If a string or list of strings, specifies the group DN(s). '
                'User will be added as a team member if the user is a member of '
                'ANY of these groups.\n'
                '- remove: True/False. Defaults to True. If True, a user who is '
                'not a member of the given groups will be removed from the team.'),
    category=_('LDAP'),
    category_slug='ldap',
    placeholder=collections.OrderedDict([
        ('My Team', collections.OrderedDict([
            ('organization', 'Test Org'),
            ('users', ['CN=Domain Users,CN=Users,DC=example,DC=com']),
            ('remove', True),
        ])),
        ('Other Team', collections.OrderedDict([
            ('organization', 'Test Org 2'),
            ('users', 'CN=Other Users,CN=Users,DC=example,DC=com'),
            ('remove', False),
        ])),
    ]),
)

###############################################################################
# RADIUS AUTHENTICATION SETTINGS
###############################################################################

register(
    'RADIUS_SERVER',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    label=_('RADIUS Server'),
    help_text=_('Hostname/IP of RADIUS server. RADIUS authentication will be '
                'disabled if this setting is empty.'),
    category=_('RADIUS'),
    category_slug='radius',
    placeholder='radius.example.com',
)

register(
    'RADIUS_PORT',
    field_class=fields.IntegerField,
    min_value=1,
    max_value=65535,
    default=1812,
    label=_('RADIUS Port'),
    help_text=_('Port of RADIUS server.'),
    category=_('RADIUS'),
    category_slug='radius',
)

register(
    'RADIUS_SECRET',
    field_class=fields.RADIUSSecretField,
    allow_blank=True,
    default='',
    label=_('RADIUS Secret'),
    help_text=_('Shared secret for authenticating to RADIUS server.'),
    category=_('RADIUS'),
    category_slug='radius',
)

###############################################################################
# GOOGLE OAUTH2 AUTHENTICATION SETTINGS
###############################################################################

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_CALLBACK_URL',
    field_class=fields.CharField,
    read_only=True,
    default=SocialAuthCallbackURL('google-oauth2'),
    label=_('Google OAuth2 Callback URL'),
    help_text=_('Create a project at https://console.developers.google.com/ to '
                'obtain an OAuth2 key and secret for a web application. Ensure '
                'that the Google+ API is enabled. Provide this URL as the '
                'callback URL for your application.'),
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
)

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('Google OAuth2 Key'),
    help_text=_('The OAuth2 key from your web application at https://console.developers.google.com/.'),
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
    placeholder='528620852399-gm2dt4hrl2tsj67fqamk09k1e0ad6gd8.apps.googleusercontent.com',
)

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('Google OAuth2 Secret'),
    help_text=_('The OAuth2 secret from your web application at https://console.developers.google.com/.'),
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
    placeholder='q2fMVCmEregbg-drvebPp8OW',
)

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS',
    field_class=fields.StringListField,
    default=[],
    label=_('Google OAuth2 Whitelisted Domains'),
    help_text=_('Update this setting to restrict the domains who are allowed to '
                'login using Google OAuth2.'),
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
    placeholder=['example.com'],
)

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS',
    field_class=fields.DictField,
    default={},
    label=_('Google OAuth2 Extra Arguments'),
    help_text=_('Extra arguments for Google OAuth2 login. When only allowing a '
                'single domain to authenticate, set to `{"hd": "yourdomain.com"}` '
                'and Google will not display any other accounts even if the user '
                'is logged in with multiple Google accounts.'),
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
    placeholder={'hd': 'example.com'},
)

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
    allow_null=True,
    default=None,
    label=_('Google OAuth2 Organization Map'),
    help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
    placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
)

register(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP',
    field_class=fields.SocialTeamMapField,
    allow_null=True,
    default=None,
    label=_('Google OAuth2 Team Map'),
    help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
    category=_('Google OAuth2'),
    category_slug='google-oauth2',
    placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
)

###############################################################################
# GITHUB OAUTH2 AUTHENTICATION SETTINGS
###############################################################################

register(
    'SOCIAL_AUTH_GITHUB_CALLBACK_URL',
    field_class=fields.CharField,
    read_only=True,
    default=SocialAuthCallbackURL('github'),
    label=_('GitHub OAuth2 Callback URL'),
    help_text=_('Create a developer application at '
                'https://github.com/settings/developers to obtain an OAuth2 '
                'key (Client ID) and secret (Client Secret). Provide this URL '
                'as the callback URL for your application.'),
    category=_('GitHub OAuth2'),
    category_slug='github',
)

register(
    'SOCIAL_AUTH_GITHUB_KEY',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub OAuth2 Key'),
    help_text=_('The OAuth2 key (Client ID) from your GitHub developer application.'),
    category=_('GitHub OAuth2'),
    category_slug='github',
)

register(
    'SOCIAL_AUTH_GITHUB_SECRET',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub OAuth2 Secret'),
    help_text=_('The OAuth2 secret (Client Secret) from your GitHub developer application.'),
    category=_('GitHub OAuth2'),
    category_slug='github',
)

register(
    'SOCIAL_AUTH_GITHUB_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
    allow_null=True,
    default=None,
    label=_('GitHub OAuth2 Organization Map'),
    help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
    category=_('GitHub OAuth2'),
    category_slug='github',
    placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
)

register(
    'SOCIAL_AUTH_GITHUB_TEAM_MAP',
    field_class=fields.SocialTeamMapField,
    allow_null=True,
    default=None,
    label=_('GitHub OAuth2 Team Map'),
    help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
    category=_('GitHub OAuth2'),
    category_slug='github',
    placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
)

###############################################################################
# GITHUB ORG OAUTH2 AUTHENTICATION SETTINGS
###############################################################################

register(
    'SOCIAL_AUTH_GITHUB_ORG_CALLBACK_URL',
    field_class=fields.CharField,
    read_only=True,
    default=SocialAuthCallbackURL('github-org'),
    label=_('GitHub Organization OAuth2 Callback URL'),
    help_text=_('Create an organization-owned application at '
                'https://github.com/organizations/<yourorg>/settings/applications '
                'and obtain an OAuth2 key (Client ID) and secret (Client Secret). '
                'Provide this URL as the callback URL for your application.'),
    category=_('GitHub Organization OAuth2'),
    category_slug='github-org',
)

register(
    'SOCIAL_AUTH_GITHUB_ORG_KEY',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub Organization OAuth2 Key'),
    help_text=_('The OAuth2 key (Client ID) from your GitHub organization application.'),
    category=_('GitHub Organization OAuth2'),
    category_slug='github-org',
)

register(
    'SOCIAL_AUTH_GITHUB_ORG_SECRET',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub Organization OAuth2 Secret'),
    help_text=_('The OAuth2 secret (Client Secret) from your GitHub organization application.'),
    category=_('GitHub Organization OAuth2'),
    category_slug='github-org',
)

register(
    'SOCIAL_AUTH_GITHUB_ORG_NAME',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub Organization Name'),
    help_text=_('The name of your GitHub organization, as used in your '
                'organization\'s URL: https://github.com/<yourorg>/.'),
    category=_('GitHub Organization OAuth2'),
    category_slug='github-org',
)

register(
    'SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
    allow_null=True,
    default=None,
    label=_('GitHub Organization OAuth2 Organization Map'),
    help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
    category=_('GitHub Organization OAuth2'),
    category_slug='github-org',
    placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
)

register(
    'SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP',
    field_class=fields.SocialTeamMapField,
    allow_null=True,
    default=None,
    label=_('GitHub Organization OAuth2 Team Map'),
    help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
    category=_('GitHub Organization OAuth2'),
    category_slug='github-org',
    placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
)

###############################################################################
# GITHUB TEAM OAUTH2 AUTHENTICATION SETTINGS
###############################################################################

register(
    'SOCIAL_AUTH_GITHUB_TEAM_CALLBACK_URL',
    field_class=fields.CharField,
    read_only=True,
    default=SocialAuthCallbackURL('github-team'),
    label=_('GitHub Team OAuth2 Callback URL'),
    help_text=_('Create an organization-owned application at '
                'https://github.com/organizations/<yourorg>/settings/applications '
                'and obtain an OAuth2 key (Client ID) and secret (Client Secret). '
                'Provide this URL as the callback URL for your application.'),
    category=_('GitHub Team OAuth2'),
    category_slug='github-team',
)

register(
    'SOCIAL_AUTH_GITHUB_TEAM_KEY',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub Team OAuth2 Key'),
    help_text=_('The OAuth2 key (Client ID) from your GitHub organization application.'),
    category=_('GitHub Team OAuth2'),
    category_slug='github-team',
)

register(
    'SOCIAL_AUTH_GITHUB_TEAM_SECRET',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub Team OAuth2 Secret'),
    help_text=_('The OAuth2 secret (Client Secret) from your GitHub organization application.'),
    category=_('GitHub Team OAuth2'),
    category_slug='github-team',
)

register(
    'SOCIAL_AUTH_GITHUB_TEAM_ID',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('GitHub Team ID'),
    help_text=_('Find the numeric team ID using the Github API: '
                'http://fabian-kostadinov.github.io/2015/01/16/how-to-find-a-github-team-id/.'),
    category=_('GitHub Team OAuth2'),
    category_slug='github-team',
)

register(
    'SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
    allow_null=True,
    default=None,
    label=_('GitHub Team OAuth2 Organization Map'),
    help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
    category=_('GitHub Team OAuth2'),
    category_slug='github-team',
    placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
)

register(
    'SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP',
    field_class=fields.SocialTeamMapField,
    allow_null=True,
    default=None,
    label=_('GitHub Team OAuth2 Team Map'),
    help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
    category=_('GitHub Team OAuth2'),
    category_slug='github-team',
    placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
)

###############################################################################
# MICROSOFT AZURE ACTIVE DIRECTORY SETTINGS
###############################################################################

register(
    'SOCIAL_AUTH_AZUREAD_OAUTH2_CALLBACK_URL',
    field_class=fields.CharField,
    read_only=True,
    default=SocialAuthCallbackURL('azuread-oauth2'),
    label=_('Azure AD OAuth2 Callback URL'),
    help_text=_('Register an Azure AD application as described by '
                'https://msdn.microsoft.com/en-us/library/azure/dn132599.aspx '
                'and obtain an OAuth2 key (Client ID) and secret (Client Secret). '
                'Provide this URL as the callback URL for your application.'),
    category=_('Azure AD OAuth2'),
    category_slug='azuread-oauth2',
)

register(
    'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('Azure AD OAuth2 Key'),
    help_text=_('The OAuth2 key (Client ID) from your Azure AD application.'),
    category=_('Azure AD OAuth2'),
    category_slug='azuread-oauth2',
)

register(
    'SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('Azure AD OAuth2 Secret'),
    help_text=_('The OAuth2 secret (Client Secret) from your Azure AD application.'),
    category=_('Azure AD OAuth2'),
    category_slug='azuread-oauth2',
)

register(
    'SOCIAL_AUTH_AZUREAD_OAUTH2_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
    allow_null=True,
    default=None,
    label=_('Azure AD OAuth2 Organization Map'),
    help_text=SOCIAL_AUTH_ORGANIZATION_MAP_HELP_TEXT,
    category=_('Azure AD OAuth2'),
    category_slug='azuread-oauth2',
    placeholder=SOCIAL_AUTH_ORGANIZATION_MAP_PLACEHOLDER,
)

register(
    'SOCIAL_AUTH_AZUREAD_OAUTH2_TEAM_MAP',
    field_class=fields.SocialTeamMapField,
    allow_null=True,
    default=None,
    label=_('Azure AD OAuth2 Team Map'),
    help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
    category=_('Azure AD OAuth2'),
    category_slug='azuread-oauth2',
    placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
)

###############################################################################
# SAML AUTHENTICATION SETTINGS
###############################################################################

def get_saml_metadata_url():
    return urlparse.urljoin(settings.TOWER_URL_BASE, reverse('sso:saml_metadata'))

register(
    'SOCIAL_AUTH_SAML_CALLBACK_URL',
    field_class=fields.CharField,
    read_only=True,
    default=SocialAuthCallbackURL('saml'),
    label=_('SAML Service Provider Callback URL'),
    help_text=_('Register Tower as a service provider (SP) with each identity '
                'provider (IdP) you have configured. Provide your SP Entity ID '
                'and this callback URL for your application.'),
    category=_('SAML'),
    category_slug='saml',
)

register(
    'SOCIAL_AUTH_SAML_METADATA_URL',
    field_class=fields.CharField,
    read_only=True,
    default=get_saml_metadata_url,
    label=_('SAML Service Provider Metadata URL'),
    help_text=_('If your identity provider (IdP) allows uploading an XML '
                'metadata file, you can download one from this URL.'),
    category=_('SAML'),
    category_slug='saml',
)

register(
    'SOCIAL_AUTH_SAML_SP_ENTITY_ID',
    field_class=fields.URLField,
    schemes=('http', 'https'),
    allow_blank=True,
    default='',
    label=_('SAML Service Provider Entity ID'),
    help_text=_('Set to a URL for a domain name you own (does not need to be a '
                'valid URL; only used as a unique ID).'),
    category=_('SAML'),
    category_slug='saml',
)

register(
    'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    validators=[validate_certificate],
    label=_('SAML Service Provider Public Certificate'),
    help_text=_('Create a keypair for Tower to use as a service provider (SP) '
                'and include the certificate content here.'),
    category=_('SAML'),
    category_slug='saml',
)

register(
    'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    validators=[validate_private_key],
    label=_('SAML Service Provider Private Key'),
    help_text=_('Create a keypair for Tower to use as a service provider (SP) '
                'and include the private key content here.'),
    category=_('SAML'),
    category_slug='saml',
)

register(
    'SOCIAL_AUTH_SAML_ORG_INFO',
    field_class=fields.SAMLOrgInfoField,
    default={},
    label=_('SAML Service Provider Organization Info'),
    help_text=_('Configure this setting with information about your app.'),
    category=_('SAML'),
    category_slug='saml',
    placeholder=collections.OrderedDict([
        ('en-US', collections.OrderedDict([
            ('name', 'example'),
            ('displayname', 'Example'),
            ('url', 'http://www.example.com'),
        ])),
    ]),
)

register(
    'SOCIAL_AUTH_SAML_TECHNICAL_CONTACT',
    field_class=fields.SAMLContactField,
    allow_blank=True,
    default={},
    label=_('SAML Service Provider Technical Contact'),
    help_text=_('Configure this setting with your contact information.'),
    category=_('SAML'),
    category_slug='saml',
    placeholder=collections.OrderedDict([
        ('givenName', 'Technical Contact'),
        ('emailAddress', 'techsup@example.com'),
    ]),
)

register(
    'SOCIAL_AUTH_SAML_SUPPORT_CONTACT',
    field_class=fields.SAMLContactField,
    allow_blank=True,
    default={},
    label=_('SAML Service Provider Support Contact'),
    help_text=_('Configure this setting with your contact information.'),
    category=_('SAML'),
    category_slug='saml',
    placeholder=collections.OrderedDict([
        ('givenName', 'Support Contact'),
        ('emailAddress', 'support@example.com'),
    ]),
)

register(
    'SOCIAL_AUTH_SAML_ENABLED_IDPS',
    field_class=fields.SAMLEnabledIdPsField,
    default={},
    label=_('SAML Enabled Identity Providers'),
    help_text=_('Configure the Entity ID, SSO URL and certificate for each '
                'identity provider (IdP) in use. Multiple SAML IdPs are supported. '
                'Some IdPs may provide user data using attribute names that differ '
                'from the default OIDs '
                '(https://github.com/omab/python-social-auth/blob/master/social/backends/saml.py#L16). '
                'Attribute names may be overridden for each IdP.'),
    category=_('SAML'),
    category_slug='saml',
    placeholder=collections.OrderedDict([
        ('Okta', collections.OrderedDict([
            ('entity_id', 'http://www.okta.com/HHniyLkaxk9e76wD0Thh'),
            ('url', 'https://dev-123456.oktapreview.com/app/ansibletower/HHniyLkaxk9e76wD0Thh/sso/saml'),
            ('x509cert', 'MIIDpDCCAoygAwIBAgIGAVVZ4rPzMA0GCSqGSIb3...'),
            ('attr_user_permanent_id', 'username'),
            ('attr_first_name', 'first_name'),
            ('attr_last_name', 'last_name'),
            ('attr_username', 'username'),
            ('attr_email', 'email'),
        ])),
        ('OneLogin', collections.OrderedDict([
            ('entity_id', 'https://app.onelogin.com/saml/metadata/123456'),
            ('url', 'https://example.onelogin.com/trust/saml2/http-post/sso/123456'),
            ('x509cert', 'MIIEJjCCAw6gAwIBAgIUfuSD54OPSBhndDHh3gZo...'),
            ('attr_user_permanent_id', 'name_id'),
            ('attr_first_name', 'User.FirstName'),
            ('attr_last_name', 'User.LastName'),
            ('attr_username', 'User.email'),
            ('attr_email', 'User.email'),
        ])),
    ]),
)

register(
    'SOCIAL_AUTH_SAML_ORGANIZATION_MAP',
    field_class=fields.SocialOrganizationMapField,
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
    field_class=fields.SocialTeamMapField,
    allow_null=True,
    default=None,
    label=_('SAML Team Map'),
    help_text=SOCIAL_AUTH_TEAM_MAP_HELP_TEXT,
    category=_('SAML'),
    category_slug='saml',
    placeholder=SOCIAL_AUTH_TEAM_MAP_PLACEHOLDER,
)
