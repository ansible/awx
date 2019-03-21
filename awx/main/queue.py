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
from kombu.serialization import registry

__all__ = ['CallbackQueueDispatcher']


# use a custom JSON serializer so we can properly handle !unsafe and !vault
# objects that may exist in events emitted by the callback plugin
# see: https://github.com/ansible/ansible/pull/38759
class AnsibleJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if getattr(o, 'yaml_tag', None) == '!vault':
            return o.data
        return super(AnsibleJSONEncoder, self).default(o)


registry.register(
    'json-ansible',
    lambda obj: json.dumps(obj, cls=AnsibleJSONEncoder),
    lambda obj: json.loads(obj),
    content_type='application/json',
    content_encoding='utf-8'
)


class CallbackQueueDispatcher(object):

    def __init__(self):
        self.callback_connection = getattr(settings, 'BROKER_URL', None)
        self.connection_queue = getattr(settings, 'CALLBACK_QUEUE', '')
        self.connection = None
        self.exchange = None
        self.logger = logging.getLogger('awx.main.queue.CallbackQueueDispatcher')

    def dispatch(self, obj):
        if not self.callback_connection or not self.connection_queue:
            return
        active_pid = os.getpid()
        for retry_count in range(4):
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
                                 serializer='json-ansible',
                                 compression='bzip2',
                                 exchange=self.exchange,
                                 declare=[self.exchange],
                                 delivery_mode="persistent" if settings.PERSISTENT_CALLBACK_MESSAGES else "transient",
                                 routing_key=self.connection_queue)
                return
            except Exception as e:
                self.logger.info('Publish Job Event Exception: %r, retry=%d', e,
                                 retry_count, exc_info=True)
