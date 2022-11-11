# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import base64
import os
import re  # noqa
import sys
import tempfile
import socket
from datetime import timedelta


if "pytest" in sys.modules:
    from unittest import mock

    with mock.patch('__main__.__builtins__.dir', return_value=[]):
        import ldap
else:
    import ldap


DEBUG = True
SQL_DEBUG = DEBUG

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# FIXME: it would be nice to cycle back around and allow this to be
# BigAutoField going forward, but we'd have to be explicit about our
# existing models.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'awx.sqlite3'),
        'ATOMIC_REQUESTS': True,
        'TEST': {
            # Test database cannot be :memory: for inventory tests.
            'NAME': os.path.join(BASE_DIR, 'awx_test.sqlite3')
        },
    }
}

# Whether or not the deployment is a K8S-based deployment
# In K8S-based deployments, instances have zero capacity - all playbook
# automation is intended to flow through defined Container Groups that
# interface with some (or some set of) K8S api (which may or may not include
# the K8S cluster where awx itself is running)
IS_K8S = False

AWX_CONTAINER_GROUP_K8S_API_TIMEOUT = 10
AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE = os.getenv('MY_POD_NAMESPACE', 'default')
# Timeout when waiting for pod to enter running state. If the pod is still in pending state , it will be terminated. Valid time units are "s", "m", "h". Example : "5m" , "10s".
AWX_CONTAINER_GROUP_POD_PENDING_TIMEOUT = "2h"

# How much capacity controlling a task costs a hybrid or control node
AWX_CONTROL_NODE_TASK_IMPACT = 1

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

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'ui', 'build', 'static'), os.path.join(BASE_DIR, 'static')]

# Absolute filesystem path to the directory where static file are collected via
# the collectstatic command.
STATIC_ROOT = '/var/lib/awx/public/static'

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
PROJECTS_ROOT = '/var/lib/awx/projects/'

# Absolute filesystem path to the directory for job status stdout (default for
# development and tests, default for production defined in production.py). This
# directory should not be web-accessible
JOBOUTPUT_ROOT = '/var/lib/awx/job_status/'

# Absolute filesystem path to the directory to store logs
LOG_ROOT = '/var/log/tower/'

# The heartbeat file for the scheduler
SCHEDULE_METADATA_LOCATION = os.path.join(BASE_DIR, '.tower_cycle')

# Django gettext files path: locale/<lang-code>/LC_MESSAGES/django.po, django.mo
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

# Graph of resources that can have named-url
NAMED_URL_GRAPH = {}

# Maximum number of the same job that can be waiting to run when launching from scheduler
# Note: This setting may be overridden by database settings.
SCHEDULE_MAX_JOBS = 10

SITE_ID = 1

# Make this unique, and don't share it with anybody.
if os.path.exists('/etc/tower/SECRET_KEY'):
    with open('/etc/tower/SECRET_KEY', 'rb') as f:
        SECRET_KEY = f.read().strip()
else:
    SECRET_KEY = base64.encodebytes(os.urandom(32)).decode().rstrip()

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# HTTP headers and meta keys to search to determine remote host name or IP. Add
# additional items to this list, such as "HTTP_X_FORWARDED_FOR", if behind a
# reverse proxy.
REMOTE_HOST_HEADERS = ['REMOTE_ADDR', 'REMOTE_HOST']

# If we are behind a reverse proxy/load balancer, use this setting to
# allow the proxy IP addresses from which Tower should trust custom
# REMOTE_HOST_HEADERS header values
# REMOTE_HOST_HEADERS = ['HTTP_X_FORWARDED_FOR', ''REMOTE_ADDR', 'REMOTE_HOST']
# PROXY_IP_ALLOWED_LIST = ['10.0.1.100', '10.0.1.101']
# If this setting is an empty list (the default), the headers specified by
# REMOTE_HOST_HEADERS will be trusted unconditionally')
PROXY_IP_ALLOWED_LIST = []

CUSTOM_VENV_PATHS = []

# Warning: this is a placeholder for a database setting
# This should not be set via a file.
DEFAULT_EXECUTION_ENVIRONMENT = None

# This list is used for creating default EEs when running awx-manage create_preload_data.
# Should be ordered from highest to lowest precedence.
# The awx-manage register_default_execution_environments command reads this setting and registers the EE(s)
# If a registry credential is needed to pull the image, that can be provided to the awx-manage command
GLOBAL_JOB_EXECUTION_ENVIRONMENTS = [{'name': 'AWX EE (latest)', 'image': 'quay.io/ansible/awx-ee:latest'}]
# This setting controls which EE will be used for project updates.
# The awx-manage register_default_execution_environments command reads this setting and registers the EE
# This image is distinguished from others by having "managed" set to True and users have limited
# ability to modify it through the API.
# If a registry credential is needed to pull the image, that can be provided to the awx-manage command
CONTROL_PLANE_EXECUTION_ENVIRONMENT = 'quay.io/ansible/awx-ee:latest'

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

# Note: These settings may be overridden by database settings.
EVENT_STDOUT_MAX_BYTES_DISPLAY = 1024
MAX_WEBSOCKET_EVENT_RATE = 30

# The amount of time before a stdout file is expired and removed locally
# Note that this can be recreated if the stdout is downloaded
LOCAL_STDOUT_EXPIRE_TIME = 2592000

# The number of processes spawned by the callback receiver to process job
# events into the database
JOB_EVENT_WORKERS = 4

# The number of seconds to buffer callback receiver bulk
# writes in memory before flushing via JobEvent.objects.bulk_create()
JOB_EVENT_BUFFER_SECONDS = 0.1

# The interval at which callback receiver statistics should be
# recorded
JOB_EVENT_STATISTICS_INTERVAL = 5

# The maximum size of the job event worker queue before requests are blocked
JOB_EVENT_MAX_QUEUE_SIZE = 10000

# The number of job events to migrate per-transaction when moving from int -> bigint
JOB_EVENT_MIGRATION_CHUNK_SIZE = 1000000

# Histogram buckets for the callback_receiver_batch_events_insert_db metric
SUBSYSTEM_METRICS_BATCH_INSERT_BUCKETS = [10, 50, 150, 350, 650, 2000]

# Interval in seconds for sending local metrics to other nodes
SUBSYSTEM_METRICS_INTERVAL_SEND_METRICS = 3

# Interval in seconds for saving local metrics to redis
SUBSYSTEM_METRICS_INTERVAL_SAVE_TO_REDIS = 2

# Record task manager metrics at the following interval in seconds
# If using Prometheus, it is recommended to be => the Prometheus scrape interval
SUBSYSTEM_METRICS_TASK_MANAGER_RECORD_INTERVAL = 15

# The maximum allowed jobs to start on a given task manager cycle
START_TASK_LIMIT = 100

# Time out task managers if they take longer than this many seconds, plus TASK_MANAGER_TIMEOUT_GRACE_PERIOD
# We have the grace period so the task manager can bail out before the timeout.
TASK_MANAGER_TIMEOUT = 300
TASK_MANAGER_TIMEOUT_GRACE_PERIOD = 60

# Number of seconds _in addition to_ the task manager timeout a job can stay
# in waiting without being reaped
JOB_WAITING_GRACE_PERIOD = 60

# Number of seconds after a container group job finished time to wait
# before the awx_k8s_reaper task will tear down the pods
K8S_POD_REAPER_GRACE_PERIOD = 60

# Disallow sending session cookies over insecure connections
SESSION_COOKIE_SECURE = True

# Seconds before sessions expire.
# Note: This setting may be overridden by database settings.
SESSION_COOKIE_AGE = 1800

# Name of the cookie that contains the session information.
# Note: Changing this value may require changes to any clients.
SESSION_COOKIE_NAME = 'awx_sessionid'

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
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [  # NOQA
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'awx.ui.context_processors.csp',
                'awx.ui.context_processors.version',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
            'builtins': ['awx.main.templatetags.swagger'],
        },
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'ui', 'build'), os.path.join(BASE_DIR, 'ui', 'public')],
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
    'django_guid',
    'corsheaders',
    'awx.conf',
    'awx.main',
    'awx.api',
    'awx.ui',
    'awx.sso',
    'solo',
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
    'DEFAULT_PERMISSION_CLASSES': ('awx.api.permissions.ModelAccessPermission',),
    'DEFAULT_FILTER_BACKENDS': (
        'awx.api.filters.TypeFilterBackend',
        'awx.api.filters.FieldLookupBackend',
        'rest_framework.filters.SearchFilter',
        'awx.api.filters.OrderByBackend',
    ),
    'DEFAULT_PARSER_CLASSES': ('awx.api.parsers.JSONParser',),
    'DEFAULT_RENDERER_CLASSES': ('awx.api.renderers.DefaultJSONRenderer', 'awx.api.renderers.BrowsableAPIRenderer'),
    'DEFAULT_METADATA_CLASS': 'awx.api.metadata.Metadata',
    'EXCEPTION_HANDLER': 'awx.api.views.api_exception_handler',
    'VIEW_DESCRIPTION_FUNCTION': 'awx.api.generics.get_view_description',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'DEFAULT_VERSION': 'v2',
    # For swagger schema generation
    # see https://github.com/encode/django-rest-framework/pull/6532
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema',
    # 'URL_FORMAT_OVERRIDE': None,
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
    'social_core.backends.github_enterprise.GithubEnterpriseOAuth2',
    'social_core.backends.github_enterprise.GithubEnterpriseOrganizationOAuth2',
    'social_core.backends.github_enterprise.GithubEnterpriseTeamOAuth2',
    'social_core.backends.open_id_connect.OpenIdConnectAuth',
    'social_core.backends.azuread.AzureADOAuth2',
    'awx.sso.backends.SAMLAuth',
    'awx.main.backends.AWXModelBackend',
)


# Django OAuth Toolkit settings
OAUTH2_PROVIDER_APPLICATION_MODEL = 'main.OAuth2Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'main.OAuth2AccessToken'
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'

OAUTH2_PROVIDER = {'ACCESS_TOKEN_EXPIRE_SECONDS': 31536000000, 'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600, 'REFRESH_TOKEN_EXPIRE_SECONDS': 2628000}
ALLOW_OAUTH2_FOR_EXTERNAL_USERS = False

# LDAP server (default to None to skip using LDAP authentication).
# Note: This setting may be overridden by database settings.
AUTH_LDAP_SERVER_URI = None

# Disable LDAP referrals by default (to prevent certain LDAP queries from
# hanging with AD).
# Note: This setting may be overridden by database settings.
AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0, ldap.OPT_NETWORK_TIMEOUT: 30}

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

DEVSERVER_DEFAULT_ADDR = '0.0.0.0'
DEVSERVER_DEFAULT_PORT = '8013'

# Set default ports for live server tests.
os.environ.setdefault('DJANGO_LIVE_TEST_SERVER_ADDRESS', 'localhost:9013-9199')

# heartbeat period can factor into some forms of logic, so it is maintained as a setting here
CLUSTER_NODE_HEARTBEAT_PERIOD = 60

# Number of missed heartbeats until a node gets marked as lost
CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2

RECEPTOR_SERVICE_ADVERTISEMENT_PERIOD = 60  # https://github.com/ansible/receptor/blob/aa1d589e154d8a0cb99a220aff8f98faf2273be6/pkg/netceptor/netceptor.go#L34
EXECUTION_NODE_REMEDIATION_CHECKS = 60 * 30  # once every 30 minutes check if an execution node errors have been resolved

# Amount of time dispatcher will try to reconnect to database for jobs and consuming new work
DISPATCHER_DB_DOWNTOWN_TOLLERANCE = 40

BROKER_URL = 'unix:///var/run/redis/redis.sock'
CELERYBEAT_SCHEDULE = {
    'tower_scheduler': {'task': 'awx.main.tasks.system.awx_periodic_scheduler', 'schedule': timedelta(seconds=30), 'options': {'expires': 20}},
    'cluster_heartbeat': {
        'task': 'awx.main.tasks.system.cluster_node_heartbeat',
        'schedule': timedelta(seconds=CLUSTER_NODE_HEARTBEAT_PERIOD),
        'options': {'expires': 50},
    },
    'gather_analytics': {'task': 'awx.main.tasks.system.gather_analytics', 'schedule': timedelta(minutes=5)},
    'task_manager': {'task': 'awx.main.scheduler.tasks.task_manager', 'schedule': timedelta(seconds=20), 'options': {'expires': 20}},
    'dependency_manager': {'task': 'awx.main.scheduler.tasks.dependency_manager', 'schedule': timedelta(seconds=20), 'options': {'expires': 20}},
    'k8s_reaper': {'task': 'awx.main.tasks.system.awx_k8s_reaper', 'schedule': timedelta(seconds=60), 'options': {'expires': 50}},
    'receptor_reaper': {'task': 'awx.main.tasks.system.awx_receptor_workunit_reaper', 'schedule': timedelta(seconds=60)},
    'send_subsystem_metrics': {'task': 'awx.main.analytics.analytics_tasks.send_subsystem_metrics', 'schedule': timedelta(seconds=20)},
    'cleanup_images': {'task': 'awx.main.tasks.system.cleanup_images_and_files', 'schedule': timedelta(hours=3)},
}

# Django Caching Configuration
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
CACHES = {'default': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': 'unix:/var/run/redis/redis.sock?db=1'}}

# Social Auth configuration.
SOCIAL_AUTH_STRATEGY = 'social_django.strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'
SOCIAL_AUTH_USER_MODEL = 'auth.User'

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
SOCIAL_AUTH_PIPELINE = _SOCIAL_AUTH_PIPELINE_BASE + ('awx.sso.pipeline.update_user_orgs', 'awx.sso.pipeline.update_user_teams')
SOCIAL_AUTH_SAML_PIPELINE = _SOCIAL_AUTH_PIPELINE_BASE + (
    'awx.sso.pipeline.update_user_orgs_by_saml_attr',
    'awx.sso.pipeline.update_user_teams_by_saml_attr',
    'awx.sso.pipeline.update_user_orgs',
    'awx.sso.pipeline.update_user_teams',
    'awx.sso.pipeline.update_user_flags',
)
SAML_AUTO_CREATE_OBJECTS = True

SOCIAL_AUTH_LOGIN_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/sso/complete/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/sso/error/'
SOCIAL_AUTH_INACTIVE_USER_URL = '/sso/inactive/'

SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = False
# SOCIAL_AUTH_SLUGIFY_USERNAMES = True
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

SOCIAL_AUTH_GITHUB_ENTERPRISE_KEY = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_SECRET = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_SCOPE = ['user:email', 'read:org']

SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_KEY = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_SECRET = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_NAME = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_ORG_SCOPE = ['user:email', 'read:org']

SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID = ''
SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SCOPE = ['user:email', 'read:org']

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
SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR = {}

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

# Additional environment variables to apply when running ansible-galaxy commands
# to fetch Ansible content - roles and collections
GALAXY_TASK_ENV = {'ANSIBLE_FORCE_COLOR': 'false', 'GIT_SSH_COMMAND': "ssh -o StrictHostKeyChecking=no"}

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

# Additional paths to show for jobs using process isolation.
# Note: This setting may be overridden by database settings.
AWX_ISOLATION_SHOW_PATHS = []

# The directory in which the service will create new temporary directories for job
# execution and isolation (such as credential files and custom
# inventory scripts).
# Note: This setting may be overridden by database settings.
AWX_ISOLATION_BASE_PATH = tempfile.gettempdir()

# User definable ansible callback plugins
# Note: This setting may be overridden by database settings.
AWX_ANSIBLE_CALLBACK_PLUGINS = ""

# Automatically remove nodes that have missed their heartbeats after some time
AWX_AUTO_DEPROVISION_INSTANCES = False

# Enable Pendo on the UI, possible values are 'off', 'anonymous', and 'detailed'
# Note: This setting may be overridden by database settings.
PENDO_TRACKING_STATE = "off"

# Enables Insights data collection.
# Note: This setting may be overridden by database settings.
INSIGHTS_TRACKING_STATE = False

# Last gather date for Analytics
AUTOMATION_ANALYTICS_LAST_GATHER = None
# Last gathered entries for expensive Analytics
AUTOMATION_ANALYTICS_LAST_ENTRIES = ''

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

INV_ENV_VARIABLE_BLOCKED = ("HOME", "USER", "_", "TERM", "PATH")

# ----------------
# -- Amazon EC2 --
# ----------------
EC2_ENABLED_VAR = 'ec2_state'
EC2_ENABLED_VALUE = 'running'
EC2_INSTANCE_ID_VAR = 'instance_id'
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
# ----- Controller     -----
# ---------------------
CONTROLLER_ENABLED_VAR = 'remote_tower_enabled'
CONTROLLER_ENABLED_VALUE = 'true'
CONTROLLER_EXCLUDE_EMPTY_GROUPS = True
CONTROLLER_INSTANCE_ID_VAR = 'remote_tower_id'

# ---------------------
# ----- Foreman -----
# ---------------------
SATELLITE6_ENABLED_VAR = 'foreman_enabled'
SATELLITE6_ENABLED_VALUE = 'True'
SATELLITE6_EXCLUDE_EMPTY_GROUPS = True
SATELLITE6_INSTANCE_ID_VAR = 'foreman_id'
# SATELLITE6_GROUP_PREFIX and SATELLITE6_GROUP_PATTERNS defined in source vars

# ----------------
# -- Red Hat Insights --
# ----------------
# INSIGHTS_ENABLED_VAR =
# INSIGHTS_ENABLED_VALUE =
INSIGHTS_INSTANCE_ID_VAR = 'insights_id'
INSIGHTS_EXCLUDE_EMPTY_GROUPS = False

# ---------------------
# ----- Custom -----
# ---------------------
# CUSTOM_ENABLED_VAR =
# CUSTOM_ENABLED_VALUE =
CUSTOM_EXCLUDE_EMPTY_GROUPS = False
# CUSTOM_INSTANCE_ID_VAR =

# ---------------------
# ----- SCM -----
# ---------------------
# SCM_ENABLED_VAR =
# SCM_ENABLED_VALUE =
SCM_EXCLUDE_EMPTY_GROUPS = False
# SCM_INSTANCE_ID_VAR =

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
DISABLE_LOCAL_AUTH = False

# Note: This setting may be overridden by database settings.
TOWER_URL_BASE = "https://towerhost"

INSIGHTS_URL_BASE = "https://example.org"
INSIGHTS_AGENT_MIME = 'application/example'
# See https://github.com/ansible/awx-facts-playbooks
INSIGHTS_SYSTEM_ID_FILE = '/etc/redhat-access-insights/machine-id'

TOWER_SETTINGS_MANIFEST = {}

# Settings related to external logger configuration
LOG_AGGREGATOR_ENABLED = False
LOG_AGGREGATOR_TCP_TIMEOUT = 5
LOG_AGGREGATOR_VERIFY_CERT = True
LOG_AGGREGATOR_LEVEL = 'INFO'
LOG_AGGREGATOR_MAX_DISK_USAGE_GB = 1
LOG_AGGREGATOR_MAX_DISK_USAGE_PATH = '/var/lib/awx'
LOG_AGGREGATOR_RSYSLOGD_DEBUG = False
LOG_AGGREGATOR_RSYSLOGD_ERROR_LOG_FILE = '/var/log/tower/rsyslog.err'
API_400_ERROR_LOG_FORMAT = 'status {status_code} received by user {user_name} attempting to access {url_path} from {remote_addr}'

# The number of retry attempts for websocket session establishment
# If you're encountering issues establishing websockets in a cluster,
# raising this value can help
CHANNEL_LAYER_RECEIVE_MAX_RETRY = 10

ASGI_APPLICATION = "awx.main.routing.application"

CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [BROKER_URL], "capacity": 10000, "group_expiry": 157784760}}  # 5 years
}

# Logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
        'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'},
        'require_debug_true_or_test': {'()': 'awx.main.utils.RequireDebugTrueOrTest'},
        'external_log_enabled': {'()': 'awx.main.utils.filters.ExternalLoggerEnabled'},
        'dynamic_level_filter': {'()': 'awx.main.utils.filters.DynamicLevelFilter'},
        'guid': {'()': 'awx.main.utils.filters.DefaultCorrelationId'},
    },
    'formatters': {
        'simple': {'format': '%(asctime)s %(levelname)-8s [%(guid)s] %(name)s %(message)s'},
        'json': {'()': 'awx.main.utils.formatters.LogstashFormatter'},
        'timed_import': {'()': 'awx.main.utils.formatters.TimeFormatter', 'format': '%(relativeSeconds)9.3f %(levelname)-8s %(message)s'},
        'dispatcher': {'format': '%(asctime)s %(levelname)-8s [%(guid)s] %(name)s PID:%(process)d %(message)s'},
        'job_lifecycle': {'()': 'awx.main.utils.formatters.JobLifeCycleFormatter'},
    },
    # Extended below based on install scenario. You probably don't want to add something directly here.
    # See 'handler_config' below.
    'handlers': {
        'console': {
            '()': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': ['dynamic_level_filter', 'guid'],
            'formatter': 'simple',
        },
        'null': {'class': 'logging.NullHandler'},
        'file': {'class': 'logging.NullHandler', 'formatter': 'simple'},
        'syslog': {'level': 'WARNING', 'filters': ['require_debug_false'], 'class': 'logging.NullHandler', 'formatter': 'simple'},
        'inventory_import': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'timed_import'},
        'external_logger': {
            'class': 'awx.main.utils.handlers.RSysLogHandler',
            'formatter': 'json',
            'address': '/var/run/awx-rsyslog/rsyslog.sock',
            'filters': ['external_log_enabled', 'dynamic_level_filter', 'guid'],
        },
    },
    'loggers': {
        'django': {'handlers': ['console']},
        'django.request': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'WARNING'},
        'daphne': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'INFO'},
        'rest_framework.request': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'WARNING', 'propagate': False},
        'py.warnings': {'handlers': ['console']},
        'awx': {'handlers': ['console', 'file', 'tower_warnings', 'external_logger'], 'level': 'DEBUG'},
        'awx.conf': {'handlers': ['null'], 'level': 'WARNING'},
        'awx.conf.settings': {'handlers': ['null'], 'level': 'WARNING'},
        'awx.main': {'handlers': ['null']},
        'awx.main.commands.run_callback_receiver': {'handlers': ['callback_receiver']},  # level handled by dynamic_level_filter
        'awx.main.dispatch': {'handlers': ['dispatcher']},
        'awx.main.consumers': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'INFO'},
        'awx.main.wsbroadcast': {'handlers': ['wsbroadcast']},
        'awx.main.commands.inventory_import': {'handlers': ['inventory_import'], 'propagate': False},
        'awx.main.tasks': {'handlers': ['task_system', 'external_logger'], 'propagate': False},
        'awx.main.analytics': {'handlers': ['task_system', 'external_logger'], 'level': 'INFO', 'propagate': False},
        'awx.main.scheduler': {'handlers': ['task_system', 'external_logger'], 'propagate': False},
        'awx.main.access': {'level': 'INFO'},  # very verbose debug-level logs
        'awx.main.signals': {'level': 'INFO'},  # very verbose debug-level logs
        'awx.api.permissions': {'level': 'INFO'},  # very verbose debug-level logs
        'awx.analytics': {'handlers': ['external_logger'], 'level': 'INFO', 'propagate': False},
        'awx.analytics.performance': {'handlers': ['console', 'file', 'tower_warnings', 'external_logger'], 'level': 'DEBUG', 'propagate': False},
        'awx.analytics.job_lifecycle': {'handlers': ['console', 'job_lifecycle'], 'level': 'DEBUG', 'propagate': False},
        'django_auth_ldap': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'DEBUG'},
        'social': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'DEBUG'},
        'system_tracking_migrations': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'DEBUG'},
        'rbac_migrations': {'handlers': ['console', 'file', 'tower_warnings'], 'level': 'DEBUG'},
    },
}

# Log handler configuration. Keys are the name of the handler. Be mindful when renaming things here.
# People might have created custom settings files that augments the behavior of these.
# Specify 'filename' (used if the environment variable AWX_LOGGING_MODE is unset or 'file')
# and an optional 'formatter'. If no formatter is specified, 'simple' is used.
handler_config = {
    'tower_warnings': {'filename': 'tower.log'},
    'callback_receiver': {'filename': 'callback_receiver.log'},
    'dispatcher': {'filename': 'dispatcher.log', 'formatter': 'dispatcher'},
    'wsbroadcast': {'filename': 'wsbroadcast.log'},
    'task_system': {'filename': 'task_system.log'},
    'rbac_migrations': {'filename': 'tower_rbac_migrations.log'},
    'job_lifecycle': {'filename': 'job_lifecycle.log', 'formatter': 'job_lifecycle'},
}

# If running on a VM, we log to files. When running in a container, we log to stdout.
logging_mode = os.getenv('AWX_LOGGING_MODE', 'file')
if logging_mode not in ('file', 'stdout'):
    raise Exception("AWX_LOGGING_MODE must be 'file' or 'stdout'")

for name, config in handler_config.items():
    # Common log handler config. Don't define a level here, it's set by settings.LOG_AGGREGATOR_LEVEL
    LOGGING['handlers'][name] = {'filters': ['dynamic_level_filter', 'guid'], 'formatter': config.get('formatter', 'simple')}

    if logging_mode == 'file':
        LOGGING['handlers'][name]['class'] = 'logging.handlers.WatchedFileHandler'
        LOGGING['handlers'][name]['filename'] = os.path.join(LOG_ROOT, config['filename'])

    if logging_mode == 'stdout':
        LOGGING['handlers'][name]['class'] = 'logging.NullHandler'

# Prevents logging to stdout on traditional VM installs
if logging_mode == 'file':
    LOGGING['handlers']['console']['filters'].insert(0, 'require_debug_true_or_test')

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

# Allow ansible-runner to store env folder (may contain sensitive information)
AWX_RUNNER_OMIT_ENV_FILES = True

# Allow ansible-runner to save ansible output (may cause performance issues)
AWX_RUNNER_SUPPRESS_OUTPUT_FILE = True

# Delete completed work units in receptor
RECEPTOR_RELEASE_WORK = True

MIDDLEWARE = [
    'django_guid.middleware.guid_middleware',
    'awx.main.middleware.SettingsCacheMiddleware',
    'awx.main.middleware.TimingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'awx.main.middleware.MigrationRanCheckMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'awx.main.middleware.DisableLocalAuthMiddleware',
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

DJANGO_GUID = {'GUID_HEADER_NAME': 'X-API-Request-Id'}

# Name of the default task queue
DEFAULT_EXECUTION_QUEUE_NAME = 'default'
# pod spec used when the default execution queue is a container group, e.g. when deploying on k8s/ocp with the operator
DEFAULT_EXECUTION_QUEUE_POD_SPEC_OVERRIDE = ''
# Name of the default controlplane queue
DEFAULT_CONTROL_PLANE_QUEUE_NAME = 'controlplane'

# Extend container runtime attributes.
# For example, to disable SELinux in containers for podman
# DEFAULT_CONTAINER_RUN_OPTIONS = ['--security-opt', 'label=disable']
DEFAULT_CONTAINER_RUN_OPTIONS = ['--network', 'slirp4netns:enable_ipv6=true']

# Mount exposed paths as hostPath resource in k8s/ocp
AWX_MOUNT_ISOLATED_PATHS_ON_K8S = False

# This is overridden downstream via /etc/tower/conf.d/cluster_host_id.py
CLUSTER_HOST_ID = socket.gethostname()
