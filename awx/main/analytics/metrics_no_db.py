import redis
import json
import time
import logging

from django.conf import settings
from django.apps import apps
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Summary,
    Histogram,
    generate_latest
)

redis_key = 'awx_metrics'
broadcast_interval = 3 # seconds
logger = logging.getLogger('awx.main.wsbroadcast')

METRICS = {
    'callback_receiver_events_queue_size_redis_total':
        {'type': 'Gauge',
        'help_text': 'Current number of events in redis queue'},
    'callback_receiver_events_popped_redis_total':
        {'type': 'Counter',
        'help_text': 'Total number of events popped from redis'},
    'callback_receiver_events_in_memory_total':
        {'type': 'Gauge',
        'help_text': 'Total number of events in memory (in transfer from redis to db)'},
    'callback_receiver_batch_events_errors_total':
        {'type': 'Counter',
        'help_text': 'Number of times batch insertion failed'},
    'callback_receiver_events_size_total':
        {'type': 'Counter',
        'help_text': 'Total size of stdout for events saved to database'},
    'callback_receiver_events_insert_db_seconds_total':
        {'type': 'Counter',
        'help_text': 'Time spent saving events to database'},
    'callback_receiver_events_insert_db_total':
        {'type': 'Counter',
        'help_text': 'Number of events inserted into database'},
    'callback_receiver_batch_events_insert_db_total':
        {'type': 'Counter',
        'help_text': 'Number of events batch inserted into database'},
    'callback_receiver_events_insert_redis_total':
        {'type': 'Counter',
        'help_text': 'Total number of events inserted into redis'},
}

def get_local_host():
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        hostname = conn.get(redis_key + "_" + "local_hostname")
        if hostname is None:
            logger.debug(f"setting local hostname redis key")
            Instance = apps.get_model('main', 'Instance')
            hostname = Instance.objects.me().hostname
            hostname = conn.set(redis_key + "_" + "local_hostname", hostname)
        return hostname.decode('UTF-8')

def store_metrics(data_json):
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        data = json.loads(data_json)
        logger.debug(f"node {get_local_host()} received metrics from node {data['node']}")
        conn.set(redis_key + "_node_" + data['node'], data['metrics'])

def send_broadcast(conn):
    from awx.main.consumers import emit_channel_notification
    lock = conn.lock(redis_key + '_lock', thread_local = False)
    if not lock.acquire(blocking=False):
        # logger.debug(f"node {get_local_host()} could not acquire lock")
        return
    try:
        # logger.debug(f"node {get_local_host()} acquired lock")
        should_broadcast = False
        if not conn.exists(redis_key + '_last_broadcast'):
            should_broadcast = True
        else:
            last_broadcast = float(conn.get(redis_key + '_last_broadcast'))
            if (time.time() - last_broadcast) > broadcast_interval:
                should_broadcast = True
        if should_broadcast:
            payload = {
                'node': get_local_host(),
                'metrics': serialize_local_metrics(),
            }
            emit_channel_notification("metrics", payload)
            logger.debug(f"node {get_local_host()} sending metrics")
            conn.set(redis_key + '_last_broadcast', time.time())
    finally:
        # logger.debug(f"node {get_local_host()} releasing lock")
        lock.release()

def hincrby(field, increment_by):
    if increment_by != 0:
        with redis.Redis.from_url(settings.BROKER_URL) as conn:
            conn.hincrby(redis_key, field, increment_by)
            send_broadcast(conn)

def hset(field, value):
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        conn.hset(redis_key, field, value)
        send_broadcast(conn)

def hincrbyfloat(field, increment_by):
    if increment_by != 0:
        with redis.Redis.from_url(settings.BROKER_URL) as conn:
            conn.hincrbyfloat(redis_key, field, increment_by)
            send_broadcast(conn)

def metrics(request):
    REGISTRY = CollectorRegistry()
    logger.debug(f"query params {request.query_params}")
    nodes_filter = request.query_params.getlist("node", None)
    all_nodes = False
    if nodes_filter is None:
        all_nodes = True
    all_node_data = {}
    if all_nodes or get_local_host() in nodes_filter:
        all_node_data[get_local_host()] = load_local_metrics()
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        for m in conn.scan_iter(redis_key + '_node_*'):
            hostname = m.decode('UTF-8').split('_node_')[1]
            logger.debug(f"{hostname} in {nodes_filter}")
            if all_nodes or hostname in nodes_filter:
                node_metrics = json.loads(conn.get(m).decode('UTF-8'))
                all_node_data[hostname] = node_metrics
    for field in METRICS:
        help_text = METRICS[field]['help_text']
        prometheus_object = Gauge(field, help_text, ['node'], registry=REGISTRY)
        for node in all_node_data:
            prometheus_object.labels(node=node).set(all_node_data[node][field])
    return generate_latest(registry=REGISTRY)

def load_local_metrics():
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
