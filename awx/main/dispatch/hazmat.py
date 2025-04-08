import django

from awx import prepare_env

from dispatcherd.utils import resolve_callable


prepare_env()

django.setup()  # noqa


from django.conf import settings


# Preload all periodic tasks so their imports will be in shared memory
for name, options in settings.CELERYBEAT_SCHEDULE.items():
    resolve_callable(options['task'])


from django.core.cache import cache as django_cache
from django.db import connection


connection.close()
django_cache.close()
