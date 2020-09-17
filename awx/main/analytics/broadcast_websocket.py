import datetime
import asyncio
import logging
import aioredis
import redis
import re

from prometheus_client import (
    generate_latest,
    Gauge,
    Counter,
    Enum,
    CollectorRegistry,
    parser,
)

from django.conf import settings


BROADCAST_WEBSOCKET_REDIS_KEY_NAME = 'broadcast_websocket_stats'


logger = logging.getLogger('awx.analytics.broadcast_websocket')


def dt_to_seconds(dt):
    return int((dt - datetime.datetime(1970,1,1)).total_seconds())


def now_seconds():
    return dt_to_seconds(datetime.datetime.now())


def safe_name(s):
    # Replace all non alpha-numeric characters with _
    return re.sub('[^0-9a-zA-Z]+', '_', s)


# Second granularity; Per-minute
class FixedSlidingWindow():
    def __init__(self, start_time=None):
        self.buckets = dict()
        self.start_time = start_time or now_seconds()

    def cleanup(self, now_bucket=None):
        now_bucket = now_bucket or now_seconds()
        if self.start_time + 60 < now_bucket:
            self.start_time = now_bucket - 60

            # Delete old entries
            for k in list(self.buckets.keys()):
                if k < self.start_time:
                    del self.buckets[k]

    def record(self, ts=None):
        now_bucket = ts or dt_to_seconds(datetime.datetime.now())

        val = self.buckets.get(now_bucket, 0)
        self.buckets[now_bucket] = val + 1

        self.cleanup(now_bucket)

    def render(self, ts=None):
        self.cleanup(now_bucket=ts)
        return sum(self.buckets.values()) or 0


class BroadcastWebsocketStatsManager():
    def __init__(self, event_loop, local_hostname):
        self._local_hostname = local_hostname

        self._event_loop = event_loop
        self._stats = dict()
        self._redis_key = BROADCAST_WEBSOCKET_REDIS_KEY_NAME

    def new_remote_host_stats(self, remote_hostname):
        self._stats[remote_hostname] = BroadcastWebsocketStats(self._local_hostname,
                                                               remote_hostname)
        return self._stats[remote_hostname]

    def delete_remote_host_stats(self, remote_hostname):
        del self._stats[remote_hostname]

    async def run_loop(self):
        try:
            redis_conn = await aioredis.create_redis_pool(settings.BROKER_URL)
            while True:
                stats_data_str = ''.join(stat.serialize() for stat in self._stats.values())
                await redis_conn.set(self._redis_key, stats_data_str)

                await asyncio.sleep(settings.BROADCAST_WEBSOCKET_STATS_POLL_RATE_SECONDS)
        except Exception as e:
            logger.warn(e)
            await asyncio.sleep(settings.BROADCAST_WEBSOCKET_STATS_POLL_RATE_SECONDS)
            self.start()

    def start(self):
        self.async_task = self._event_loop.create_task(self.run_loop())
        return self.async_task

    @classmethod
    def get_stats_sync(cls):
        '''
        Stringified verion of all the stats
        '''
        redis_conn = redis.Redis.from_url(settings.BROKER_URL)
        stats_str = redis_conn.get(BROADCAST_WEBSOCKET_REDIS_KEY_NAME) or b''
        return parser.text_string_to_metric_families(stats_str.decode('UTF-8'))


class BroadcastWebsocketStats():
    def __init__(self, local_hostname, remote_hostname):
        self._local_hostname = local_hostname
        self._remote_hostname = remote_hostname
        self._registry = CollectorRegistry()

        # TODO: More robust replacement
        self.name = safe_name(self._local_hostname)
        self.remote_name = safe_name(self._remote_hostname)

        self._messages_received_total = Counter(f'awx_{self.remote_name}_messages_received_total',
                                                'Number of messages received, to be forwarded, by the broadcast websocket system',
                                                registry=self._registry)
        self._messages_received = Gauge(f'awx_{self.remote_name}_messages_received',
                                        'Number forwarded messages received by the broadcast websocket system, for the duration of the current connection',
                                        registry=self._registry)
        self._connection = Enum(f'awx_{self.remote_name}_connection',
                                'Websocket broadcast connection',
                                states=['disconnected', 'connected'],
                                registry=self._registry)
        self._connection.state('disconnected')
        self._connection_start = Gauge(f'awx_{self.remote_name}_connection_start',
                                       'Time the connection was established',
                                       registry=self._registry)

        self._messages_received_per_minute = Gauge(f'awx_{self.remote_name}_messages_received_per_minute',
                                                   'Messages received per minute',
                                                   registry=self._registry)
        self._internal_messages_received_per_minute = FixedSlidingWindow()

    def unregister(self):
        self._registry.unregister(f'awx_{self.remote_name}_messages_received')
        self._registry.unregister(f'awx_{self.remote_name}_connection')

    def record_message_received(self):
        self._internal_messages_received_per_minute.record()
        self._messages_received.inc()
        self._messages_received_total.inc()

    def record_connection_established(self):
        self._connection.state('connected')
        self._connection_start.set_to_current_time()
        self._messages_received.set(0)

    def record_connection_lost(self):
        self._connection.state('disconnected')

    def get_connection_duration(self):
        return (datetime.datetime.now() - self._connection_established_ts).total_seconds()

    def render(self):
        msgs_per_min = self._internal_messages_received_per_minute.render()
        self._messages_received_per_minute.set(msgs_per_min)

    def serialize(self):
        self.render()

        registry_data = generate_latest(self._registry).decode('UTF-8')
        return registry_data
