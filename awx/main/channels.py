
import os
import json
import logging
import websockets
import asyncio

from channels_redis.core import RedisChannelLayer
from channels.layers import get_channel_layer

from django.conf import settings
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger('awx.main')
BROADCAST_GROUP = 'broadcast-group_send'


def wrap_broadcast_msg(group, message):
    # TODO: Maybe wrap as "group","message" so that we don't need to
    # encode/decode as json.
    return json.dumps(dict(group=group, message=message), cls=DjangoJSONEncoder)


def unwrap_broadcast_msg(payload):
    return (payload['group'], payload['message'])


class RedisGroupBroadcastChannelLayer(RedisChannelLayer):
    def __init__(self, *args, **kwargs):
        super(RedisGroupBroadcastChannelLayer, self).__init__(*args, **kwargs)
        Instance = apps.get_model('main', 'Instance')

        self.broadcast_hosts = [h[0] for h in Instance.objects.all().exclude(hostname=Instance.objects.me().hostname).values_list('hostname')]
        self.broadcast_websockets = set()

        loop = asyncio.get_event_loop()
        for host in self.broadcast_hosts:
            loop.create_task(self.run(host, settings.WEBSOCKETS_PORT))

    async def run(self, host, port, secret='abc123'):
        channel_layer = get_channel_layer()
        uri = "ws://{}:{}/websocket/".format(host, port)
        # TODO: Better loop and disconect/reconnect handling
        async with websockets.connect(uri, extra_headers={'secret': secret}) as websocket:
            while True:
                try:
                    payload = json.loads(await websocket.recv())
                except json.JSONDecodeError:
                    logmsg = "Failed to decode broadcast message"
                    if logger.isEnabledFor(logging.DEBUG):
                        logmsg = "{} {}".format(logmsg, payload)
                    logger.warn(logmsg)
                    continue

                # HACK: Carry over to handle our v1 channels "API"
                if 'accept' in payload:
                    return
                (group, message) = unwrap_broadcast_msg(payload)

                await channel_layer.group_send(group, {"type": "internal.message", "text": message})


