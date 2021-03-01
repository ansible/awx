import redis
import json
import time
import logging

from django.conf import settings
from django.apps import apps
from django.utils.timezone import now as tz_now
from awx.main.consumers import emit_channel_notification
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest
)

redis_key = 'awx_metrics'
send_metrics_interval = 3 # seconds
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
    'debug_send_metrics_timestamp':
        {'help_text': 'Timestamp when last metrics were sent',
         'debug': True},
}


def get_local_instance_name():
    # get local instance name and store it in redis for fast retrieval
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
        # if conn is not passed in, create one
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
    # `with RedisPipe() as` context. pipeline.execute() should be called explicitly
    # to submit transaction to redis
    def __init__(self):
        self.pipe = redis.Redis.from_url(settings.BROKER_URL).pipeline()
        self.pipe.client_setname(redis_key)

    def __enter__(self):
        return self.pipe

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.pipe.reset()


def setfloat(field, value, conn=None):
    with RedisConn(conn) as inner_conn:
        with RedisConn() as tmp_conn:
            previous_value = tmp_conn.hget(redis_key, field)
            logger.debug(f"{previous_value}")
            if previous_value is not None and float(previous_value) == value:
                logger.debug(f"{previous_value} compare with {float(previous_value)}")
                return
        # logger.debug(f"{previous_value} compare with {float(previous_value)}")
        inner_conn.hset(redis_key, field, value)
        logger.debug(f"updated {field}")
        send_metrics()


def incrint(field, increment_by, conn=None):
    if increment_by != 0:
        with RedisConn(conn) as inner_conn:
            inner_conn.hincrby(redis_key, field, increment_by)
            send_metrics()


def incrfloat(field, increment_by, conn=None):
    if increment_by != 0:
        with RedisConn(conn) as inner_conn:
            inner_conn.hincrbyfloat(redis_key, field, increment_by)
            logger.debug(f"updated {field}")
            send_metrics()


def send_metrics():
    # send a serialized copy of the metrics to other instances
    # only send metrics if last_broadcast is older than send_metrics_interval
    # uses a lock on redis to prevent this method from being called simultaneously
    with RedisConn() as conn:
        lock = conn.lock(redis_key + '_lock', thread_local = False)
        if not lock.acquire(blocking=False):
            # logger.debug(f"instance {get_local_instance_name()} could not acquire lock")
            return
        try:
            # logger.debug(f"instance {get_local_instance_name()} acquired lock")
            should_broadcast = False
            metrics_last_sent = 0.0
            if not conn.exists(redis_key + '_last_broadcast'):
                should_broadcast = True
            else:
                last_broadcast = float(conn.get(redis_key + '_last_broadcast'))
                metrics_last_sent = time.time() - last_broadcast
                if metrics_last_sent > send_metrics_interval:
                    should_broadcast = True
            if should_broadcast:
                payload = {
                    'instance': get_local_instance_name(),
                    'metrics': serialize_local_metrics(),
                }
                emit_channel_notification("metrics", payload)
                logger.debug(f"instance {get_local_instance_name()} sending metrics")
                conn.set(redis_key + '_last_broadcast', time.time())
                conn.hset(redis_key, 'debug_send_metrics_interval', f'{metrics_last_sent:.2f}')
                conn.hset(redis_key, 'debug_send_metrics_timestamp', str(tz_now()))
        finally:
            # logger.debug(f"instance {get_local_instance_name()} releasing lock")
            lock.release()


def store_metrics(data_json):
    # called when receiving metrics from other instances
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        data = json.loads(data_json)
        # logger.debug(f"instance {get_local_instance_name()} received metrics from instance {data['instance_hostname']}")
        conn.set(redis_key + "_instance_" + data['instance'], data['metrics'])


def metrics(request):
    # takes the api request, filters, and generates prometheus data
    REGISTRY = CollectorRegistry()
    # logger.debug(f"query params {request.query_params}")
    instances_filter = request.query_params.getlist("node")
    include_debug_filter = request.query_params.get("debug", "1")
    use_all_instances = False
    if len(instances_filter) == 0:
        use_all_instances = True
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        instance_names = [get_local_instance_name()]
        for m in conn.scan_iter(redis_key + '_instance_*'):
            instance_names.append(m.decode('UTF-8').split('_instance_')[1])
        instance_names.sort()
        instance_data = {}
        for instance in instance_names:
            if use_all_instances or instance in instances_filter:
                if instance == get_local_instance_name():
                    instance_metrics = load_local_metrics()
                else:
                    instance_metrics = json.loads(conn.get(redis_key + '_instance_' + instance).decode('UTF-8'))
                instance_data[instance] = instance_metrics
    if instance_data:
        for field in METRICS:
            help_text = METRICS[field]['help_text']
            is_debug = METRICS[field].get('debug', False)
            if is_debug and include_debug_filter == "0":
                continue
            prometheus_object = Gauge(field, help_text, ['instance'], registry=REGISTRY)
            for instance in instance_data:
                prometheus_object.labels(node=instance).set(instance_data[instance][field])
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
