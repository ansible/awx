# AWX settings file

import os

ADMINS = ()

STATIC_ROOT = '/var/lib/awx/public/static'

PROJECTS_ROOT = '/var/lib/awx/projects'

JOBOUTPUT_ROOT = '/var/lib/awx/job_status'

SECRET_KEY = file('/etc/tower/SECRET_KEY', 'rb').read().strip()

ALLOWED_HOSTS = ['*']

INTERNAL_API_URL = 'http://127.0.0.1:80'

AWX_TASK_ENV['HOME'] = '/var/lib/awx'

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

LOGGING['loggers']['django.request']['handlers'] = ['console']
LOGGING['loggers']['rest_framework.request']['handlers'] = ['console']
LOGGING['loggers']['awx']['handlers'] = ['console']
LOGGING['loggers']['awx.main.commands.run_callback_receiver']['handlers'] = ['console']
LOGGING['loggers']['awx.main.commands.inventory_import']['handlers'] = ['console']
LOGGING['loggers']['awx.main.tasks']['handlers'] = ['console']
LOGGING['loggers']['awx.main.scheduler']['handlers'] = ['console']
LOGGING['loggers']['awx.main.commands.run_fact_cache_receiver']['handlers'] = ['console']
LOGGING['loggers']['django_auth_ldap']['handlers'] = ['console']
LOGGING['loggers']['social']['handlers'] = ['console']
LOGGING['loggers']['system_tracking_migrations']['handlers'] = ['console']
LOGGING['loggers']['rbac_migrations']['handlers'] = ['console']

DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'transaction_hooks.backends.postgresql_psycopg2',
        'NAME': os.getenv("DATABASE_NAME", None),
        'USER': os.getenv("DATABASE_USER", None),
        'PASSWORD': os.getenv("DATABASE_PASSWORD", None),
        'HOST': os.getenv("DATABASE_HOST", None),
        'PORT': os.getenv("DATABASE_PORT", None),
    }
}

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
}
