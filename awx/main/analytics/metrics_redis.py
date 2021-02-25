import redis
import json
import time
import logging

from django.conf import settings
from django.apps import apps
from awx.main.consumers import emit_channel_notification
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest
)

redis_key = 'awx_metrics'
broadcast_interval = 3 # seconds
logger = logging.getLogger('awx.main.wsbroadcast')

METRICS = {
    'callback_receiver_events_queue_size_redis':
        {'help_text': 'Current number of events in redis queue'},
    'callback_receiver_events_popped_redis':
        {'help_text': 'Number of events popped from redis'},
    'callback_receiver_events_in_memory':
        {'help_text': 'Current number of events in memory (in transfer from redis to db)'},
    'callback_receiver_batch_events_errors':
        {'help_text': 'Number of times batch insertion failed'},
    'callback_receiver_events_size':
        {'help_text': 'Number of events saved to database'},
    'callback_receiver_events_insert_db_seconds':
        {'help_text': 'Time spent saving events to database'},
    'callback_receiver_events_insert_db':
        {'help_text': 'Number of events inserted into database'},
    'callback_receiver_batch_events_insert_db':
        {'help_text': 'Number of events batch inserted into database'},
    'callback_receiver_events_insert_redis':
        {'help_text': 'Number of events inserted into redis'},
    'debug_send_metrics_interval':
        {'help_text': 'Elapsed time (seconds) between sending the previous two metrics',
         'debug': True},
}


def get_local_instance_name():
    # get local instance name and cache it in redis
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        instance_name = conn.get(redis_key + "_local_instance_name")
        if instance_name is None:
            Instance = apps.get_model('main', 'Instance')
            instance_name = Instance.objects.me().hostname
            conn.set(redis_key + "_local_instance_name", instance_name)
            return instance_name
        else:
            return instance_name.decode('UTF-8')


class RedisConn():
    # context capable class that can accept an already existing conn
    def __init__(self, conn = None):
        if conn is None:
            self.close_conn_on_exit = True
            self.conn = redis.Redis.from_url(settings.BROKER_URL)
            self.conn.client_setname(redis_key)
        else:
            self.close_conn_on_exit = False
            self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self.close_conn_on_exit:
            self.conn.close()


class RedisPipe():
    # Returns a redis client pipeline, intended to be used in a
    # `with RedisPipe() as` block. pipeline.execute() should be called elsewhere
    # to submit transaction to redis
    def __init__(self):
        self.pipe = redis.Redis.from_url(settings.BROKER_URL).pipeline()
        self.pipe.client_setname(redis_key)

    def __enter__(self):
        return self.pipe

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.pipe.reset()


def hincrby(field, increment_by, conn=None):
    if increment_by != 0:
        with RedisConn(conn) as inner_conn:
            inner_conn.hincrby(redis_key, field, increment_by)
            send_metrics()


def hset(field, value, conn=None):
    with RedisConn(conn) as inner_conn:
        inner_conn.hset(redis_key, field, value)
        send_metrics()


def hincrbyfloat(field, increment_by, conn=None):
    if increment_by != 0:
        with RedisConn(conn) as inner_conn:
            inner_conn.hincrbyfloat(redis_key, field, increment_by)
            send_metrics()


def send_metrics():
    # send a serialized copy of the metrics to other nodes
    # only send metrics if last_broadcast is older than broadcast interval
    # uses a lock on redis to prevent this method from being called simultaneously
    with RedisConn() as conn:
        lock = conn.lock(redis_key + '_lock', thread_local = False)
        if not lock.acquire(blocking=False):
            # logger.debug(f"node {get_local_instance_name()} could not acquire lock")
            return
        try:
            # logger.debug(f"node {get_local_instance_name()} acquired lock")
            should_broadcast = False
            metrics_last_sent = 0.0
            if not conn.exists(redis_key + '_last_broadcast'):
                should_broadcast = True
            else:
                last_broadcast = float(conn.get(redis_key + '_last_broadcast'))
                metrics_last_sent = time.time() - last_broadcast
                if metrics_last_sent > broadcast_interval:
                    should_broadcast = True
            if should_broadcast:
                payload = {
                    'node': get_local_instance_name(),
                    'metrics': serialize_local_metrics(),
                }
                emit_channel_notification("metrics", payload)
                # logger.debug(f"node {get_local_instance_name()} sending metrics")
                conn.set(redis_key + '_last_broadcast', time.time())
                conn.hset(redis_key, 'debug_send_metrics_interval', f'{metrics_last_sent:.2f}')
        finally:
            # logger.debug(f"node {get_local_instance_name()} releasing lock")
            lock.release()


def store_metrics(data_json):
    # called when receiving metrics from other nodes
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        data = json.loads(data_json)
        # logger.debug(f"node {get_local_instance_name()} received metrics from node {data['node']}")
        conn.set(redis_key + "_node_" + data['node'], data['metrics'])


def metrics(request):
    # takes the api request, filters, and generates prometheus data
    REGISTRY = CollectorRegistry()
    # logger.debug(f"query params {request.query_params}")
    nodes_filter = request.query_params.getlist("node")
    include_debug_filter = request.query_params.get("debug", "1")
    use_all_nodes = False
    if len(nodes_filter) == 0:
        use_all_nodes = True
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        node_names = [get_local_instance_name()]
        for m in conn.scan_iter(redis_key + '_node_*'):
            node_names.append(m.decode('UTF-8').split('_node_')[1])
        node_names.sort()
        node_data = {}
        for node in node_names:
            if use_all_nodes or node in nodes_filter:
                if node == get_local_instance_name():
                    node_metrics = load_local_metrics()
                else:
                    node_metrics = json.loads(conn.get(redis_key + '_node_' + node).decode('UTF-8'))
                node_data[node] = node_metrics
    if node_data:
        for field in METRICS:
            help_text = METRICS[field]['help_text']
            is_debug = METRICS[field].get('debug', False)
            if is_debug and include_debug_filter == "0":
                continue
            prometheus_object = Gauge(field, help_text, ['node'], registry=REGISTRY)
            for node in node_data:
                prometheus_object.labels(node=node).set(node_data[node][field])
    return generate_latest(registry=REGISTRY)


def load_local_metrics():
    # generate python dictionary of key values from metrics stored in redis
    data = {}
    for field in METRICS:
        with redis.Redis.from_url(settings.BROKER_URL) as conn:
            field_value = conn.hget(redis_key, field)
            if field_value is not None:
                field_value = float(field_value)
            else:
                field_value = 0.0
            data[field] = field_value
    return data


def serialize_local_metrics():
    data = load_local_metrics()
    return json.dumps(data)
