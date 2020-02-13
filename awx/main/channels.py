
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


def dt_to_seconds(dt):
    return int((dt - datetime.datetime(1970,1,1)).total_seconds())


def now_seconds():
    return dt_to_seconds(datetime.datetime.now())


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


# Second granularity; Per-minute
class FixedSlidingWindow():
    def __init__(self, start_time=None):
        self.buckets = dict()
        self.start_time = start_time or now_seconds()

    def cleanup(self, now_bucket=now_seconds()):
        if self.start_time + 60 >= now_bucket:
            self.start_time = now_bucket - 60 + 1

            # Delete old entries
            for k,v in self.buckets.items():
                if k < self.start_time:
                    del self.buckets[k]

    def record(self, ts=datetime.datetime.now()):
        now_bucket = int((ts-datetime.datetime(1970,1,1)).total_seconds())

        val = self.buckets.get(now_bucket, 0)
        self.buckets[now_bucket] = val + 1

        self.cleanup(now_bucket)

    def sum(self):
        self.cleanup()
        return sum(self.buckets.values()) or 0


class Stats():
    def __init__(self, name):
        self.name = name
        self._messages_received_per_minute = FixedSlidingWindow()
        self._messages_received = 0
        self._is_connected = False
        self._connection_established_ts = None

    def record_message_received(self, ts=datetime.datetime.now()):
        self._messages_received += 1
        self._messages_received_per_minute.record(ts)

    def get_messages_received_total(self):
        return self._messages_received

    def get_messages_received_per_minute(self):
        self._messages_received_per_minute.sum()

    def record_connection_established(self, ts=datetime.datetime.now()):
        self._connection_established_ts = ts

    def record_connection_lost(self, ts=datetime.datetime.now()):
        self._connection_established_ts = None
        self._is_connected = False

    def get_connection_duration(self):
        return (datetime.datetime.now() - self._connection_established_ts).total_seconds()



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
        self.stats = Stats(name)
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
                    self.stats.record_connection_established()
                    attempt = 0
                    await self.run_loop(websocket)
        except Exception as e:
            # Early on, this is our canary. I'm not sure what exceptions we can really encounter.
            # Does aiohttp throws an exception if a disconnect happens?
            logger.warn("Websocket broadcast client exception {}".format(e))
        finally:
            self.stats.record_connection_lost()
            # Reconnect
            self.start(attempt=attempt+1)

    def start(self, attempt=0):
        self.event_loop.create_task(self.connect(attempt=attempt))


class HealthWebsocketTask(WebsocketTask):
    def __init__(self, *args, **kwargs):
        self.period = kwargs.pop('period', 10)
        self.broadcast_stats = kwargs.pop('broadcast_stats', [])

        super().__init__(*args, endpoint='health', **kwargs)

        self.period_abs = None
        # Ideally, we send a health beat at exactly the period. In reality
        # there is always jitter due to OS needs, system load, etc.
        # This variable tracks that offset.
        self.last_period_offset = 0

    async def run_loop(self, websocket: aiohttp.ClientWebSocketResponse):
        '''
        now = datetime.datetime.now()
        if not self.period_abs:
            self.period_abs = now

        sleep_time = self.period_abs + self.period


        if now <= next_period:
            logger.warn("Websocket broadcast missed sending health ping.")
        else:
            await asyncio.sleep(sleep_time)


        sleep_time = datetime.datetime.now() - (self.last_period + datetime.timedelta(seconds=PERIOD))
        '''

        # Start stats loop
        self.event_loop.create_task(self.run_calc_stats_loop())

        # Let this task loop be the send loop
        await self.run_send_stats_loop(websocket)

    async def run_calc_stats_loop(self):
        """
        Do any periodic calculations needed. i.e. sampling
        """
        await asyncio.sleep(1)

    async def run_send_stats_loop(self, websocket: aiohttp.ClientWebSocketResponse):
        while True:
            msg = {
                "sending_host": self.name,
                "remote_hosts": [],
            }
            for s in self.broadcast_stats:
                msg['remote_hosts'].append({
                    'name': s.name,
                    'messages_received': s.get_messages_received_total(),
                    'messages_received_per_minute': s.get_messages_received_per_minute(),
                })

            logger.debug(f"Sending health message {msg}")
            await websocket.send_json(msg)
            await asyncio.sleep(10)


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

                logger.debug(f"{self.name} broadcasting message")
                await self.channel_layer.group_send(group, {"type": "internal.message", "text": message})


class RedisGroupBroadcastChannelLayer(RedisChannelLayer):
    def __init__(self, *args, **kwargs):
        super(RedisGroupBroadcastChannelLayer, self).__init__(*args, **kwargs)

        remote_hosts = get_broadcast_hosts()
        loop = asyncio.get_event_loop()
        local_hostname = get_local_host()

        broadcast_tasks = [BroadcastWebsocketTask(local_hostname, loop, h) for h in remote_hosts]
        broadcast_stats = [t.stats for t in broadcast_tasks]
        health_tasks = [HealthWebsocketTask(local_hostname, loop, h, broadcast_stats=broadcast_stats) for h in remote_hosts]

        [t.start() for t in broadcast_tasks]
        [t.start() for t in health_tasks]

