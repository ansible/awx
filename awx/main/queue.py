# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import logging

# Django
from django.conf import settings

# AWX
from awx.main.utils.redis import get_redis_client

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
        self.connection = get_redis_client()

    def dispatch(self, obj):
        self.connection.rpush(self.queue, json.dumps(obj, cls=AnsibleJSONEncoder))
