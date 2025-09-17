import django

# dispatcherd publisher logic is likely to be used, but needs manual preload
from dispatcherd.brokers import pg_notify  # noqa

# Cache may not be initialized until we are in the worker, so preload here
from channels_redis import core  # noqa

from awx import prepare_env

from dispatcherd.utils import resolve_callable


prepare_env()

django.setup()  # noqa


from django.conf import settings


# Preload all periodic tasks so their imports will be in shared memory
for name, options in settings.CELERYBEAT_SCHEDULE.items():
    resolve_callable(options['task'])


# Preload in-line import from tasks
from awx.main.scheduler.kubernetes import PodManager  # noqa


from django.core.cache import cache as django_cache
from django.db import connection


connection.close()
django_cache.close()
