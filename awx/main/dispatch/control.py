import logging
import uuid
import json

from django.conf import settings
from django.db import connection
import redis

from awx.main.dispatch import get_task_queuename

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
        r = redis.Redis.from_url(settings.BROKER_URL)
        if self.service == 'dispatcher':
            stats = r.get(f'awx_{self.service}_statistics') or b''
            return stats.decode('utf-8')
        else:
            workers = []
            for key in r.keys('awx_callback_receiver_statistics_*'):
                workers.append(r.get(key).decode('utf-8'))
            return '\n'.join(workers)

    def running(self, *args, **kwargs):
        return self.control_with_reply('running', *args, **kwargs)

    def cancel(self, task_ids, with_reply=True):
        if with_reply:
            return self.control_with_reply('cancel', extra_data={'task_ids': task_ids})
        else:
            self.control({'control': 'cancel', 'task_ids': task_ids, 'reply_to': None}, extra_data={'task_ids': task_ids})

    def schedule(self, *args, **kwargs):
        return self.control_with_reply('schedule', *args, **kwargs)

    @classmethod
    def generate_reply_queue_name(cls):
        return f"reply_to_{str(uuid.uuid4()).replace('-','_')}"

    def control_with_reply(self, command, timeout=5, extra_data=None):
        logger.warning('checking {} {} for {}'.format(self.service, command, self.queuename))
        reply_queue = Control.generate_reply_queue_name()
        self.result = None

        if not connection.get_autocommit():
            raise RuntimeError('Control-with-reply messages can only be done in autocommit mode')

        with pg_bus_conn(select_timeout=timeout) as conn:
            conn.listen(reply_queue)
            send_data = {'control': command, 'reply_to': reply_queue}
            if extra_data:
                send_data.update(extra_data)
            conn.notify(self.queuename, json.dumps(send_data))

            for reply in conn.events(yield_timeouts=True):
                if reply is None:
                    logger.error(f'{self.service} did not reply within {timeout}s')
                    raise RuntimeError(f"{self.service} did not reply within {timeout}s")
                break

        return json.loads(reply.payload)

    def control(self, msg, **kwargs):
        with pg_bus_conn() as conn:
            conn.notify(self.queuename, json.dumps(msg))
