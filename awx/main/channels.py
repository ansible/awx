
import os
import json
import logging
import aiohttp
import asyncio
import datetime

from channels_redis.core import RedisChannelLayer
from channels.layers import get_channel_layer

from django.utils.encoding import force_bytes
from django.conf import settings
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger('awx.main')


def wrap_broadcast_msg(group, message: str):
    # TODO: Maybe wrap as "group","message" so that we don't need to
    # encode/decode as json.
    return json.dumps(dict(group=group, message=message), cls=DjangoJSONEncoder)


def unwrap_broadcast_msg(payload: dict):
    return (payload['group'], payload['message'])


def get_broadcast_hosts():
    Instance = apps.get_model('main', 'Instance')
    instances = Instance.objects.filter(rampart_groups__controller__isnull=True) \
                                .exclude(hostname=Instance.objects.me().hostname) \
                                .order_by('hostname') \
                                .values('hostname', 'ip_address') \
                                .distinct()
    return [i['ip_address'] or i['hostname'] for i in instances]


def get_local_host():
    Instance = apps.get_model('main', 'Instance')
    return Instance.objects.me().hostname


class WebsocketTask():
    def __init__(self,
                 name,
                 event_loop,
                 remote_host: str,
                 remote_port: int=settings.BROADCAST_WEBSOCKETS_PORT,
                 protocol: str=settings.BROADCAST_WEBSOCKETS_PROTOCOL,
                 verify_ssl: bool=settings.BROADCAST_WEBSOCKETS_VERIFY_CERT,
                 endpoint: str='broadcast'):
        self.name = name
        self.event_loop = event_loop
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.endpoint = endpoint
        self.protocol = protocol
        self.verify_ssl = verify_ssl
        self.channel_layer = None

    async def run_loop(self, websocket: aiohttp.ClientWebSocketResponse):
        raise RuntimeError("Implement me")

    async def connect(self, attempt):
        from awx.main.consumers import WebsocketSecretAuthHelper # noqa
        logger.debug(f"{self.name} connect attempt {attempt} to {self.remote_host}")

        '''
        Can not put get_channel_layer() in the init code because it is in the init
        path of channel layers i.e. RedisChannelLayer() calls our init code.
        '''
        if not self.channel_layer:
            self.channel_layer = get_channel_layer()

        if attempt > 0:
            await asyncio.sleep(5)
        uri = f"{self.protocol}://{self.remote_host}:{self.remote_port}/websocket/{self.endpoint}/"
        timeout = aiohttp.ClientTimeout(total=10)

        secret_val = WebsocketSecretAuthHelper.construct_secret()
        try:
            async with aiohttp.ClientSession(headers={'secret': secret_val},
                                             timeout=timeout) as session:
                async with session.ws_connect(uri, ssl=self.verify_ssl) as websocket:
                    attempt = 0
                    await self.run_loop(websocket)
        except Exception as e:
            # Early on, this is our canary. I'm not sure what exceptions we can really encounter.
            # Does aiohttp throws an exception if a disconnect happens?
            logger.warn("Websocket broadcast client exception {}".format(e))
        finally:
            # Reconnect
            self.start(attempt=attempt+1)

    def start(self, attempt=0):
        self.event_loop.create_task(self.connect(attempt=attempt))


class BroadcastWebsocketTask(WebsocketTask):
    async def run_loop(self, websocket: aiohttp.ClientWebSocketResponse):
        async for msg in websocket:

            if msg.type == aiohttp.WSMsgType.ERROR:
                break
            elif msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                except json.JSONDecodeError:
                    logmsg = "Failed to decode broadcast message"
                    if logger.isEnabledFor(logging.DEBUG):
                        logmsg = "{} {}".format(logmsg, payload)
                    logger.warn(logmsg)
                    continue

                (group, message) = unwrap_broadcast_msg(payload)

                logger.debug(f"{self.name} broadcasting message")
                await self.channel_layer.group_send(group, {"type": "internal.message", "text": message})


class RedisGroupBroadcastChannelLayer(RedisChannelLayer):
    def __init__(self, *args, **kwargs):
        super(RedisGroupBroadcastChannelLayer, self).__init__(*args, **kwargs)

        remote_hosts = get_broadcast_hosts()
        loop = asyncio.get_event_loop()
        local_hostname = get_local_host()

        broadcast_tasks = [BroadcastWebsocketTask(name=local_hostname,
                                                  event_loop=loop,
                                                  remote_host=h) for h in remote_hosts]

        [t.start() for t in broadcast_tasks]
