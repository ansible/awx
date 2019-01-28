# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import os
import re  # noqa
import sys
from datetime import timedelta

# global settings
from django.conf import global_settings
# ugettext lazy
from django.utils.translation import ugettext_lazy as _

# Update this module's local settings from the global settings module.
this_module = sys.modules[__name__]
for setting in dir(global_settings):
    if setting == setting.upper():
        setattr(this_module, setting, getattr(global_settings, setting))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def is_testing(argv=None):
    import sys
    '''Return True if running django or py.test unit tests.'''
    if 'PYTEST_CURRENT_TEST' in os.environ.keys():
        return True
    argv = sys.argv if argv is None else argv
    if len(argv) >= 1 and ('py.test' in argv[0] or 'py/test.py' in argv[0]):
        return True
    elif len(argv) >= 2 and argv[1] == 'test':
        return True
    return False


def IS_TESTING(argv=None):
    return is_testing(argv)


if "pytest" in sys.modules:
    from unittest import mock
    with mock.patch('__main__.__builtins__.dir', return_value=[]):
        import ldap
else:
    import ldap

DEBUG = True
SQL_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'awx.sqlite3'),
        'ATOMIC_REQUESTS': True,
        'TEST': {
            # Test database cannot be :memory: for inventory tests.
            'NAME': os.path.join(BASE_DIR, 'awx_test.sqlite3'),
        },
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
TIME_ZONE = 'UTC'

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
    os.path.join(BASE_DIR, 'ui', 'static'),
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

LOGIN_URL = '/api/login/'

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

# Django gettext files path: locale/<lang-code>/LC_MESSAGES/django.po, django.mo
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Graph of resources that can have named-url
NAMED_URL_GRAPH = {}

# Maximum number of the same job that can be waiting to run when launching from scheduler
# Note: This setting may be overridden by database settings.
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

# If Tower is behind a reverse proxy/load balancer, use this setting to
# whitelist the proxy IP addresses from which Tower should trust custom
# REMOTE_HOST_HEADERS header values
# REMOTE_HOST_HEADERS = ['HTTP_X_FORWARDED_FOR', ''REMOTE_ADDR', 'REMOTE_HOST']
# PROXY_IP_WHITELIST = ['10.0.1.100', '10.0.1.101']
# If this setting is an empty list (the default), the headers specified by
# REMOTE_HOST_HEADERS will be trusted unconditionally')
PROXY_IP_WHITELIST = []

# Note: This setting may be overridden by database settings.
STDOUT_MAX_BYTES_DISPLAY = 1048576

# Returned in the header on event api lists as a recommendation to the UI
# on how many events to display before truncating/hiding
MAX_UI_JOB_EVENTS = 4000

# Returned in index.html, tells the UI if it should make requests
# to update job data in response to status changes websocket events
UI_LIVE_UPDATES_ENABLED = True

# The maximum size of the ansible callback event's res data structure
# beyond this limit and the value will be removed
MAX_EVENT_RES_DATA = 700000

# Note: This setting may be overridden by database settings.
EVENT_STDOUT_MAX_BYTES_DISPLAY = 1024

# The amount of time before a stdout file is expired and removed locally
# Note that this can be recreated if the stdout is downloaded
LOCAL_STDOUT_EXPIRE_TIME = 2592000

# The number of processes spawned by the callback receiver to process job
# events into the database
JOB_EVENT_WORKERS = 4

# The maximum size of the job event worker queue before requests are blocked
JOB_EVENT_MAX_QUEUE_SIZE = 10000

# Disallow sending session cookies over insecure connections
SESSION_COOKIE_SECURE = True

# Seconds before sessions expire.
# Note: This setting may be overridden by database settings.
SESSION_COOKIE_AGE = 1800

# Maximum number of per-user valid, concurrent sessions.
# -1 is unlimited
# Note: This setting may be overridden by database settings.
SESSIONS_PER_USER = -1

CSRF_USE_SESSIONS = False

# Disallow sending csrf cookies over insecure connections
CSRF_COOKIE_SECURE = True

# Limit CSRF cookies to browser sessions
CSRF_COOKIE_AGE = None

TEMPLATES = [
    {
        'NAME': 'default',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [# NOQA
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'awx.ui.context_processors.settings',
                'awx.ui.context_processors.version',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
            'loaders': [(
                'django.template.loaders.cached.Loader',
                ('django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',),
            )],
            'builtins': ['awx.main.templatetags.swagger'],
        },
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
    },
]

MIDDLEWARE_CLASSES = (  # NOQA
    'awx.main.middleware.TimingMiddleware',
    'awx.main.middleware.MigrationRanCheckMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'awx.main.middleware.ActivityStreamMiddleware',
    'awx.sso.middleware.SocialAuthMiddleware',
    'crum.CurrentRequestUserMiddleware',
    'awx.main.middleware.URLModificationMiddleware',
    'awx.main.middleware.SessionTimeoutMiddleware',
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
    'oauth2_provider',
    'rest_framework',
    'django_extensions',
    'channels',
    'polymorphic',
    'taggit',
    'social_django',
    'corsheaders',
    'awx.conf',
    'awx.main',
    'awx.api',
    'awx.ui',
    'awx.sso',
    'solo'
)

INTERNAL_IPS = ('127.0.0.1',)

MAX_PAGE_SIZE = 200
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'awx.api.pagination.Pagination',
    'PAGE_SIZE': 25,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'awx.api.authentication.LoggedOAuth2Authentication',
        'awx.api.authentication.SessionAuthentication',
        'awx.api.authentication.LoggedBasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'awx.api.permissions.ModelAccessPermission',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'awx.api.filters.TypeFilterBackend',
        'awx.api.filters.FieldLookupBackend',
        'rest_framework.filters.SearchFilter',
        'awx.api.filters.OrderByBackend',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'awx.api.parsers.JSONParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'awx.api.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_METADATA_CLASS': 'awx.api.metadata.Metadata',
    'EXCEPTION_HANDLER': 'awx.api.views.api_exception_handler',
    'VIEW_NAME_FUNCTION': 'awx.api.generics.get_view_name',
    'VIEW_DESCRIPTION_FUNCTION': 'awx.api.generics.get_view_description',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'DEFAULT_VERSION': 'v2',
    #'URL_FORMAT_OVERRIDE': None,
}

AUTHENTICATION_BACKENDS = (
    'awx.sso.backends.LDAPBackend',
    'awx.sso.backends.LDAPBackend1',
    'awx.sso.backends.LDAPBackend2',
    'awx.sso.backends.LDAPBackend3',
    'awx.sso.backends.LDAPBackend4',
    'awx.sso.backends.LDAPBackend5',
    'awx.sso.backends.RADIUSBackend',
    'awx.sso.backends.TACACSPlusBackend',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.github.GithubOrganizationOAuth2',
    'social_core.backends.github.GithubTeamOAuth2',
    'social_core.backends.azuread.AzureADOAuth2',
    'awx.sso.backends.SAMLAuth',
    'django.contrib.auth.backends.ModelBackend',
)


# Django OAuth Toolkit settings
OAUTH2_PROVIDER_APPLICATION_MODEL = 'main.OAuth2Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'main.OAuth2AccessToken'
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'

OAUTH2_PROVIDER = {'ACCESS_TOKEN_EXPIRE_SECONDS': 31536000000,
                   'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600}
ALLOW_OAUTH2_FOR_EXTERNAL_USERS = False

# LDAP server (default to None to skip using LDAP authentication).
# Note: This setting may be overridden by database settings.
AUTH_LDAP_SERVER_URI = None

# Disable LDAP referrals by default (to prevent certain LDAP queries from
# hanging with AD).
# Note: This setting may be overridden by database settings.
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
    ldap.OPT_NETWORK_TIMEOUT: 30
}

# Radius server settings (default to empty string to skip using Radius auth).
# Note: These settings may be overridden by database settings.
RADIUS_SERVER = ''
RADIUS_PORT = 1812
RADIUS_SECRET = ''

# TACACS+ settings (default host to empty string to skip using TACACS+ auth).
# Note: These settings may be overridden by database settings.
TACACSPLUS_HOST = ''
TACACSPLUS_PORT = 49
TACACSPLUS_SECRET = ''
TACACSPLUS_SESSION_TIMEOUT = 5
TACACSPLUS_AUTH_PROTOCOL = 'ascii'

# Enable / Disable HTTP Basic Authentication used in the API browser
# Note: Session limits are not enforced when using HTTP Basic Authentication.
# Note: This setting may be overridden by database settings.
AUTH_BASIC_ENABLED = True

# If set, serve only minified JS for UI.
USE_MINIFIED_JS = False

# Email address that error messages come from.
SERVER_EMAIL = 'root@localhost'

# Default email address to use for various automated correspondence from
# the site managers.
DEFAULT_FROM_EMAIL = 'tower@localhost'

# Subject-line prefix for email messages send with django.core.mail.mail_admins
# or ...mail_managers.  Make sure to include the trailing space.
EMAIL_SUBJECT_PREFIX = '[Tower] '

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

# The number of seconds to sleep between status checks for jobs running on isolated nodes
AWX_ISOLATED_CHECK_INTERVAL = 30

# The timeout (in seconds) for launching jobs on isolated nodes
AWX_ISOLATED_LAUNCH_TIMEOUT = 600

# Ansible connection timeout (in seconds) for communicating with isolated instances
AWX_ISOLATED_CONNECTION_TIMEOUT = 10

# The time (in seconds) between the periodic isolated heartbeat status check
AWX_ISOLATED_PERIODIC_CHECK = 600

# Verbosity level for isolated node management tasks
AWX_ISOLATED_VERBOSITY = 0

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

DEVSERVER_DEFAULT_ADDR = '0.0.0.0'
DEVSERVER_DEFAULT_PORT = '8013'

# Set default ports for live server tests.
os.environ.setdefault('DJANGO_LIVE_TEST_SERVER_ADDRESS', 'localhost:9013-9199')

BROKER_POOL_LIMIT = None
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_DEFAULT_QUEUE = 'awx_private_queue'
CELERYBEAT_SCHEDULE = {
    'tower_scheduler': {
        'task': 'awx.main.tasks.awx_periodic_scheduler',
        'schedule': timedelta(seconds=30),
        'options': {'expires': 20,}
    },
    'admin_checks': {
        'task': 'awx.main.tasks.run_administrative_checks',
        'schedule': timedelta(days=30)
    },
    'cluster_heartbeat': {
        'task': 'awx.main.tasks.cluster_node_heartbeat',
        'schedule': timedelta(seconds=60),
        'options': {'expires': 50,}
    },
    'purge_stdout_files': {
        'task': 'awx.main.tasks.purge_old_stdout_files',
        'schedule': timedelta(days=7)
    },
    'gather_analytics': {
        'task': 'awx.main.tasks.gather_analytics',
        'schedule': timedelta(days=1)
    },
    'task_manager': {
        'task': 'awx.main.scheduler.tasks.run_task_manager',
        'schedule': timedelta(seconds=20),
        'options': {'expires': 20}
    },
    'isolated_heartbeat': {
        'task': 'awx.main.tasks.awx_isolated_heartbeat',
        'schedule': timedelta(seconds=AWX_ISOLATED_PERIODIC_CHECK),
        'options': {'expires': AWX_ISOLATED_PERIODIC_CHECK * 2},
    }
}
AWX_INCONSISTENT_TASK_INTERVAL = 60 * 3

AWX_CELERY_QUEUES_STATIC = [
    CELERY_DEFAULT_QUEUE,
]

AWX_CELERY_BCAST_QUEUES_STATIC = [
    'tower_broadcast_all',
]

ASGI_AMQP = {
    'INIT_FUNC': 'awx.prepare_env',
    'MODEL': 'awx.main.models.channels.ChannelGroup',
}

# Django Caching Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
    },
}

# Social Auth configuration.
SOCIAL_AUTH_STRATEGY = 'social_django.strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL  # noqa

_SOCIAL_AUTH_PIPELINE_BASE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'awx.sso.pipeline.check_user_found_or_created',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'awx.sso.pipeline.set_is_active_for_new_user',
    'social_core.pipeline.user.user_details',
    'awx.sso.pipeline.prevent_inactive_login',
)
SOCIAL_AUTH_PIPELINE = _SOCIAL_AUTH_PIPELINE_BASE + (
    'awx.sso.pipeline.update_user_orgs',
    'awx.sso.pipeline.update_user_teams',
)
SOCIAL_AUTH_SAML_PIPELINE = _SOCIAL_AUTH_PIPELINE_BASE + (
    'awx.sso.pipeline.update_user_orgs_by_saml_attr',
    'awx.sso.pipeline.update_user_teams_by_saml_attr',
    'awx.sso.pipeline.update_user_orgs',
    'awx.sso.pipeline.update_user_teams',
)

SOCIAL_AUTH_LOGIN_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/sso/complete/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/sso/error/'
SOCIAL_AUTH_INACTIVE_USER_URL = '/sso/inactive/'

SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = False
#SOCIAL_AUTH_SLUGIFY_USERNAMES = True
SOCIAL_AUTH_CLEAN_USERNAMES = True

SOCIAL_AUTH_SANITIZE_REDIRECTS = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False

# Note: These settings may be overridden by database settings.
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['profile']

SOCIAL_AUTH_GITHUB_KEY = ''
SOCIAL_AUTH_GITHUB_SECRET = ''
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email', 'read:org']

SOCIAL_AUTH_GITHUB_ORG_KEY = ''
SOCIAL_AUTH_GITHUB_ORG_SECRET = ''
SOCIAL_AUTH_GITHUB_ORG_NAME = ''
SOCIAL_AUTH_GITHUB_ORG_SCOPE = ['user:email', 'read:org']

SOCIAL_AUTH_GITHUB_TEAM_KEY = ''
SOCIAL_AUTH_GITHUB_TEAM_SECRET = ''
SOCIAL_AUTH_GITHUB_TEAM_ID = ''
SOCIAL_AUTH_GITHUB_TEAM_SCOPE = ['user:email', 'read:org']

SOCIAL_AUTH_AZUREAD_OAUTH2_KEY = ''
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET = ''

SOCIAL_AUTH_SAML_SP_ENTITY_ID = ''
SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = ''
SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = ''
SOCIAL_AUTH_SAML_ORG_INFO = {}
SOCIAL_AUTH_SAML_TECHNICAL_CONTACT = {}
SOCIAL_AUTH_SAML_SUPPORT_CONTACT = {}
SOCIAL_AUTH_SAML_ENABLED_IDPS = {}

SOCIAL_AUTH_SAML_ORGANIZATION_ATTR = {}
SOCIAL_AUTH_SAML_TEAM_ATTR = {}

# Any ANSIBLE_* settings will be passed to the task runner subprocess
# environment

# Do not want AWX to ask interactive questions and want it to be friendly with
# reprovisioning
ANSIBLE_HOST_KEY_CHECKING = False

# RHEL has too old of an SSH so ansible will select paramiko and this is VERY
# slow.
ANSIBLE_PARAMIKO_RECORD_HOST_KEYS = False

# Force ansible in color even if we don't have a TTY so we can properly colorize
# output
ANSIBLE_FORCE_COLOR = True

# If tmp generated inventory parsing fails (error state), fail playbook fast
ANSIBLE_INVENTORY_UNPARSED_FAILED = True

# Additional environment variables to be passed to the ansible subprocesses
AWX_TASK_ENV = {}

# Flag to enable/disable updating hosts M2M when saving job events.
CAPTURE_JOB_EVENT_HOSTS = False

# Rebuild Host Smart Inventory memberships.
AWX_REBUILD_SMART_MEMBERSHIP = False

# By default, allow arbitrary Jinja templating in extra_vars defined on a Job Template
ALLOW_JINJA_IN_EXTRA_VARS = 'template'

# Enable dynamically pulling roles from a requirement.yml file
# when updating SCM projects 
# Note: This setting may be overridden by database settings.
AWX_ROLES_ENABLED = True

# Enable bubblewrap support for running jobs (playbook runs only).
# Note: This setting may be overridden by database settings.
AWX_PROOT_ENABLED = True

# Command/path to bubblewrap.
AWX_PROOT_CMD = 'bwrap'

# Additional paths to hide from jobs using bubblewrap.
# Note: This setting may be overridden by database settings.
AWX_PROOT_HIDE_PATHS = []

# Additional paths to show for jobs using bubbelwrap.
# Note: This setting may be overridden by database settings.
AWX_PROOT_SHOW_PATHS = []

# Number of jobs to show as part of the job template history
AWX_JOB_TEMPLATE_HISTORY = 10

# The directory in which Tower will create new temporary directories for job
# execution and isolation (such as credential files and custom
# inventory scripts).
# Note: This setting may be overridden by database settings.
AWX_PROOT_BASE_PATH = "/tmp"

# User definable ansible callback plugins
# Note: This setting may be overridden by database settings.
AWX_ANSIBLE_CALLBACK_PLUGINS = ""

# Automatically remove nodes that have missed their heartbeats after some time
AWX_AUTO_DEPROVISION_INSTANCES = False

# Enable Pendo on the UI, possible values are 'off', 'anonymous', and 'detailed'
# Note: This setting may be overridden by database settings.
PENDO_TRACKING_STATE = "off"

# Default list of modules allowed for ad hoc commands.
# Note: This setting may be overridden by database settings.
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

INV_ENV_VARIABLE_BLACKLIST = ("HOME", "USER", "_", "TERM")

# ----------------
# -- Amazon EC2 --
# ----------------

# AWS does not appear to provide pretty region names via any API, so store the
# list of names here.  The available region IDs will be pulled from boto.
# http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region
EC2_REGION_NAMES = {
    'us-east-1': _('US East (Northern Virginia)'),
    'us-east-2': _('US East (Ohio)'),
    'us-west-2': _('US West (Oregon)'),
    'us-west-1': _('US West (Northern California)'),
    'ca-central-1': _('Canada (Central)'),
    'eu-central-1': _('EU (Frankfurt)'),
    'eu-west-1': _('EU (Ireland)'),
    'eu-west-2': _('EU (London)'),
    'ap-southeast-1': _('Asia Pacific (Singapore)'),
    'ap-southeast-2': _('Asia Pacific (Sydney)'),
    'ap-northeast-1': _('Asia Pacific (Tokyo)'),
    'ap-northeast-2': _('Asia Pacific (Seoul)'),
    'ap-south-1': _('Asia Pacific (Mumbai)'),
    'sa-east-1': _('South America (Sao Paulo)'),
    'us-gov-west-1': _('US West (GovCloud)'),
    'cn-north-1': _('China (Beijing)'),
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
VMWARE_ENABLED_VAR = 'guest.gueststate'
VMWARE_ENABLED_VALUE = 'running'

# Inventory variable name containing the unique instance ID.
VMWARE_INSTANCE_ID_VAR = 'config.instanceuuid'

# Filter for allowed group and host names when importing inventory
# from VMware.
VMWARE_GROUP_FILTER = r'^.+$'
VMWARE_HOST_FILTER = r'^.+$'
VMWARE_EXCLUDE_EMPTY_GROUPS = True

VMWARE_VALIDATE_CERTS = False
# ---------------------------
# -- Google Compute Engine --
# ---------------------------

# It's not possible to get zones in GCE without authenticating, so we
# provide a list here.
# Source: https://developers.google.com/compute/docs/zones
GCE_REGION_CHOICES = [
    ('us-east1-b', _('US East 1 (B)')),
    ('us-east1-c', _('US East 1 (C)')),
    ('us-east1-d', _('US East 1 (D)')),
    ('us-east4-a', _('US East 4 (A)')),
    ('us-east4-b', _('US East 4 (B)')),
    ('us-east4-c', _('US East 4 (C)')),
    ('us-central1-a', _('US Central (A)')),
    ('us-central1-b', _('US Central (B)')),
    ('us-central1-c', _('US Central (C)')),
    ('us-central1-f', _('US Central (F)')),
    ('us-west1-a', _('US West (A)')),
    ('us-west1-b', _('US West (B)')),
    ('us-west1-c', _('US West (C)')),
    ('europe-west1-b', _('Europe West 1 (B)')),
    ('europe-west1-c', _('Europe West 1 (C)')),
    ('europe-west1-d', _('Europe West 1 (D)')),
    ('europe-west2-a', _('Europe West 2 (A)')),
    ('europe-west2-b', _('Europe West 2 (B)')),
    ('europe-west2-c', _('Europe West 2 (C)')),
    ('asia-east1-a', _('Asia East (A)')),
    ('asia-east1-b', _('Asia East (B)')),
    ('asia-east1-c', _('Asia East (C)')),
    ('asia-southeast1-a', _('Asia Southeast (A)')),
    ('asia-southeast1-b', _('Asia Southeast (B)')),
    ('asia-northeast1-a', _('Asia Northeast (A)')),
    ('asia-northeast1-b', _('Asia Northeast (B)')),
    ('asia-northeast1-c', _('Asia Northeast (C)')),
    ('australia-southeast1-a', _('Australia Southeast (A)')),
    ('australia-southeast1-b', _('Australia Southeast (B)')),
    ('australia-southeast1-c', _('Australia Southeast (C)')),
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

# --------------------------------------
# -- Microsoft Azure Resource Manager --
# --------------------------------------
# It's not possible to get zones in Azure without authenticating, so we
# provide a list here.
AZURE_RM_REGION_CHOICES = [
    ('eastus', _('US East')),
    ('eastus2', _('US East 2')),
    ('centralus', _('US Central')),
    ('northcentralus', _('US North Central')),
    ('southcentralus', _('US South Central')),
    ('westcentralus', _('US West Central')),
    ('westus', _('US West')),
    ('westus2', _('US West 2')),
    ('canadaeast', _('Canada East')),
    ('canadacentral', _('Canada Central')),
    ('brazilsouth', _('Brazil South')),
    ('northeurope', _('Europe North')),
    ('westeurope', _('Europe West')),
    ('ukwest', _('UK West')),
    ('uksouth', _('UK South')),
    ('eastasia', _('Asia East')),
    ('southestasia', _('Asia Southeast')),
    ('australiaeast', _('Australia East')),
    ('australiasoutheast', _('Australia Southeast')),
    ('westindia', _('India West')),
    ('southindia', _('India South')),
    ('japaneast', _('Japan East')),
    ('japanwest', _('Japan West')),
    ('koreacentral', _('Korea Central')),
    ('koreasouth', _('Korea South')),
]
AZURE_RM_REGIONS_BLACKLIST = []

AZURE_RM_GROUP_FILTER = r'^.+$'
AZURE_RM_HOST_FILTER = r'^.+$'
AZURE_RM_ENABLED_VAR = 'powerstate'
AZURE_RM_ENABLED_VALUE = 'running'
AZURE_RM_INSTANCE_ID_VAR = 'id'
AZURE_RM_EXCLUDE_EMPTY_GROUPS = True

# ---------------------
# ----- OpenStack -----
# ---------------------
OPENSTACK_ENABLED_VAR = 'status'
OPENSTACK_ENABLED_VALUE = 'ACTIVE'
OPENSTACK_GROUP_FILTER = r'^.+$'
OPENSTACK_HOST_FILTER = r'^.+$'
OPENSTACK_EXCLUDE_EMPTY_GROUPS = True
OPENSTACK_INSTANCE_ID_VAR = 'openstack.id'

# ---------------------
# ----- oVirt4 -----
# ---------------------
RHV_ENABLED_VAR = 'status'
RHV_ENABLED_VALUE = 'up'
RHV_GROUP_FILTER = r'^.+$'
RHV_HOST_FILTER = r'^.+$'
RHV_EXCLUDE_EMPTY_GROUPS = True
RHV_INSTANCE_ID_VAR = 'id'

# ---------------------
# ----- Tower     -----
# ---------------------
TOWER_ENABLED_VAR = 'remote_tower_enabled'
TOWER_ENABLED_VALUE = 'true'
TOWER_GROUP_FILTER = r'^.+$'
TOWER_HOST_FILTER = r'^.+$'
TOWER_EXCLUDE_EMPTY_GROUPS = True
TOWER_INSTANCE_ID_VAR = 'remote_tower_id'

# ---------------------
# ----- Foreman -----
# ---------------------
SATELLITE6_ENABLED_VAR = 'foreman.enabled'
SATELLITE6_ENABLED_VALUE = 'True'
SATELLITE6_GROUP_FILTER = r'^.+$'
SATELLITE6_HOST_FILTER = r'^.+$'
SATELLITE6_EXCLUDE_EMPTY_GROUPS = True
SATELLITE6_INSTANCE_ID_VAR = 'foreman.id'
# SATELLITE6_GROUP_PREFIX and SATELLITE6_GROUP_PATTERNS defined in source vars

# ---------------------
# ----- CloudForms -----
# ---------------------
CLOUDFORMS_ENABLED_VAR = 'cloudforms.power_state'
CLOUDFORMS_ENABLED_VALUE = 'on'
CLOUDFORMS_GROUP_FILTER = r'^.+$'
CLOUDFORMS_HOST_FILTER = r'^.+$'
CLOUDFORMS_EXCLUDE_EMPTY_GROUPS = True
CLOUDFORMS_INSTANCE_ID_VAR = 'cloudforms.id'

# ---------------------
# ----- Custom -----
# ---------------------
#CUSTOM_ENABLED_VAR =
#CUSTOM_ENABLED_VALUE =
CUSTOM_GROUP_FILTER = r'^.+$'
CUSTOM_HOST_FILTER = r'^.+$'
CUSTOM_EXCLUDE_EMPTY_GROUPS = True
#CUSTOM_INSTANCE_ID_VAR =

# ---------------------
# ----- SCM -----
# ---------------------
#SCM_ENABLED_VAR =
#SCM_ENABLED_VALUE =
SCM_GROUP_FILTER = r'^.+$'
SCM_HOST_FILTER = r'^.+$'
SCM_EXCLUDE_EMPTY_GROUPS = True
#SCM_INSTANCE_ID_VAR =

# ---------------------
# -- Activity Stream --
# ---------------------
# Defaults for enabling/disabling activity stream.
# Note: These settings may be overridden by database settings.
ACTIVITY_STREAM_ENABLED = True
ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC = False

# Internal API URL for use by inventory scripts and callback plugin.
INTERNAL_API_URL = 'http://127.0.0.1:%s' % DEVSERVER_DEFAULT_PORT

PERSISTENT_CALLBACK_MESSAGES = True
USE_CALLBACK_QUEUE = True
CALLBACK_QUEUE = "callback_tasks"
FACT_QUEUE = "facts"

SCHEDULER_QUEUE = "scheduler"

TASK_COMMAND_PORT = 6559

SOCKETIO_NOTIFICATION_PORT = 6557
SOCKETIO_LISTEN_PORT = 8080

FACT_CACHE_PORT = 6564

# Note: This setting may be overridden by database settings.
ORG_ADMINS_CAN_SEE_ALL_USERS = True
MANAGE_ORGANIZATION_AUTH = True

# Note: This setting may be overridden by database settings.
TOWER_ADMIN_ALERTS = True

# Note: This setting may be overridden by database settings.
TOWER_URL_BASE = "https://towerhost"

INSIGHTS_URL_BASE = "https://example.org"
INSIGHTS_AGENT_MIME = 'application/example'

TOWER_SETTINGS_MANIFEST = {}

# Settings related to external logger configuration
LOG_AGGREGATOR_ENABLED = False
LOG_AGGREGATOR_TCP_TIMEOUT = 5
LOG_AGGREGATOR_VERIFY_CERT = True
LOG_AGGREGATOR_LEVEL = 'INFO'

# The number of retry attempts for websocket session establishment
# If you're encountering issues establishing websockets in clustered Tower,
# raising this value can help
CHANNEL_LAYER_RECEIVE_MAX_RETRY = 10

# Logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_true_or_test': {
            '()': 'awx.main.utils.RequireDebugTrueOrTest',
        },
        'external_log_enabled': {
            '()': 'awx.main.utils.filters.ExternalLoggerEnabled'
        },
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)-8s %(name)s %(message)s',
        },
        'json': {
            '()': 'awx.main.utils.formatters.LogstashFormatter'
        },
        'timed_import': {
            '()': 'awx.main.utils.formatters.TimeFormatter',
            'format': '%(relativeSeconds)9.3f %(levelname)-8s %(message)s'
        },
        'dispatcher': {
            'format': '%(asctime)s %(levelname)-8s %(name)s PID:%(process)d %(message)s',
        },
    },
    'handlers': {
        'console': {
            '()': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': ['require_debug_true_or_test'],
            'formatter': 'simple',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
        'file': {
            'class': 'logging.NullHandler',
            'formatter': 'simple',
        },
        'syslog': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'logging.NullHandler',
            'formatter': 'simple',
        },
        'external_logger': {
            'class': 'awx.main.utils.handlers.AWXProxyHandler',
            'formatter': 'json',
            'filters': ['external_log_enabled'],
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
            'filename': os.path.join(LOG_ROOT, 'tower.log'),
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
        'dispatcher': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'dispatcher.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'dispatcher',
        },
        'celery.beat': {
            'class':'logging.StreamHandler',
            'level': 'ERROR'
        },  # don't log every celerybeat wakeup
        'inventory_import': {
            'level': 'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'timed_import',
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
        'management_playbooks': {
            'level': 'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'management_playbooks.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'fact_receiver': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'fact_receiver.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'system_tracking_migrations': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'tower_system_tracking_migrations.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'rbac_migrations': {
            'level': 'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': os.path.join(LOG_ROOT, 'tower_rbac_migrations.log'),
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
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'WARNING',
        },
        'rest_framework.request': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'WARNING',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
        },
        'awx': {
            'handlers': ['console', 'file', 'tower_warnings', 'external_logger'],
            'level': 'DEBUG',
        },
        'awx.conf': {
            'handlers': ['null'],
            'level': 'WARNING',
        },
        'awx.conf.settings': {
            'handlers': ['null'],
            'level': 'WARNING',
        },
        'awx.main': {
            'handlers': ['null']
        },
        'awx.main.commands.run_callback_receiver': {
            'handlers': ['callback_receiver'],
            'level': 'INFO'  # in debug mode, includes full callback data
        },
        'awx.main.dispatch': {
            'handlers': ['dispatcher'],
        },
        'awx.isolated.manager.playbooks': {
            'handlers': ['management_playbooks'],
            'propagate': False
        },
        'awx.main.commands.inventory_import': {
            'handlers': ['inventory_import'],
            'propagate': False
        },
        'awx.main.tasks': {
            'handlers': ['task_system', 'external_logger'],
            'propagate': False
        },
        'awx.main.scheduler': {
            'handlers': ['task_system', 'external_logger'],
            'propagate': False
        },
        'awx.main.access': {
            'level': 'INFO',  # very verbose debug-level logs
        },
        'awx.main.signals': {
            'level': 'INFO',  # very verbose debug-level logs
        },
        'awx.api.permissions': {
            'level': 'INFO',  # very verbose debug-level logs
        },
        'awx.analytics': {
            'handlers': ['external_logger'],
            'level': 'INFO',
            'propagate': False
        },
        'django_auth_ldap': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'DEBUG',
        },
        'social': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'DEBUG',
        },
        'system_tracking_migrations': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'DEBUG',
        },
        'rbac_migrations': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'DEBUG',
        },
    }
}
# Apply coloring to messages logged to the console
COLOR_LOGS = False

# https://github.com/django-polymorphic/django-polymorphic/issues/195
# FIXME: Disabling models.E006 warning until we can renamed Project and InventorySource
SILENCED_SYSTEM_CHECKS = ['models.E006']

# Use middleware to get request statistics
AWX_REQUEST_PROFILE = False
