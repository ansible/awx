# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

import os
import logging
import signal
import time

from django import db


from awx.main.utils.redis import get_redis_client
from awx.main.dispatch.pool import WorkerPool

logger = logging.getLogger('awx.main.commands.run_callback_receiver')


def signame(sig):
    return dict((k, v) for v, k in signal.__dict__.items() if v.startswith('SIG') and not v.startswith('SIG_'))[sig]


class AWXConsumerRedis(object):

    def __init__(self, name, worker):
        self.name = name
        self.pool = WorkerPool()
        self.pool.init_workers(worker.work_loop)
        self.redis = get_redis_client()

    def run(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        logger.info(f'Callback receiver started with pid={os.getpid()}')
        db.connection.close()  # logs use database, so close connection

        while True:
            time.sleep(60)

    def stop(self, signum, frame):
        logger.warning('received {}, stopping'.format(signame(signum)))
        raise SystemExit()
