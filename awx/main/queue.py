# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

import json

from redis import StrictRedis

from django.conf import settings

__all__ = ['FifoQueue']


# Determine, based on settings.BROKER_URL (for celery), what the correct Redis
# connection settings are.
redis_kwargs = {}
broker_url = settings.BROKER_URL
if not broker_url.lower().startswith('redis://'):
    raise RuntimeError('Error importing awx.main.queue: Cannot use queue with '
                       'a non-Redis broker configured for celery.\n'
                       'Broker is set to: %s' % broker_url)
broker_url = broker_url[8:]

# There may or may not be a password; address both situations by checking
# for an "@" in the broker URL.
if '@' in broker_url:
    broker_auth, broker_host = broker_url.split('@')
    redis_kwargs['password'] = broker_auth.split(':')[1]
else:
    broker_host = broker_url

# Ignore anything after a / in the broker host.
broker_host = broker_host.split('/')[0]

# If a custom port is present, parse it out.
if ':' in broker_host:
    broker_host, broker_port = broker_host.split(':')
    redis_kwargs['port'] = int(broker_port)

# Now create a StrictRedis object that knows how to connect appropriately.
redis = StrictRedis(broker_host, **redis_kwargs)


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
        return redis.llen(self._queue_name)
        
    def push(self, value):
        """Push a value onto the right side of the queue."""
        redis.rpush(self._queue_name, json.dumps(value))

    def pop(self):
        """Retrieve a value from the left side of the queue."""
        answer = redis.lpop(self._queue_name)
        if answer:
            return json.loads(answer)
