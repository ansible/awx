# Copyright (c) 2014, Ansible, Inc.
# All Rights Reserved.

import json

from redis import StrictRedis

redis = StrictRedis('127.0.0.1')  # FIXME: Don't hard-code.


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

    def push(self, value):
        """Push a value onto the right side of the queue."""
        redis.rpush(self._queue_name, json.dumps(value))

    def pop(self):
        """Retrieve a value from the left side of the queue."""
        return json.loads(redis.lpop(self._queue_name))

