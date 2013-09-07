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

LOGGING['handlers']['syslog'] = {
    # ERROR captures 500 errors, WARNING also logs 4xx responses.
    'level': 'ERROR',
    'filters': ['require_debug_false'],
    'class': 'logging.handlers.SysLogHandler',
    'address': '/dev/log',
    'facility': 'local0',
    'formatter': 'simple',
}

AWX_TASK_ENV['HOME'] = '/var/lib/awx'
AWX_TASK_ENV['USER'] = 'awx'

SERVER_EMAIL = 'root@localhost'
DEFAULT_FROM_EMAIL = 'webmaster@localhost'
EMAIL_SUBJECT_PREFIX = '[AnsibleWorks] '

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

# LDAP connection and authentication settings.  Refer to django-auth-ldap docs:
# http://pythonhosted.org/django-auth-ldap/authentication.html

AUTH_LDAP_SERVER_URI = ''
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_START_TLS = False

#import ldap
#from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion

# LDAP search query to find users.
#AUTH_LDAP_USER_SEARCH = LDAPSearch(
#    'OU=Users,DC=example,DC=com',
#    ldap.SCOPE_SUBTREE,
#    '(sAMAccountName=%(user)s)',
#)

# Alternative to user search.
#AUTH_LDAP_USER_DN_TEMPLATE = 'sAMAccountName=%(user)s,OU=Users,DC=example,DC=com'

# Mapping of LDAP attributes to user attributes.
#AUTH_LDAP_USER_ATTR_MAP = {
#    'first_name': 'givenName',
#    'last_name': 'sn',
#    'email': 'mail',
#}
