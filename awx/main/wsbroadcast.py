import json
import logging
import asyncio

import aiohttp
from aiohttp import client_exceptions

from channels.layers import get_channel_layer

from django.conf import settings
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder

from awx.main.analytics.broadcast_websocket import (
    BroadcastWebsocketStats,
    BroadcastWebsocketStatsManager,
)


logger = logging.getLogger('awx.main.wsbroadcast')


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
                 stats: BroadcastWebsocketStats,
                 remote_host: str,
                 remote_port: int = settings.BROADCAST_WEBSOCKET_PORT,
                 protocol: str = settings.BROADCAST_WEBSOCKET_PROTOCOL,
                 verify_ssl: bool = settings.BROADCAST_WEBSOCKET_VERIFY_CERT,
                 endpoint: str = 'broadcast'):
        self.name = name
        self.event_loop = event_loop
        self.stats = stats
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

        try:
            if attempt > 0:
                await asyncio.sleep(settings.BROADCAST_WEBSOCKET_RECONNECT_RETRY_RATE_SECONDS)
        except asyncio.CancelledError:
            logger.warn(f"{self.name} connection to {self.remote_host} cancelled")
            raise

        uri = f"{self.protocol}://{self.remote_host}:{self.remote_port}/websocket/{self.endpoint}/"
        timeout = aiohttp.ClientTimeout(total=10)

        secret_val = WebsocketSecretAuthHelper.construct_secret()
        try:
            async with aiohttp.ClientSession(headers={'secret': secret_val},
                                             timeout=timeout) as session:
                async with session.ws_connect(uri, ssl=self.verify_ssl) as websocket:
                    self.stats.record_connection_established()
                    attempt = 0
                    await self.run_loop(websocket)
        except asyncio.CancelledError:
            # TODO: Check if connected and disconnect
            # Possibly use run_until_complete() if disconnect is async
            logger.warn(f"{self.name} connection to {self.remote_host} cancelled")
            self.stats.record_connection_lost()
            raise
        except client_exceptions.ClientConnectorError as e:
            logger.warn(f"Failed to connect to {self.remote_host}: '{e}'. Reconnecting ...")
            self.stats.record_connection_lost()
            self.start(attempt=attempt + 1)
        except asyncio.TimeoutError:
            logger.warn(f"Timeout while trying to connect to {self.remote_host}. Reconnecting ...")
            self.stats.record_connection_lost()
            self.start(attempt=attempt + 1)
        except Exception as e:
            # Early on, this is our canary. I'm not sure what exceptions we can really encounter.
            logger.warn(f"Websocket broadcast client exception {type(e)} {e}")
            self.stats.record_connection_lost()
            self.start(attempt=attempt + 1)

    def start(self, attempt=0):
        self.async_task = self.event_loop.create_task(self.connect(attempt=attempt))

    def cancel(self):
        self.async_task.cancel()


class BroadcastWebsocketTask(WebsocketTask):
    async def run_loop(self, websocket: aiohttp.ClientWebSocketResponse):
        async for msg in websocket:
            self.stats.record_message_received()

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

                await self.channel_layer.group_send(group, {"type": "internal.message", "text": message})


class BroadcastWebsocketManager(object):
    def __init__(self):
        self.event_loop = asyncio.get_event_loop()
        self.broadcast_tasks = dict()
        # parallel dict to broadcast_tasks that tracks stats
        self.local_hostname = get_local_host()
        self.stats_mgr = BroadcastWebsocketStatsManager(self.event_loop, self.local_hostname)

    async def run_per_host_websocket(self):

        while True:
            future_remote_hosts = get_broadcast_hosts()
            current_remote_hosts = self.broadcast_tasks.keys()
            deleted_remote_hosts = set(current_remote_hosts) - set(future_remote_hosts)
            new_remote_hosts = set(future_remote_hosts) - set(current_remote_hosts)

            if deleted_remote_hosts:
                logger.warn(f"{self.local_hostname} going to remove {deleted_remote_hosts} from the websocket broadcast list")
            if new_remote_hosts:
                logger.warn(f"{self.local_hostname} going to add {new_remote_hosts} to the websocket broadcast list")

            for h in deleted_remote_hosts:
                self.broadcast_tasks[h].cancel()
                del self.broadcast_tasks[h]
                self.stats_mgr.delete_remote_host_stats(h)

            for h in new_remote_hosts:
                stats = self.stats_mgr.new_remote_host_stats(h)
                broadcast_task = BroadcastWebsocketTask(name=self.local_hostname,
                                                        event_loop=self.event_loop,
                                                        stats=stats,
                                                        remote_host=h)
                broadcast_task.start()
                self.broadcast_tasks[h] = broadcast_task

            await asyncio.sleep(settings.BROADCAST_WEBSOCKET_NEW_INSTANCE_POLL_RATE_SECONDS)

    def start(self):
        self.stats_mgr.start()

        self.async_task = self.event_loop.create_task(self.run_per_host_websocket())
        return self.async_task
