import logging
import time

from dispatcherd.worker.task import TaskWorker

from django.conf import settings
from django.db import connection

from awx.main.tasks.receptor import receptor_config_exists

logger = logging.getLogger('awx.main.dispatch')


class AWXTaskWorker(TaskWorker):
    def on_start(self) -> None:
        """Get worker connected so that first task it gets will be worked quickly"""
        connection.ensure_connection()

        if settings.IS_K8S:
            for attempt in range(60):
                if receptor_config_exists():
                    break
                logger.info("Waiting for receptor config to be created by EE sidecar...")
                time.sleep(2)
            else:
                logger.error("Receptor config not created after 120s.")

    def pre_task(self, message) -> None:
        """This should remedy bad connections that can not fix themselves"""
        connection.close_if_unusable_or_obsolete()
