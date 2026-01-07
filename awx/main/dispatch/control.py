import logging
import uuid
import json

from django.db import connection

from awx.main.dispatch import get_task_queuename
from awx.main.utils.redis import get_redis_client

from . import pg_bus_conn

logger = logging.getLogger('awx.main.dispatch')


class Control(object):
    services = ('dispatcher', 'callback_receiver')
    result = None

    def __init__(self, service, host=None):
        if service not in self.services:
            raise RuntimeError('{} must be in {}'.format(service, self.services))
        self.service = service
        self.queuename = host or get_task_queuename()

    def status(self, *args, **kwargs):
        r = get_redis_client()
        if self.service == 'dispatcher':
            stats = r.get(f'awx_{self.service}_statistics') or b''
            return stats.decode('utf-8')
        else:
            workers = []
            for key in r.keys('awx_callback_receiver_statistics_*'):
                workers.append(r.get(key).decode('utf-8'))
            return '\n'.join(workers)

    @classmethod
    def generate_reply_queue_name(cls):
        return f"reply_to_{str(uuid.uuid4()).replace('-','_')}"
