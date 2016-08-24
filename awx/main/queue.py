# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import json

from django.conf import settings

__all__ = ['FifoQueue']

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
