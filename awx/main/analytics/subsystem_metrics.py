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

root_key = 'awx_metrics'
send_metrics_interval = 3 # seconds
logger = logging.getLogger('awx.main.wsbroadcast')


class BaseM():
    def __init__(self, field, help_text):
        self.field = field
        self.help_text = help_text

    def decode(self, conn):
        value = conn.hget(root_key, self.field)
        return self.decode_value(value)

    def decode_to_str(self, conn):
        value = self.decode(conn)
        return self.value_to_str(value)

    def set(self, value, conn):
        conn.hset(root_key, self.field, value)


class FloatM(BaseM):
    def inc(self, value, conn):
        conn.hincrbyfloat(root_key, self.field, value)

    def decode_value(self, value):
        if value is not None:
            return float(value)
        else:
            return 0.0

    def value_to_str(self, value):
        return f'{value:.2f}'


class IntM(BaseM):
    def inc(self, value, conn):
        conn.hincrby(root_key, self.field, value)

    def decode_value(self, value):
        if value is not None:
            return int(value)
        else:
            return 0

    def value_to_str(self, value):
        return str(value)


class Metrics():
    def __init__(self, conn = None):
        if conn is None:
            self.conn = redis.Redis.from_url(settings.BROKER_URL)
            self.conn.client_setname("subsystem_metrics")
        else:
            self.conn = conn

        Instance = apps.get_model('main', 'Instance')
        instance_name = Instance.objects.me().hostname
        self.instance_name = instance_name

    def inc(self, field, value, conn = None):
        if value != 0:
            if conn is None:
                conn = self.conn
            METRICS[field].inc(value, conn)
            self.send_metrics()

    def set(self, field, value, conn = None):
        # conn here could be a pipeline(), so we must get a new conn to do the
        # previous value lookup. Otherwise the hget() won't execute until
        # pipeline().execute is called in the calling function.
        with self.conn as inner_conn:
            previous_value = METRICS[field].decode(inner_conn)
            if previous_value is not None and previous_value == value:
                return
        if conn is None:
            conn = self.conn
        METRICS[field].set(value, conn)
        self.send_metrics()

    def serialize_local_metrics(self):
        data = self.load_local_metrics()
        return json.dumps(data)

    def load_local_metrics(self):
        # generate python dictionary of key values from metrics stored in redis
        data = {}
        for field in METRICS:
            data[field] = METRICS[field].decode_to_str(self.conn)
        return data

    def store_metrics(self, data_json):
        # called when receiving metrics from other instances
        data = json.loads(data_json)
        logger.debug(f"instance {self.instance_name} received subsystem metrics from instance {data['instance']}")
        self.conn.set(root_key + "_instance_" + data['instance'], data['metrics'])

    def send_metrics(self):
        # more than one thread could be calling this at the same time, so should
        # get acquire redis lock before sending metrics
        lock = self.conn.lock(root_key + '_lock', thread_local = False)
        if not lock.acquire(blocking=False):
            return
        try:
            should_broadcast = False
            metrics_last_sent = 0.0
            if not self.conn.exists(root_key + '_last_broadcast'):
                should_broadcast = True
            else:
                last_broadcast = float(self.conn.get(root_key + '_last_broadcast'))
                metrics_last_sent = time.time() - last_broadcast
                if metrics_last_sent > send_metrics_interval:
                    should_broadcast = True
            if should_broadcast:
                payload = {
                    'instance': self.instance_name,
                    'metrics': self.serialize_local_metrics(),
                }
                emit_channel_notification("metrics", payload)
                self.conn.set(root_key + '_last_broadcast', time.time())
        finally:
            lock.release()

    def load_other_metrics(self, request):
        # data received from other nodes are stored in their own keys
        # e.g., awx_metrics_instance_awx-1, awx_metrics_instance_awx-2
        # this method looks for keys with "_instance_" in the name and loads the data
        # also filters data based on request query params
        instances_filter = request.query_params.getlist("node")
        use_all_instances = False
        if len(instances_filter) == 0:
            use_all_instances = True
        # get a sorted list of instance names
        instance_names = [self.instance_name]
        for m in self.conn.scan_iter(root_key + '_instance_*'):
            instance_names.append(m.decode('UTF-8').split('_instance_')[1])
        instance_names.sort()

        # load data, including data from the this local instance
        instance_data = {}
        for instance in instance_names:
            if use_all_instances or instance in instances_filter:
                if instance == self.instance_name:
                    instance_metrics = self.load_local_metrics()
                else:
                    instance_metrics = json.loads(self.conn.get(root_key + '_instance_' + instance).decode('UTF-8'))
                instance_data[instance] = instance_metrics
        return instance_data

    def generate_metrics(self, request):
        # takes the api request, filters, and generates prometheus data
        REGISTRY = CollectorRegistry()
        instance_data = self.load_other_metrics(request)
        if instance_data:
            for field in METRICS:
                help_text = METRICS[field].help_text
                prometheus_object = Gauge(field, help_text, ['node'], registry=REGISTRY)
                for instance in instance_data:
                    prometheus_object.labels(node=instance).set(instance_data[instance][field])
        return generate_latest(registry=REGISTRY)


def metrics(request):
    m = Metrics()
    return m.generate_metrics(request)


# metric name, help_text
METRICSLIST = [
    IntM('callback_receiver_events_queue_size_redis',
         'Current number of events in redis queue'),
    IntM('callback_receiver_events_popped_redis',
         'Number of events popped from redis'),
    IntM('callback_receiver_events_in_memory',
         'Current number of events in memory (in transfer from redis to db)'),
    IntM('callback_receiver_batch_events_errors',
         'Number of times batch insertion failed'),
    IntM('callback_receiver_events_size',
         'Size of events saved to db'),
    FloatM('callback_receiver_events_insert_db_seconds',
           'Time spent saving events to database'),
    IntM('callback_receiver_events_insert_db',
         'Number of events batch inserted into database'),
    IntM('callback_receiver_batch_events_insert_db',
         'Number of events batch inserted into database'),
    IntM('callback_receiver_events_insert_redis',
         'Number of events inserted into redis'),
]
# turn metric list into dictionary with the metric name as a key
METRICS = {}
for m in METRICSLIST:
    METRICS[m.field] = m
