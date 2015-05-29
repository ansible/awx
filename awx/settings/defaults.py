# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

import os
import sys
from datetime import timedelta

MONGO_DB = 'system_tracking'

# Update this module's local settings from the global settings module.
from django.conf import global_settings
this_module = sys.modules[__name__]
for setting in dir(global_settings):
    if setting == setting.upper():
        setattr(this_module, setting, getattr(global_settings, setting))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'awx.sqlite3'),
        # Test database cannot be :memory: for celery/inventory tests to work.
        'TEST_NAME': os.path.join(BASE_DIR, 'awx_test.sqlite3'),
        'ATOMIC_REQUESTS': True,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
#
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

USE_TZ = True

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'ui', 'dist'),
    os.path.join(BASE_DIR, 'static'),
)

# Absolute filesystem path to the directory where static file are collected via
# the collectstatic command.
STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
STATIC_URL = '/static/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'public', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory to host projects (with playbooks).
# This directory should not be web-accessible.
PROJECTS_ROOT = os.path.join(BASE_DIR, 'projects')

# Absolute filesystem path to the directory for job status stdout (default for
# development and tests, default for production defined in production.py). This
# directory should not be web-accessible
JOBOUTPUT_ROOT = os.path.join(BASE_DIR, 'job_output')

# Absolute filesystem path to the directory to store logs
LOG_ROOT = os.path.join(BASE_DIR)

# The heartbeat file for the tower scheduler
SCHEDULE_METADATA_LOCATION = os.path.join(BASE_DIR, '.tower_cycle')

# Maximum number of the same job that can be waiting to run when launching from scheduler
SCHEDULE_MAX_JOBS = 10

SITE_ID = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'p7z7g1ql4%6+(6nlebb6hdk7sd^&fnjpal308%n%+p^_e6vo1y'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# HTTP headers and meta keys to search to determine remote host name or IP. Add
# additional items to this list, such as "HTTP_X_FORWARDED_FOR", if behind a
# reverse proxy.
REMOTE_HOST_HEADERS = ['REMOTE_ADDR', 'REMOTE_HOST']

TEMPLATE_CONTEXT_PROCESSORS += (  # NOQA
    'django.core.context_processors.request',
    'awx.ui.context_processors.settings',
    'awx.ui.context_processors.version',
)

MIDDLEWARE_CLASSES += (  # NOQA
    'awx.main.middleware.HAMiddleware',
    'awx.main.middleware.ActivityStreamMiddleware',
    'crum.CurrentRequestUserMiddleware',
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

ROOT_URLCONF = 'awx.urls'

WSGI_APPLICATION = 'awx.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'south',
    'rest_framework',
    'django_extensions',
    'djcelery',
    'kombu.transport.django',
    'polymorphic',
    'taggit',
    'awx.main',
    'awx.api',
    'awx.ui',
    'awx.fact',
)

INTERNAL_IPS = ('127.0.0.1',)

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_SERIALIZER_CLASS': 'awx.api.pagination.PaginationSerializer',
    'PAGINATE_BY': 25,
    'PAGINATE_BY_PARAM': 'page_size',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'awx.api.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        #'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'awx.api.permissions.ModelAccessPermission',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'awx.api.filters.ActiveOnlyBackend',
        'awx.api.filters.TypeFilterBackend',
        'awx.api.filters.FieldLookupBackend',
        'rest_framework.filters.SearchFilter',
        'awx.api.filters.OrderByBackend',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'awx.api.renderers.BrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'awx.api.views.api_exception_handler',
    'VIEW_NAME_FUNCTION': 'awx.api.generics.get_view_name',
    'VIEW_DESCRIPTION_FUNCTION': 'awx.api.generics.get_view_description',
}

AUTHENTICATION_BACKENDS = (
    'awx.main.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# LDAP server (default to None to skip using LDAP authentication).
AUTH_LDAP_SERVER_URI = None

# Seconds before auth tokens expire.
AUTH_TOKEN_EXPIRATION = 1800

# If set, serve only minified JS for UI.
USE_MINIFIED_JS = False

# Email address that error messages come from.
SERVER_EMAIL = 'root@localhost'

# Default email address to use for various automated correspondence from
# the site managers.
DEFAULT_FROM_EMAIL = 'webmaster@localhost'

# Subject-line prefix for email messages send with django.core.mail.mail_admins
# or ...mail_managers.  Make sure to include the trailing space.
EMAIL_SUBJECT_PREFIX = '[AWX] '

# The email backend to use. For possible shortcuts see django.core.mail.
# The default is to use the SMTP backend.
# Third-party backends can be specified by providing a Python path
# to a module that defines an EmailBackend class.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Host for sending email.
EMAIL_HOST = 'localhost'

# Port for sending email.
EMAIL_PORT = 25

# Optional SMTP authentication information for EMAIL_HOST.
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

# Memcached django cache configuration
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': '127.0.0.1:11211',
#         'TIMEOUT': 864000,
#         'KEY_PREFIX': 'tower_dev',
#     }
# }

# Use Django-Debug-Toolbar if installed.
try:
    import debug_toolbar
    INSTALLED_APPS += (debug_toolbar.__name__,)
except ImportError:
    pass

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'ENABLE_STACKTRACES' : True,
}

# Use Django-devserver if installed.
try:
    import devserver
    INSTALLED_APPS += (devserver.__name__,)
except ImportError:
    pass

DEVSERVER_DEFAULT_ADDR = '0.0.0.0'
DEVSERVER_DEFAULT_PORT = '8013'
DEVSERVER_MODULES = (
    'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',
    #'devserver.modules.ajax.AjaxDumpModule',
    #'devserver.modules.profile.MemoryUseModule',
    #'devserver.modules.cache.CacheSummaryModule',
    #'devserver.modules.profile.LineProfilerModule',
)

# Set default ports for live server tests.
os.environ.setdefault('DJANGO_LIVE_TEST_SERVER_ADDRESS', 'localhost:9013-9199')

# Skip migrations when running tests.
SOUTH_TESTS_MIGRATE = False

# Initialize Django-Celery.
import djcelery
djcelery.setup_loader()

BROKER_URL = 'redis://localhost/'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TRACK_STARTED = True
CELERYD_TASK_TIME_LIMIT = None
CELERYD_TASK_SOFT_TIME_LIMIT = None
CELERYBEAT_SCHEDULER = 'celery.beat.PersistentScheduler'
CELERYBEAT_MAX_LOOP_INTERVAL = 60
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERYBEAT_SCHEDULE = {
    'tower_scheduler': {
        'task': 'awx.main.tasks.tower_periodic_scheduler',
        'schedule': timedelta(seconds=30)
    },
}

# Any ANSIBLE_* settings will be passed to the subprocess environment by the
# celery task.

# Do not want AWX to ask interactive questions and want it to be friendly with
# reprovisioning
ANSIBLE_HOST_KEY_CHECKING = False

# RHEL has too old of an SSH so ansible will select paramiko and this is VERY
# slow.
ANSIBLE_PARAMIKO_RECORD_HOST_KEYS = False

# Force ansible in color even if we don't have a TTY so we can properly colorize
# output
ANSIBLE_FORCE_COLOR = True

# Additional environment variables to be passed to the subprocess started by
# the celery task.
AWX_TASK_ENV = {}

# Maximum number of job events processed by the callback receiver worker process
# before it recycles
JOB_EVENT_RECYCLE_THRESHOLD = 3000

# Maximum number of job events that can be waiting on a single worker queue before
# it can be skipped as too busy
JOB_EVENT_MAX_QUEUE_SIZE = 100

# Flag to enable/disable updating hosts M2M when saving job events.
CAPTURE_JOB_EVENT_HOSTS = False

# Enable proot support for running jobs (playbook runs only).
AWX_PROOT_ENABLED = False

# Command/path to proot.
AWX_PROOT_CMD = 'proot'

# Additional paths to hide from jobs using proot.
AWX_PROOT_HIDE_PATHS = []

# Additional paths to show for jobs using proot.
AWX_PROOT_SHOW_PATHS = []

# Number of jobs to show as part of the job template history
AWX_JOB_TEMPLATE_HISTORY = 10

# Default list of modules allowed for ad hoc commands.
AD_HOC_COMMANDS = [
    'command',
    'shell',
    'yum',
    'apt',
    'apt_key',
    'apt_repository',
    'apt_rpm',
    'service',
    'group',
    'user',
    'mount',
    'ping',
    'selinux',
    'setup',
    'win_ping',
    'win_service',
    'win_updates',
    'win_group',
    'win_user',
]

# Not possible to get list of regions without authenticating, so use this list
# instead (based on docs from:
# http://docs.rackspace.com/loadbalancers/api/v1.0/clb-devguide/content/Service_Access_Endpoints-d1e517.html)
RAX_REGION_CHOICES = [
    ('ORD', 'Chicago'),
    ('DFW', 'Dallas/Ft. Worth'),
    ('IAD', 'Northern Virginia'),
    ('LON', 'London'),
    ('SYD', 'Sydney'),
    ('HKG', 'Hong Kong'),
]

# Inventory variable name/values for determining if host is active/enabled.
RAX_ENABLED_VAR = 'rax_status'
RAX_ENABLED_VALUE = 'ACTIVE'

# Inventory variable name containing unique instance ID.
RAX_INSTANCE_ID_VAR = 'rax_id'

# Filter for allowed group/host names when importing inventory from Rackspace.
# By default, filter group of one created for each instance and exclude all
# groups without children, hosts and variables.
RAX_GROUP_FILTER = r'^(?!instance-.+).+$'
RAX_HOST_FILTER = r'^.+$'
RAX_EXCLUDE_EMPTY_GROUPS = True

INV_ENV_VARIABLE_BLACKLIST = ("HOME", "USER", "_", "TERM")

# ----------------
# -- Amazon EC2 --
# ----------------

# AWS does not appear to provide pretty region names via any API, so store the
# list of names here.  The available region IDs will be pulled from boto.
# http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region
EC2_REGION_NAMES = {
    'us-east-1': 'US East (Northern Virginia)',
    'us-west-2': 'US West (Oregon)',
    'us-west-1': 'US West (Northern California)',
    'eu-central-1': 'EU (Frankfurt)',
    'eu-west-1': 'EU (Ireland)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'sa-east-1': 'South America (Sao Paulo)',
    'us-gov-west-1': 'US West (GovCloud)',
    'cn-north-1': 'China (Beijing)',
}

EC2_REGIONS_BLACKLIST = [
    'us-gov-west-1',
    'cn-north-1',
]

# Inventory variable name/values for determining if host is active/enabled.
EC2_ENABLED_VAR = 'ec2_state'
EC2_ENABLED_VALUE = 'running'

# Inventory variable name containing unique instance ID.
EC2_INSTANCE_ID_VAR = 'ec2_id'

# Filter for allowed group/host names when importing inventory from EC2.
EC2_GROUP_FILTER = r'^.+$'
EC2_HOST_FILTER = r'^.+$'
EC2_EXCLUDE_EMPTY_GROUPS = True


# ------------
# -- VMware --
# ------------
VMWARE_REGIONS_BLACKLIST = []

# Inventory variable name/values for determining whether a host is
# active in vSphere.
VMWARE_ENABLED_VAR = 'vmware_powerState'
VMWARE_ENABLED_VALUE = 'poweredOn'

# Inventory variable name containing the unique instance ID.
VMWARE_INSTANCE_ID_VAR = 'vmware_uuid'

# Filter for allowed group and host names when importing inventory
# from VMware.
VMWARE_GROUP_FILTER = r'^.+$'
VMWARE_HOST_FILTER = r'^.+$'
VMWARE_EXCLUDE_EMPTY_GROUPS = True


# ---------------------------
# -- Google Compute Engine --
# ---------------------------

# It's not possible to get zones in GCE without authenticating, so we
# provide a list here.
# Source: https://developers.google.com/compute/docs/zones
GCE_REGION_CHOICES = [
    ('us-central1-a', 'US Central (A)'),
    ('us-central1-b', 'US Central (B)'),
    ('us-central1-f', 'US Central (F)'),
    ('europe-west1-a', 'Europe West (A)'),
    ('europe-west1-b', 'Europe West (B)'),
    ('asia-east1-a', 'Asia East (A)'),
    ('asia-east1-b', 'Asia East (B)'),
]
GCE_REGIONS_BLACKLIST = []

# Inventory variable name/value for determining whether a host is active
# in Google Compute Engine.
GCE_ENABLED_VAR = 'status'
GCE_ENABLED_VALUE = 'running'

# Filter for allowed group and host names when importing inventory from
# Google Compute Engine.
GCE_GROUP_FILTER = r'^.+$'
GCE_HOST_FILTER = r'^.+$'
GCE_EXCLUDE_EMPTY_GROUPS = True
GCE_INSTANCE_ID_VAR = None


# -------------------
# -- Microsoft Azure --
# -------------------

# It's not possible to get zones in Azure without authenticating, so we
# provide a list here.
AZURE_REGION_CHOICES = [
    ('Central_US', 'US Central'),
    ('East_US_1', 'US East'),
    ('East_US_2', 'US East 2'),
    ('North_Central_US', 'US North Central'),
    ('South_Central_US', 'US South Central'),
    ('West_US', 'US West'),
    ('North_Europe', 'Europe North'),
    ('West_Europe', 'Europe West'),
    ('East_Asia_Pacific', 'Asia Pacific East'),
    ('Southest_Asia_Pacific', 'Asia Pacific Southeast'),
    ('East_Japan', 'Japan East'),
    ('West_Japan', 'Japan West'),
    ('South_Brazil', 'Brazil South'),
]
AZURE_REGIONS_BLACKLIST = []

# Inventory variable name/value for determining whether a host is active
# in Microsoft Azure.
AZURE_ENABLED_VAR = 'instance_status'
AZURE_ENABLED_VALUE = 'ReadyRole'

# Filter for allowed group and host names when importing inventory from
# Microsoft Azure.
AZURE_GROUP_FILTER = r'^.+$'
AZURE_HOST_FILTER = r'^.+$'
AZURE_EXCLUDE_EMPTY_GROUPS = True
AZURE_INSTANCE_ID_VAR = 'private_id'

# ---------------------
# ----- OpenStack -----
# ---------------------
OPENSTACK_ENABLED_VAR = 'status'
OPENSTACK_ENABLED_VALUE = 'ACTIVE'
OPENSTACK_GROUP_FILTER = r'^.+$'
OPENSTACK_HOST_FILTER = r'^.+$'
OPENSTACK_EXCLUDE_EMPTY_GROUPS = True
OPENSTACK_INSTANCE_ID_VAR = "id"

# ---------------------
# -- Activity Stream --
# ---------------------
# Defaults for enabling/disabling activity stream.
ACTIVITY_STREAM_ENABLED = True
ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC = False

# Internal API URL for use by inventory scripts and callback plugin.
if 'devserver' in INSTALLED_APPS:
    INTERNAL_API_URL = 'http://127.0.0.1:%s' % DEVSERVER_DEFAULT_PORT
else:
    INTERNAL_API_URL = 'http://127.0.0.1:8000'

# ZeroMQ callback settings.
CALLBACK_CONSUMER_PORT = "tcp://127.0.0.1:5556"
CALLBACK_QUEUE_PORT = "ipc:///tmp/callback_receiver.ipc"

TASK_COMMAND_PORT = 6559

SOCKETIO_NOTIFICATION_PORT = 6557
SOCKETIO_LISTEN_PORT = 8080

FACT_CACHE_PORT = 6564

ORG_ADMINS_CAN_SEE_ALL_USERS = True

# Logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'awx.lib.compat.RequireDebugTrue',
        },
        'require_debug_true_or_test': {
            '()': 'awx.main.utils.RequireDebugTrueOrTest',
        },
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)-8s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true_or_test'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'class': 'django.utils.log.NullHandler',
        },
        'file': {
            'class': 'django.utils.log.NullHandler',
            'formatter': 'simple',
        },
        'syslog': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.NullHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'tower_warnings': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'tower_warnings.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'callback_receiver': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'callback_receiver.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'socketio_service': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'socketio_service.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'task_system': {
            'level': 'INFO',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'task_system.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
        },
        'django.request': {
            'handlers': ['mail_admins', 'console', 'file', 'tower_warnings'],
            'level': 'WARNING',
            'propagate': False,
        },
        'rest_framework.request': {
            'handlers': ['mail_admins', 'console', 'file', 'tower_warnings'],
            'level': 'WARNING',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
        },
        'awx': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'DEBUG',
        },
        'awx.main.commands.run_callback_receiver': {
            'handlers': ['console', 'file', 'callback_receiver'],
            'propagate': False
        },
        'awx.main.commands.run_socketio_service': {
            'handlers': ['console', 'file', 'socketio_service'],
            'propagate': False
        },
        'awx.main.commands.run_task_system': {
            'handlers': ['console', 'file', 'task_system'],
            'propagate': False
        },
        'awx.main.access': {
            'handlers': ['null'],
            'propagate': False,
        },
        'awx.main.signals': {
            'handlers': ['null'],
            'propagate': False,
        },
        'awx.api.permissions': {
            'handlers': ['null'],
            'propagate': False,
        },
        'django_auth_ldap': {
            'handlers': ['null'],
        },
    }
}
