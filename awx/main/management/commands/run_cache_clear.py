import logging
import json

from django.core.management.base import BaseCommand
from awx.main.dispatch import pg_bus_conn
from awx.main.dispatch.worker.task import TaskWorker

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
                        body = json.loads(e.payload)
                        logger.info(f"Cache clear request received. Clearing now, payload: {e.payload}")
                        TaskWorker.run_callable(body)
                    else:
                        logger.info('run_clear_cache got timeout')

        except Exception:
            # Log unanticipated exception in addition to writing to stderr to get timestamps and other metadata
            logger.exception('Encountered unhandled error in cache clear main loop')
            raise
