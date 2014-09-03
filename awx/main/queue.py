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


class PubSub(object):
    """An abstraction class implemented for pubsub.

    Intended to allow alteration of backend details in a single, consistent
    way throughout the Tower application.
    """
    def __init__(self, queue_name):
        """Instantiate a pubsub object, which is able to interact with a
        Redis key as a pubsub.

        Ideally this should be used with `contextmanager.closing` to ensure
        well-behavedness:

            from contextmanager import closing

            with closing(PubSub('foobar')) as foobar:
                for message in foobar.listen(wait=0.1):
                    <deal with message>
        """
        self._queue_name = queue_name
        self._ps = redis.pubsub(ignore_subscribe_messages=True)
        self._ps.subscribe(queue_name)

    def publish(self, message):
        """Publish a message to the given queue."""
        redis.publish(self._queue_name, json.dumps(message))

    def retrieve(self):
        """Retrieve a single message from the subcription channel
        and return it.
        """
        return self._ps.get_message()

    def listen(self, wait=0.001):
        """Listen to content from the subscription channel indefinitely,
        and yield messages as they are retrieved.
        """
        while True:
            message = self.retrieve()
            if message is None:
                time.sleep(max(wait, 0.001))
            else:
                yield json.loads(message)

    def close(self):
        """Close the pubsub connection."""
        self._ps.close()
