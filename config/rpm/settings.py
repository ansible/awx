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
    'level': 'ERROR',
    'filters': ['require_debug_false'],
    'class': 'logging.handlers.SysLogHandler',
    'address': '/dev/log',
    'facility': 'local0',
    'formatter': 'simple',
}

SERVER_EMAIL = 'root@localhost'
DEFAULT_FROM_EMAIL = 'webmaster@localhost'
EMAIL_SUBJECT_PREFIX = '[AnsibleWorks] '

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
