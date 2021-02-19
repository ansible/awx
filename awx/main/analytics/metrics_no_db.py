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
}

def get_local_instance_name():
    # get local instance name and cache it in redis
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        instance_name = conn.get(redis_key + "_local_instance_name")
        if instance_name is None:
            logger.debug(f"setting local instance name redis key")
            Instance = apps.get_model('main', 'Instance')
            instance_name = Instance.objects.me().hostname
            instance_name = conn.set(redis_key + "_local_instance_name", instance_name)
        return instance_name.decode('UTF-8')

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

def send_broadcast(conn):
    # send a serialized copy of the metrics to other nodes
    # only send metrics if last_broadcast is older than broadcast interval
    # uses a lock on redis to prevent this method from being called simultaneously
    from awx.main.consumers import emit_channel_notification
    lock = conn.lock(redis_key + '_lock', thread_local = False)
    if not lock.acquire(blocking=False):
        # logger.debug(f"node {get_local_instance_name()} could not acquire lock")
        return
    try:
        # logger.debug(f"node {get_local_instance_name()} acquired lock")
        should_broadcast = False
        if not conn.exists(redis_key + '_last_broadcast'):
            should_broadcast = True
        else:
            last_broadcast = float(conn.get(redis_key + '_last_broadcast'))
            if (time.time() - last_broadcast) > broadcast_interval:
                should_broadcast = True
        if should_broadcast:
            payload = {
                'node': get_local_instance_name(),
                'metrics': serialize_local_metrics(),
            }
            emit_channel_notification("metrics", payload)
            logger.debug(f"node {get_local_instance_name()} sending metrics")
            conn.set(redis_key + '_last_broadcast', time.time())
    finally:
        # logger.debug(f"node {get_local_instance_name()} releasing lock")
        lock.release()

def store_metrics(data_json):
    # called when receiving metrics from other nodes
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        data = json.loads(data_json)
        logger.debug(f"node {get_local_instance_name()} received metrics from node {data['node']}")
        conn.set(redis_key + "_node_" + data['node'], data['metrics'])

def metrics(request):
    # takes the api request, filters, and generates prometheus data
    REGISTRY = CollectorRegistry()
    logger.debug(f"query params {request.query_params}")
    nodes_filter = request.query_params.getlist("node")
    use_all_nodes = False
    if len(nodes_filter) == 0:
        use_all_nodes = True
    all_node_data = {}
    if use_all_nodes or get_local_instance_name() in nodes_filter:
        all_node_data[get_local_instance_name()] = load_local_metrics()
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        for m in conn.scan_iter(redis_key + '_node_*'):
            node_name = m.decode('UTF-8').split('_node_')[1]
            logger.debug(f"{node_name} in {nodes_filter}")
            if use_all_nodes or node_name in nodes_filter:
                node_metrics = json.loads(conn.get(m).decode('UTF-8'))
                all_node_data[node_name] = node_metrics
    if all_node_data:
        for field in METRICS:
            help_text = METRICS[field]['help_text']
            prometheus_object = Gauge(field, help_text, ['node'], registry=REGISTRY)
            for node in all_node_data:
                prometheus_object.labels(node=node).set(all_node_data[node][field])
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
