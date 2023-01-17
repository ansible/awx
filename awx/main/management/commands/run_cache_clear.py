import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from awx.main.dispatch import pg_bus_conn
from awx.conf import settings_registry

logger = logging.getLogger('awx.main.cache_clear')


class Command(BaseCommand):
    """
    Cache Clear
    Runs as a management command and starts a daemon that listens for a pg_notify message to clear the cache.
    """

    help = 'Launch the cache clear daemon'

    def handle(self, *arg, **options):
        try:
            with pg_bus_conn(new_connection=True) as conn:
                conn.listen("tower_settings_change")
                for e in conn.events(yield_timeouts=True):
                    if e is not None:
                        logger.info("Cache clear request received. Clearing now")
                        # clear the cache of the keys in the payload
                        setting_keys = e.payload
                        orig_len = len(setting_keys)
                        for i in range(orig_len):
                            for dependent_key in settings_registry.get_dependent_settings(setting_keys[i]):
                                setting_keys.append(dependent_key)
                        cache_keys = set(setting_keys)
                        logger.info('cache delete_many(%r)', cache_keys)
                        cache.delete_many(cache_keys)
        except Exception:
            # Log unanticipated exception in addition to writing to stderr to get timestamps and other metadata
            logger.exception('Encountered unhandled error in cache clear main loop')
            raise
