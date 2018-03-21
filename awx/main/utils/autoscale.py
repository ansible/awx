from celery.utils.log import get_logger
from celery.worker.autoscale import Autoscaler, AUTOSCALE_KEEPALIVE
from django.conf import settings
import psutil

logger = get_logger('awx.main.tasks')


class DynamicAutoScaler(Autoscaler):

    def __init__(self, pool, max_concurrency, min_concurrency=0, worker=None,
                 keepalive=AUTOSCALE_KEEPALIVE, mutex=None):
        super(DynamicAutoScaler, self).__init__(pool, max_concurrency,
                                                min_concurrency, worker,
                                                keepalive, mutex)
        settings_absmem = getattr(settings, 'SYSTEM_TASK_ABS_MEM', None)
        if settings_absmem is not None:
            total_memory_gb = int(settings_absmem)
        else:
            total_memory_gb = (psutil.virtual_memory().total >> 30) + 1  # noqa: round up

        # 5 workers per GB of total memory
        self.max_concurrency = min(max_concurrency, (total_memory_gb * 5))
        logger.warn('celery worker dynamic --autoscale={},{}'.format(
            self.max_concurrency,
            self.min_concurrency
        ))
