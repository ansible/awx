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

# AnsibleWorks AWX can be configured to centrally use LDAP as a source for
# authentication information.  When so configured, a user who logs in with
# a LDAP username and password will automatically get an AWX account created
# for them, and they can be automatically placed into multiple organizations
# as either regular users or organization administrators.  If users are created
# via an LDAP login, by default they cannot change their username, firstname,
# lastname, or set a local password for themselves. This is also tunable
# to restrict editing of other field names.

# For more information about these various settings, advanced users may refer
# to django-auth-ldap docs, though this should not be neccessary for most
# users: http://pythonhosted.org/django-auth-ldap/authentication.html

# LDAP server URI, such as "ldap://ldap.example.com:389" (non-SSL) or
# "ldaps://ldap.example.com:636" (SSL).  LDAP authentication is disabled if this
# parameter is empty.

AUTH_LDAP_SERVER_URI = ''

# DN (Distinguished Name) of user to bind for all search queries. Normally in the format
# "CN=Some User,OU=Users,DC=example,DC=com" but may also be specified as
# "DOMAIN\username" for Active Directory. This is the system user account 
# we will use to login to query LDAP for other user information.

AUTH_LDAP_BIND_DN = ''

# Password using to bind above user account.

AUTH_LDAP_BIND_PASSWORD = ''

# Whether to enable TLS when the LDAP connection is not using SSL.

AUTH_LDAP_START_TLS = False

# Imports needed for remaining LDAP configuration.
# do not alter this section

import ldap
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
from django_auth_ldap.config import ActiveDirectoryGroupType

# LDAP search query to find users.  Any user that matches the pattern
# below will be able to login to AWX.  The user should also be mapped
# into an AWX organization (as defined later on in this file).  If multiple
# search queries need to be supported use of "LDAPUnion" is possible. See
# python-ldap documentation as linked at the top of this section.

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    'OU=Users,DC=example,DC=com',   # Base DN
    ldap.SCOPE_SUBTREE,             # SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE
    '(sAMAccountName=%(user)s)',    # Query
)

# Alternative to user search, if user DNs are all of the same format. This will be
# more efficient for lookups than the above system if it is usable in your organizational
# environment. If this setting has a value it will be used instead of AUTH_LDAP_USER_SEARCH
# above.

#AUTH_LDAP_USER_DN_TEMPLATE = 'uid=%(user)s,OU=Users,DC=example,DC=com'

# Mapping of LDAP user schema to AWX API user atrributes (key is user attribute name, value is LDAP
# attribute name).  The default setting in this configuration file is valid for ActiveDirectory but
# users with other LDAP configurations may need to change the values (not the keys) of the dictionary/hash-table
# below.

AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}

# Users in AWX are mapped to organizations based on their membership in LDAP groups.  The following setting defines
# the LDAP search query to find groups. Note that this, unlike the user search above, does not support LDAPSearchUnion.

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'DC=example,DC=com',    # Base DN
    ldap.SCOPE_SUBTREE,     # SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE
    '(objectClass=group)',  # Query
)

# The group type import may need to be changed based on the type of the LDAP server.
# Values are listed at: http://pythonhosted.org/django-auth-ldap/groups.html#types-of-groups

AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

# Group DN required to login. If specified, user must be a member of this
# group to login via LDAP.  If not set, everyone in LDAP that matches the
# user search defined above will be able to login via AWX.  Only one 
# require group is supported.

#AUTH_LDAP_REQUIRE_GROUP = ''

# Group DN denied from login. If specified, user will not be allowed to login
# if a member of this group.  Only one deny group is supported.

#AUTH_LDAP_DENY_GROUP = ''

# User profile flags updated from group membership (key is user attribute name,
# value is group DN).  These are boolean fields that are matched based on
# whether the user is a member of the given group.  So far only is_superuser
# is settable via this method.  This flag is set both true and false at login
# time based on current LDAP settings.

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    #'is_superuser': 'CN=Domain Admins,CN=Users,DC=example,DC=com',
}

# Mapping between organization admins/users and LDAP groups. This controls what
# users are placed into what AWX organizations relative to their LDAP group
# memberships. Keys are organization names.  Organizations will be created if not present.  
# Values are dictionaries defining the options for each organization's membership.  For each organization 
# it is possible to specify what groups are automatically users of the organization and also what
# groups can administer the organization.  
#
# - admins: None, True/False, string or list/tuple of strings.
#   If None, organization admins will not be updated based on LDAP values.
#   If True, all users in LDAP will automatically be added as admins of the organization.
#   If False, no LDAP users will be automatically added as admins of the organiation.
#   If a string or list of strings, specifies the group DN(s) that will be added of the organization if they match
#   any of the specified groups.
# - remove_admins: True/False. Defaults to False. 
#   If True, a user who is not an member of the given groups will be removed from the organization's administrative list.
# - users: None, True/False, string or list/tuple of strings. Same rules apply
#   as for admins.
# - remove_users: True/False. Defaults to False. Same rules as apply for remove_admins

AUTH_LDAP_ORGANIZATION_MAP = {
    #'Test Org': {
    #    'admins': 'CN=Domain Admins,CN=Users,DC=example,DC=com',
    #    'users': ['CN=Domain Users,CN=Users,DC=example,DC=com'],
    #    'remove_users' : False,
    #    'remove_admins' : False,
    #},
    #'Test Org 2': {
    #    'admins': ['CN=Administrators,CN=Builtin,DC=example,DC=com'],
    #    'users': True,
    #    'remove_users' : False,
    #    'remove_admins' : False,
    #},
}
