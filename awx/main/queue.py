# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import logging
import redis

# Django
from django.conf import settings


__all__ = ['CallbackQueueDispatcher']


# use a custom JSON serializer so we can properly handle !unsafe and !vault
# objects that may exist in events emitted by the callback plugin
# see: https://github.com/ansible/ansible/pull/38759
class AnsibleJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if getattr(o, 'yaml_tag', None) == '!vault':
            return o.data
        return super(AnsibleJSONEncoder, self).default(o)


class CallbackQueueDispatcher(object):

    def __init__(self):
        self.queue = getattr(settings, 'CALLBACK_QUEUE', '')
        self.logger = logging.getLogger('awx.main.queue.CallbackQueueDispatcher')
        self.connection = redis.Redis.from_url(settings.BROKER_URL)

    def dispatch(self, obj):
        self.connection.rpush(self.queue, json.dumps(obj, cls=AnsibleJSONEncoder))
