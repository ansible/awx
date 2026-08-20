import json
import logging

from django.core.management.base import BaseCommand
from django_guid import set_guid

from awx.main.dispatch import pg_bus_conn
from awx.main.tasks.system import clear_setting_cache

logger = logging.getLogger("awx.main.cache_clear")
EXPECTED_TASK = "awx.main.tasks.system.clear_setting_cache"


class Command(BaseCommand):
    """
    Cache Clear
    Runs as a management command and starts a daemon that listens for a pg_notify message to clear the cache.
    """

    help = "Launch the cache clear daemon"

    def handle(self, *arg, **options):
        try:
            with pg_bus_conn() as conn:
                conn.listen("tower_settings_change")
                for e in conn.events():
                    if e is not None:
                        body = json.loads(e.payload)
                        task = body.get("task")
                        if task != EXPECTED_TASK:
                            logger.critical(
                                "Refusing unexpected task %s; expected %s",
                                task,
                                EXPECTED_TASK,
                            )
                            continue
                        if "guid" in body:
                            set_guid(body["guid"])
                        args = body.get("args", [])
                        kwargs = body.get("kwargs", {})
                        logger.info("Cache clear request received. Clearing now.")
                        clear_setting_cache(*args, **kwargs)

        except Exception:
            # Log unanticipated exception in addition to writing to stderr to get timestamps and other metadata
            logger.exception("Encountered unhandled error in cache clear main loop")
            raise
