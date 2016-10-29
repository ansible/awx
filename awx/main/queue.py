# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import logging
import os

# Django
from django.conf import settings

# Kombu
from kombu import Connection, Exchange, Producer

__all__ = ['FifoQueue', 'CallbackQueueDispatcher']


# TODO: Figure out wtf to do with this class
class FifoQueue(object):
    """An abstraction class implemented for a simple push/pull queue.

    Intended to allow alteration of backend details in a single, consistent
    way throughout the Tower application.
    """
    def __init__(self, queue_name):
        """Instantiate a queue object, which is able to interact with a
        particular queue.
        """
        self._queue_name = queue_name

    def __len__(self):
        """Return the length of the Redis list."""
        #return redis.llen(self._queue_name)
        return 0
        
    def push(self, value):
        """Push a value onto the right side of the queue."""
        #redis.rpush(self._queue_name, json.dumps(value))

    def pop(self):
        """Retrieve a value from the left side of the queue."""
        #answer = redis.lpop(self._queue_name)
        answer = None
        if answer:
            return json.loads(answer)


class CallbackQueueDispatcher(object):

    def __init__(self):
        self.callback_connection = getattr(settings, 'CALLBACK_CONNECTION', None)
        self.connection_queue = getattr(settings, 'CALLBACK_QUEUE', '')
        self.connection = None
        self.exchange = None
        self.logger = logging.getLogger('awx.main.queue.CallbackQueueDispatcher')

    def dispatch(self, obj):
        if not self.callback_connection or not self.connection_queue:
            return
        active_pid = os.getpid()
        for retry_count in xrange(4):
            try:
                if not hasattr(self, 'connection_pid'):
                    self.connection_pid = active_pid
                if self.connection_pid != active_pid:
                    self.connection = None
                if self.connection is None:
                    self.connection = Connection(self.callback_connection)
                    self.exchange = Exchange(self.connection_queue, type='direct')

                producer = Producer(self.connection)
                producer.publish(obj,
                                 serializer='json',
                                 compression='bzip2',
                                 exchange=self.exchange,
                                 declare=[self.exchange],
                                 routing_key=self.connection_queue)
                return
            except Exception, e:
                self.logger.info('Publish Job Event Exception: %r, retry=%d', e,
                                 retry_count, exc_info=True)
