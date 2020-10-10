# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import os
import re  # noqa
import sys
from datetime import timedelta

# global settings
from django.conf import global_settings

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

AWX_CONTAINER_GROUP_K8S_API_TIMEOUT = 10
AWX_CONTAINER_GROUP_POD_LAUNCH_RETRIES = 100
AWX_CONTAINER_GROUP_POD_LAUNCH_RETRY_DELAY = 5
AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE = 'default'
AWX_CONTAINER_GROUP_DEFAULT_IMAGE = 'ansible/ansible-runner'

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
    os.path.join(BASE_DIR, 'ui_next', 'build', 'static'),
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

# Absolute filesystem path to the directory to host collections for
# running inventory imports, isolated playbooks
AWX_ANSIBLE_COLLECTIONS_PATHS = os.path.join(BASE_DIR, 'vendor', 'awx_ansible_collections')

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
# allow the proxy IP addresses from which Tower should trust custom
# REMOTE_HOST_HEADERS header values
# REMOTE_HOST_HEADERS = ['HTTP_X_FORWARDED_FOR', ''REMOTE_ADDR', 'REMOTE_HOST']
# PROXY_IP_ALLOWED_LIST = ['10.0.1.100', '10.0.1.101']
# If this setting is an empty list (the default), the headers specified by
# REMOTE_HOST_HEADERS will be trusted unconditionally')
PROXY_IP_ALLOWED_LIST = []

CUSTOM_VENV_PATHS = []

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

# The number of seconds (must be an integer) to buffer callback receiver bulk
# writes in memory before flushing via JobEvent.objects.bulk_create()
JOB_EVENT_BUFFER_SECONDS = 1

# The interval at which callback receiver statistics should be
# recorded
JOB_EVENT_STATISTICS_INTERVAL = 5

# The maximum size of the job event worker queue before requests are blocked
JOB_EVENT_MAX_QUEUE_SIZE = 10000

# The number of job events to migrate per-transaction when moving from int -> bigint
JOB_EVENT_MIGRATION_CHUNK_SIZE = 1000000

# The maximum allowed jobs to start on a given task manager cycle
START_TASK_LIMIT = 100

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
            os.path.join(BASE_DIR, 'ui_next', 'build'),
        ],
    },
]

ROOT_URLCONF = 'awx.urls'

WSGI_APPLICATION = 'awx.wsgi.application'

INSTALLED_APPS = [
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
]

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
        'awx.api.renderers.DefaultJSONRenderer',
        'awx.api.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_METADATA_CLASS': 'awx.api.metadata.Metadata',
    'EXCEPTION_HANDLER': 'awx.api.views.api_exception_handler',
    'VIEW_DESCRIPTION_FUNCTION': 'awx.api.generics.get_view_description',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'DEFAULT_VERSION': 'v2',
    # For swagger schema generation
    # see https://github.com/encode/django-rest-framework/pull/6532
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema',
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
                   'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,
                   'REFRESH_TOKEN_EXPIRE_SECONDS': 2628000}
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

# If set, specifies a URL that unauthenticated users will be redirected to
# when trying to access a UI page that requries authentication.
LOGIN_REDIRECT_OVERRIDE = ''

# Default to skipping isolated host key checking (the initial connection will
# hang on an interactive "The authenticity of host example.org can't be
# established" message)
AWX_ISOLATED_HOST_KEY_CHECKING = False

# The number of seconds to sleep between status checks for jobs running on isolated nodes
AWX_ISOLATED_CHECK_INTERVAL = 30

# The timeout (in seconds) for launching jobs on isolated nodes
AWX_ISOLATED_LAUNCH_TIMEOUT = 600

# Ansible connection timeout (in seconds) for communicating with isolated instances
AWX_ISOLATED_CONNECTION_TIMEOUT = 10

# The time (in seconds) between the periodic isolated heartbeat status check
AWX_ISOLATED_PERIODIC_CHECK = 600

DEVSERVER_DEFAULT_ADDR = '0.0.0.0'
DEVSERVER_DEFAULT_PORT = '8013'

# Set default ports for live server tests.
os.environ.setdefault('DJANGO_LIVE_TEST_SERVER_ADDRESS', 'localhost:9013-9199')

BROKER_URL = 'unix:///var/run/redis/redis.sock'
CELERYBEAT_SCHEDULE = {
    'tower_scheduler': {
        'task': 'awx.main.tasks.awx_periodic_scheduler',
        'schedule': timedelta(seconds=30),
        'options': {'expires': 20,}
    },
    'cluster_heartbeat': {
        'task': 'awx.main.tasks.cluster_node_heartbeat',
        'schedule': timedelta(seconds=60),
        'options': {'expires': 50,}
    },
    'gather_analytics': {
        'task': 'awx.main.tasks.gather_analytics',
        'schedule': timedelta(minutes=5)
    },
    'task_manager': {
        'task': 'awx.main.scheduler.tasks.run_task_manager',
        'schedule': timedelta(seconds=20),
        'options': {'expires': 20}
    },
    'k8s_reaper': {
        'task': 'awx.main.tasks.awx_k8s_reaper',
        'schedule': timedelta(seconds=60),
        'options': {'expires': 50,}
    },
    # 'isolated_heartbeat': set up at the end of production.py and development.py
}

# Django Caching Configuration
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'unix:/var/run/redis/redis.sock?db=1'
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
SAML_AUTO_CREATE_OBJECTS = True

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

# Rebuild Host Smart Inventory memberships.
AWX_REBUILD_SMART_MEMBERSHIP = False

# By default, allow arbitrary Jinja templating in extra_vars defined on a Job Template
ALLOW_JINJA_IN_EXTRA_VARS = 'template'

# Run project updates with extra verbosity
PROJECT_UPDATE_VVV = False

# Enable dynamically pulling roles from a requirement.yml file
# when updating SCM projects
# Note: This setting may be overridden by database settings.
AWX_ROLES_ENABLED = True

# Enable dynamically pulling collections from a requirement.yml file
# when updating SCM projects
# Note: This setting may be overridden by database settings.
AWX_COLLECTIONS_ENABLED = True

# Follow symlinks when scanning for playbooks
AWX_SHOW_PLAYBOOK_LINKS = False

# Applies to any galaxy server
GALAXY_IGNORE_CERTS = False

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

# The directory in which Tower will create new temporary directories for job
# execution and isolation (such as credential files and custom
# inventory scripts).
# Note: This setting may be overridden by database settings.
AWX_PROOT_BASE_PATH = "/tmp"

# Disable resource profiling by default
AWX_RESOURCE_PROFILING_ENABLED = False

# Interval (in seconds) between polls for cpu usage
AWX_RESOURCE_PROFILING_CPU_POLL_INTERVAL = '0.25'

# Interval (in seconds) between polls for memory usage
AWX_RESOURCE_PROFILING_MEMORY_POLL_INTERVAL = '0.25'

# Interval (in seconds) between polls for PID count
AWX_RESOURCE_PROFILING_PID_POLL_INTERVAL = '0.25'

# User definable ansible callback plugins
# Note: This setting may be overridden by database settings.
AWX_ANSIBLE_CALLBACK_PLUGINS = ""

# Automatically remove nodes that have missed their heartbeats after some time
AWX_AUTO_DEPROVISION_INSTANCES = False

# Enable Pendo on the UI, possible values are 'off', 'anonymous', and 'detailed'
# Note: This setting may be overridden by database settings.
PENDO_TRACKING_STATE = "off"

# Enables Insights data collection for Ansible Tower.
# Note: This setting may be overridden by database settings.
INSIGHTS_TRACKING_STATE = False

# Last gather date for Analytics
AUTOMATION_ANALYTICS_LAST_GATHER = None

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

INV_ENV_VARIABLE_BLOCKED = ("HOME", "USER", "_", "TERM")

# ----------------
# -- Amazon EC2 --
# ----------------
EC2_ENABLED_VAR = 'ec2_state'
EC2_ENABLED_VALUE = 'running'
EC2_INSTANCE_ID_VAR = 'ec2_id'
EC2_EXCLUDE_EMPTY_GROUPS = True

# ------------
# -- VMware --
# ------------
VMWARE_ENABLED_VAR = 'guest.gueststate'
VMWARE_ENABLED_VALUE = 'running'
VMWARE_INSTANCE_ID_VAR = 'config.instanceUuid, config.instanceuuid'
VMWARE_EXCLUDE_EMPTY_GROUPS = True

VMWARE_VALIDATE_CERTS = False

# ---------------------------
# -- Google Compute Engine --
# ---------------------------
GCE_ENABLED_VAR = 'status'
GCE_ENABLED_VALUE = 'running'
GCE_EXCLUDE_EMPTY_GROUPS = True
GCE_INSTANCE_ID_VAR = 'gce_id'

# --------------------------------------
# -- Microsoft Azure Resource Manager --
# --------------------------------------
AZURE_RM_ENABLED_VAR = 'powerstate'
AZURE_RM_ENABLED_VALUE = 'running'
AZURE_RM_INSTANCE_ID_VAR = 'id'
AZURE_RM_EXCLUDE_EMPTY_GROUPS = True

# ---------------------
# ----- OpenStack -----
# ---------------------
OPENSTACK_ENABLED_VAR = 'status'
OPENSTACK_ENABLED_VALUE = 'ACTIVE'
OPENSTACK_EXCLUDE_EMPTY_GROUPS = True
OPENSTACK_INSTANCE_ID_VAR = 'openstack.id'

# ---------------------
# ----- oVirt4 -----
# ---------------------
RHV_ENABLED_VAR = 'status'
RHV_ENABLED_VALUE = 'up'
RHV_EXCLUDE_EMPTY_GROUPS = True
RHV_INSTANCE_ID_VAR = 'id'

# ---------------------
# ----- Tower     -----
# ---------------------
TOWER_ENABLED_VAR = 'remote_tower_enabled'
TOWER_ENABLED_VALUE = 'true'
TOWER_EXCLUDE_EMPTY_GROUPS = True
TOWER_INSTANCE_ID_VAR = 'remote_tower_id'

# ---------------------
# ----- Foreman -----
# ---------------------
SATELLITE6_ENABLED_VAR = 'foreman.enabled'
SATELLITE6_ENABLED_VALUE = 'True'
SATELLITE6_EXCLUDE_EMPTY_GROUPS = True
SATELLITE6_INSTANCE_ID_VAR = 'foreman.id'
# SATELLITE6_GROUP_PREFIX and SATELLITE6_GROUP_PATTERNS defined in source vars

# ---------------------
# ----- Custom -----
# ---------------------
#CUSTOM_ENABLED_VAR =
#CUSTOM_ENABLED_VALUE =
CUSTOM_EXCLUDE_EMPTY_GROUPS = False
#CUSTOM_INSTANCE_ID_VAR =

# ---------------------
# ----- SCM -----
# ---------------------
#SCM_ENABLED_VAR =
#SCM_ENABLED_VALUE =
SCM_EXCLUDE_EMPTY_GROUPS = False
#SCM_INSTANCE_ID_VAR =

# ---------------------
# -- Activity Stream --
# ---------------------
# Defaults for enabling/disabling activity stream.
# Note: These settings may be overridden by database settings.
ACTIVITY_STREAM_ENABLED = True
ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC = False

CALLBACK_QUEUE = "callback_tasks"

# Note: This setting may be overridden by database settings.
ORG_ADMINS_CAN_SEE_ALL_USERS = True
MANAGE_ORGANIZATION_AUTH = True

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
LOG_AGGREGATOR_MAX_DISK_USAGE_GB = 1
LOG_AGGREGATOR_MAX_DISK_USAGE_PATH = '/var/lib/awx'
LOG_AGGREGATOR_RSYSLOGD_DEBUG = False

# The number of retry attempts for websocket session establishment
# If you're encountering issues establishing websockets in clustered Tower,
# raising this value can help
CHANNEL_LAYER_RECEIVE_MAX_RETRY = 10

ASGI_APPLICATION = "awx.main.routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [BROKER_URL],
            "capacity": 10000,
            "group_expiry": 157784760, # 5 years
        },
    },
}

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
        'dynamic_level_filter': {
            '()': 'awx.main.utils.filters.DynamicLevelFilter'
        }
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
            'class': 'awx.main.utils.handlers.RSysLogHandler',
            'formatter': 'json',
            'address': '/var/run/awx-rsyslog/rsyslog.sock',
            'filters': ['external_log_enabled', 'dynamic_level_filter'],
        },
        'tower_warnings': {
            # don't define a level here, it's set by settings.LOG_AGGREGATOR_LEVEL
            'class': 'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false', 'dynamic_level_filter'],
            'filename': os.path.join(LOG_ROOT, 'tower.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'callback_receiver': {
            # don't define a level here, it's set by settings.LOG_AGGREGATOR_LEVEL
            'class': 'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false', 'dynamic_level_filter'],
            'filename': os.path.join(LOG_ROOT, 'callback_receiver.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
        },
        'dispatcher': {
            # don't define a level here, it's set by settings.LOG_AGGREGATOR_LEVEL
            'class': 'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false', 'dynamic_level_filter'],
            'filename': os.path.join(LOG_ROOT, 'dispatcher.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'dispatcher',
        },
        'wsbroadcast': {
            # don't define a level here, it's set by settings.LOG_AGGREGATOR_LEVEL
            'class': 'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false', 'dynamic_level_filter'],
            'filename': os.path.join(LOG_ROOT, 'wsbroadcast.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'simple',
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
            # don't define a level here, it's set by settings.LOG_AGGREGATOR_LEVEL
            'class': 'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false', 'dynamic_level_filter'],
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
        'daphne': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'INFO',
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
            'handlers': ['callback_receiver'],  # level handled by dynamic_level_filter
        },
        'awx.main.dispatch': {
            'handlers': ['dispatcher'],
        },
        'awx.main.consumers': {
            'handlers': ['console', 'file', 'tower_warnings'],
            'level': 'INFO',
        },
        'awx.main.wsbroadcast': {
            'handlers': ['wsbroadcast'],
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
        'awx.main.analytics': {
            'handlers': ['task_system', 'external_logger'],
            'level': 'INFO',
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

#
# Optionally, AWX can generate DOT graphs
# (http://www.graphviz.org/doc/info/lang.html) for per-request profiling
# via gprof2dot (https://github.com/jrfonseca/gprof2dot)
#
# If you set this to True, you must `/var/lib/awx/venv/awx/bin/pip install gprof2dot`
# .dot files will be saved in `/var/log/tower/profile/` and can be converted e.g.,
#
# ~ yum install graphviz
# ~ dot -o profile.png -Tpng /var/log/tower/profile/some-profile-data.dot
#
AWX_REQUEST_PROFILE_WITH_DOT = False

# Allow profiling callback workers via SIGUSR1
AWX_CALLBACK_PROFILE = False

# Delete temporary directories created to store playbook run-time
AWX_CLEANUP_PATHS = True

MIDDLEWARE = [
    'awx.main.middleware.TimingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'awx.main.middleware.MigrationRanCheckMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'awx.sso.middleware.SocialAuthMiddleware',
    'crum.CurrentRequestUserMiddleware',
    'awx.main.middleware.URLModificationMiddleware',
    'awx.main.middleware.SessionTimeoutMiddleware',
]

# Secret header value to exchange for websockets responsible for distributing websocket messages.
# This needs to be kept secret and randomly generated
BROADCAST_WEBSOCKET_SECRET = ''

# Port for broadcast websockets to connect to
# Note: that the clients will follow redirect responses
BROADCAST_WEBSOCKET_PORT = 443

# Whether or not broadcast websockets should check nginx certs when interconnecting
BROADCAST_WEBSOCKET_VERIFY_CERT = False

# Connect to other AWX nodes using http or https
BROADCAST_WEBSOCKET_PROTOCOL = 'https'

# All websockets that connect to the broadcast websocket endpoint will be put into this group
BROADCAST_WEBSOCKET_GROUP_NAME = 'broadcast-group_send'

# Time wait before retrying connecting to a websocket broadcast tower node
BROADCAST_WEBSOCKET_RECONNECT_RETRY_RATE_SECONDS = 5

# How often websocket process will look for changes in the Instance table
BROADCAST_WEBSOCKET_NEW_INSTANCE_POLL_RATE_SECONDS = 10

# How often websocket process will generate stats
BROADCAST_WEBSOCKET_STATS_POLL_RATE_SECONDS = 5
