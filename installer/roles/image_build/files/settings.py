# AWX settings file

import os


def get_secret():
    if os.path.exists("/etc/tower/SECRET_KEY"):
        return open('/etc/tower/SECRET_KEY', 'rb').read().strip()
    return os.getenv("SECRET_KEY", "privateawx")


ADMINS = ()

STATIC_ROOT = '/var/lib/awx/public/static'

PROJECTS_ROOT = '/var/lib/awx/projects'

JOBOUTPUT_ROOT = '/var/lib/awx/job_status'

SECRET_KEY = get_secret()

ALLOWED_HOSTS = ['*']

INTERNAL_API_URL = 'http://awxweb:8052'

# Container environments don't like chroots
AWX_PROOT_ENABLED = False


CLUSTER_HOST_ID = "awx"
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

###############################################################################
# EMAIL SETTINGS
###############################################################################

SERVER_EMAIL = 'root@localhost'
DEFAULT_FROM_EMAIL = 'webmaster@localhost'
EMAIL_SUBJECT_PREFIX = '[AWX] '

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

LOGGING['handlers']['console'] = {
    '()': 'logging.StreamHandler',
    'level': 'DEBUG',
    'formatter': 'simple',
}

LOGGING['loggers']['django.request']['handlers'] = ['console']
LOGGING['loggers']['rest_framework.request']['handlers'] = ['console']
LOGGING['loggers']['awx']['handlers'] = ['console', 'external_logger']
LOGGING['loggers']['awx.main.commands.run_callback_receiver']['handlers'] = ['console']
LOGGING['loggers']['awx.main.tasks']['handlers'] = ['console', 'external_logger']
LOGGING['loggers']['awx.main.scheduler']['handlers'] = ['console', 'external_logger']
LOGGING['loggers']['django_auth_ldap']['handlers'] = ['console']
LOGGING['loggers']['social']['handlers'] = ['console']
LOGGING['loggers']['system_tracking_migrations']['handlers'] = ['console']
LOGGING['loggers']['rbac_migrations']['handlers'] = ['console']
LOGGING['loggers']['awx.isolated.manager.playbooks']['handlers'] = ['console']
LOGGING['handlers']['callback_receiver'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['fact_receiver'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['task_system'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['tower_warnings'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['rbac_migrations'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['system_tracking_migrations'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['management_playbooks'] = {'class': 'logging.NullHandler'}

DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DATABASE_NAME", None),
        'USER': os.getenv("DATABASE_USER", None),
        'PASSWORD': os.getenv("DATABASE_PASSWORD", None),
        'HOST': os.getenv("DATABASE_HOST", None),
        'PORT': os.getenv("DATABASE_PORT", None),
    }
}

if os.getenv("DATABASE_SSLMODE", False):
    DATABASES['default']['OPTIONS'] = {'sslmode': os.getenv("DATABASE_SSLMODE")}

BROKER_URL = 'amqp://{}:{}@{}:{}/{}'.format(
    os.getenv("RABBITMQ_USER", None),
    os.getenv("RABBITMQ_PASSWORD", None),
    os.getenv("RABBITMQ_HOST", None),
    os.getenv("RABBITMQ_PORT", "5672"),
    os.getenv("RABBITMQ_VHOST", "tower"))

CHANNEL_LAYERS = {
    'default': {'BACKEND': 'asgi_amqp.AMQPChannelLayer',
                'ROUTING': 'awx.main.routing.channel_routing',
                'CONFIG': {'url': BROKER_URL}}
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '{}:{}'.format(os.getenv("MEMCACHED_HOST", None),
                                   os.getenv("MEMCACHED_PORT", "11211"))
    },
    'ephemeral': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

USE_X_FORWARDED_PORT = True
