###############################################################################
# MISC PROJECT SETTINGS
###############################################################################

ADMINS = (
   #('Joe Admin', 'joeadmin@example.com'),
)

DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
       'NAME': 'awx',
       'USER': 'awx',
       'PASSWORD': 'AWsecret',
       'HOST': '',
       'PORT': '',
   }
}

# Use SQLite for unit tests instead of PostgreSQL.
if len(sys.argv) >= 2 and sys.argv[1] == 'test':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'var/lib/awx/awx.sqlite3',
            # Test database cannot be :memory: for celery/inventory tests.
            'TEST_NAME': '/var/lib/awx/awx_test.sqlite3',
        }
    }

STATIC_ROOT = '/var/lib/awx/public/static'

PROJECTS_ROOT = '/var/lib/awx/projects'

SECRET_KEY = file('/etc/awx/SECRET_KEY', 'rb').read().strip()

ALLOWED_HOSTS = ['*']

AWX_TASK_ENV['HOME'] = '/var/lib/awx'
AWX_TASK_ENV['USER'] = 'awx'

###############################################################################
# EMAIL SETTINGS
###############################################################################

SERVER_EMAIL = 'root@localhost'
DEFAULT_FROM_EMAIL = 'webmaster@localhost'
EMAIL_SUBJECT_PREFIX = '[AnsibleWorks] '

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

###############################################################################
# LOGGING SETTINGS
###############################################################################

LOGGING['handlers']['syslog'] = {
    # ERROR captures 500 errors, WARNING also logs 4xx responses.
    'level': 'ERROR',
    'filters': ['require_debug_false'],
    'class': 'logging.handlers.SysLogHandler',
    'address': '/dev/log',
    'facility': 'local0',
    'formatter': 'simple',
}

###############################################################################
# LDAP AUTHENTICATION SETTINGS
###############################################################################

# Refer to django-auth-ldap docs for more details:
# http://pythonhosted.org/django-auth-ldap/authentication.html

# LDAP server URI, such as "ldap://ldap.example.com:389" (non-SSL) or
# "ldaps://ldap.example.com:636" (SSL).  LDAP authentication is disable if this
# parameter is empty.
AUTH_LDAP_SERVER_URI = ''

# DN of user to bind for all search queries. Normally in the format
# "CN=Some User,OU=Users,DC=example,DC=com" but may also be specified as
# "DOMAIN\username" for Active Directory.
AUTH_LDAP_BIND_DN = ''

# Password using to bind above user account.
AUTH_LDAP_BIND_PASSWORD = ''

# Enable TLS when the connection is not using SSL.
AUTH_LDAP_START_TLS = False

# Imports needed for remaining LDAP configuration.
import ldap
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
from django_auth_ldap.config import ActiveDirectoryGroupType

# LDAP search query to find users.
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    'OU=Users,DC=example,DC=com',   # Base DN
    ldap.SCOPE_SUBTREE,             # SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE
    '(sAMAccountName=%(user)s)',    # Query
)

# Alternative to user search, if user DNs are all of the same format.
#AUTH_LDAP_USER_DN_TEMPLATE = 'uid=%(user)s,OU=Users,DC=example,DC=com'

# Mapping of LDAP to user atrributes (key is user attribute name, value is LDAP
# attribute name).
AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}

# LDAP search query to find groups. Does not support LDAPSearchUnion.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'DC=example,DC=com',    # Base DN
    ldap.SCOPE_SUBTREE,     # SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE
    '(objectClass=group)',  # Query
)
# Type of group returned by the search above. Should be one of the types
# listed at: http://pythonhosted.org/django-auth-ldap/groups.html#types-of-groups
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

# Group DN required to login. If specified, user must be a member of this
# group to login via LDAP.
AUTH_LDAP_REQUIRE_GROUP = ''

# Group DN denied from login. If specified, user will not be allowed to login
# if a member of this group.
AUTH_LDAP_DENY_GROUP = ''

# User profile flags updated from group membership (key is user attribute name,
# value is group DN).
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    #'is_superuser': 'CN=Domain Admins,CN=Users,DC=example,DC=com',
}

# Mapping between organization admins/users and LDAP groups. Keys are
# organization names (will be created if not present). Values are dictionaries
# of options for each organization's membership, where each can contain the
# following parameters:
# - remove: True/False. Defaults to False. Specifies the default for
#   remove_admins or remove_users if those parameters aren't explicitly set.
# - admins: None, True/False, string or list/tuple of strings.
#   If None, organization admins will not be updated.
#   If True/False, all LDAP users will be added/removed as admins.
#   If a string or list of strings, specifies the group DN(s). User will be
#   added as an org admin if the user is a member of ANY of these groups.
# - remove_admins: True/False. Defaults to False. If True, a user who is not an
#   member of the given groups will be removed from the organization's admins.
# - users: None, True/False, string or list/tuple of strings. Same rules apply
#   as for admins.
# - remove_users: True/False. Defaults to False. If True, a user who is not a
#   member of the given groups will be removed from the organization's users.
AUTH_LDAP_ORGANIZATION_MAP = {
    #'Test Org': {
    #    'admins': 'CN=Domain Admins,CN=Users,DC=example,DC=com',
    #    'users': ['CN=Domain Users,CN=Users,DC=example,DC=com'],
    #},
    #'Test Org 2': {
    #    'admins': ['CN=Administrators,CN=Builtin,DC=example,DC=com'],
    #    'users': True,
    #},
}
