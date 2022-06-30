import redis
import json
import time
import logging

from django.conf import settings
from django.apps import apps
from awx.main.consumers import emit_channel_notification

root_key = 'awx_metrics'
logger = logging.getLogger('awx.main.analytics')


class BaseM:
    def __init__(self, field, help_text):
        self.field = field
        self.help_text = help_text
        self.current_value = 0
        self.metric_has_changed = False

    def reset_value(self, conn):
        conn.hset(root_key, self.field, 0)
        self.current_value = 0

    def inc(self, value):
        self.current_value += value
        self.metric_has_changed = True

    def set(self, value):
        self.current_value = value
        self.metric_has_changed = True

    def get(self):
        return self.current_value

    def decode(self, conn):
        value = conn.hget(root_key, self.field)
        return self.decode_value(value)

    def to_prometheus(self, instance_data):
        output_text = f"# HELP {self.field} {self.help_text}\n# TYPE {self.field} gauge\n"
        for instance in instance_data:
            if self.field in instance_data[instance]:
                # on upgrade, if there are stale instances, we can end up with issues where new metrics are not present
                output_text += f'{self.field}{{node="{instance}"}} {instance_data[instance][self.field]}\n'
        return output_text


class FloatM(BaseM):
    def decode_value(self, value):
        if value is not None:
            return float(value)
        else:
            return 0.0

    def store_value(self, conn):
        if self.metric_has_changed:
            conn.hincrbyfloat(root_key, self.field, self.current_value)
            self.current_value = 0
            self.metric_has_changed = False


class IntM(BaseM):
    def decode_value(self, value):
        if value is not None:
            return int(value)
        else:
            return 0

    def store_value(self, conn):
        if self.metric_has_changed:
            conn.hincrby(root_key, self.field, self.current_value)
            self.current_value = 0
            self.metric_has_changed = False


class SetIntM(BaseM):
    def decode_value(self, value):
        if value is not None:
            return int(value)
        else:
            return 0

    def store_value(self, conn):
        if self.metric_has_changed:
            conn.hset(root_key, self.field, self.current_value)
            self.metric_has_changed = False


class SetFloatM(SetIntM):
    def decode_value(self, value):
        if value is not None:
            return float(value)
        else:
            return 0


class HistogramM(BaseM):
    def __init__(self, field, help_text, buckets):
        self.buckets = buckets
        self.buckets_to_keys = {}
        for b in buckets:
            self.buckets_to_keys[b] = IntM(field + '_' + str(b), '')
        self.inf = IntM(field + '_inf', '')
        self.sum = IntM(field + '_sum', '')
        super(HistogramM, self).__init__(field, help_text)

    def reset_value(self, conn):
        conn.hset(root_key, self.field, 0)
        self.inf.reset_value(conn)
        self.sum.reset_value(conn)
        for b in self.buckets_to_keys.values():
            b.reset_value(conn)
        super(HistogramM, self).reset_value(conn)

    def observe(self, value):
        for b in self.buckets:
            if value <= b:
                self.buckets_to_keys[b].inc(1)
                break
        self.sum.inc(value)
        self.inf.inc(1)

    def decode(self, conn):
        values = {'counts': []}
        for b in self.buckets_to_keys:
            values['counts'].append(self.buckets_to_keys[b].decode(conn))
        values['sum'] = self.sum.decode(conn)
        values['inf'] = self.inf.decode(conn)
        return values

    def store_value(self, conn):
        for b in self.buckets:
            self.buckets_to_keys[b].store_value(conn)
        self.sum.store_value(conn)
        self.inf.store_value(conn)

    def to_prometheus(self, instance_data):
        output_text = f"# HELP {self.field} {self.help_text}\n# TYPE {self.field} histogram\n"
        for instance in instance_data:
            for i, b in enumerate(self.buckets):
                output_text += f'{self.field}_bucket{{le="{b}",node="{instance}"}} {sum(instance_data[instance][self.field]["counts"][0:i+1])}\n'
            output_text += f'{self.field}_bucket{{le="+Inf",node="{instance}"}} {instance_data[instance][self.field]["inf"]}\n'
            output_text += f'{self.field}_count{{node="{instance}"}} {instance_data[instance][self.field]["inf"]}\n'
            output_text += f'{self.field}_sum{{node="{instance}"}} {instance_data[instance][self.field]["sum"]}\n'
        return output_text


class Metrics:
    def __init__(self, auto_pipe_execute=False, instance_name=None):
        self.pipe = redis.Redis.from_url(settings.BROKER_URL).pipeline()
        self.conn = redis.Redis.from_url(settings.BROKER_URL)
        self.last_pipe_execute = time.time()
        # track if metrics have been modified since last saved to redis
        # start with True so that we get an initial save to redis
        self.metrics_have_changed = True
        self.pipe_execute_interval = settings.SUBSYSTEM_METRICS_INTERVAL_SAVE_TO_REDIS
        self.send_metrics_interval = settings.SUBSYSTEM_METRICS_INTERVAL_SEND_METRICS
        # auto pipe execute will commit transaction of metric data to redis
        # at a regular interval (pipe_execute_interval). If set to False,
        # the calling function should call .pipe_execute() explicitly
        self.auto_pipe_execute = auto_pipe_execute
        Instance = apps.get_model('main', 'Instance')
        if instance_name:
            self.instance_name = instance_name
        elif settings.IS_TESTING():
            self.instance_name = "awx_testing"
        else:
            self.instance_name = Instance.objects.me().hostname

        # metric name, help_text
        METRICSLIST = [
            SetIntM('callback_receiver_events_queue_size_redis', 'Current number of events in redis queue'),
            IntM('callback_receiver_events_popped_redis', 'Number of events popped from redis'),
            IntM('callback_receiver_events_in_memory', 'Current number of events in memory (in transfer from redis to db)'),
            IntM('callback_receiver_batch_events_errors', 'Number of times batch insertion failed'),
            FloatM('callback_receiver_events_insert_db_seconds', 'Total time spent saving events to database'),
            IntM('callback_receiver_events_insert_db', 'Number of events batch inserted into database'),
            IntM('callback_receiver_events_broadcast', 'Number of events broadcast to other control plane nodes'),
            HistogramM(
                'callback_receiver_batch_events_insert_db', 'Number of events batch inserted into database', settings.SUBSYSTEM_METRICS_BATCH_INSERT_BUCKETS
            ),
            SetFloatM('callback_receiver_event_processing_avg_seconds', 'Average processing time per event per callback receiver batch'),
            FloatM('subsystem_metrics_pipe_execute_seconds', 'Time spent saving metrics to redis'),
            IntM('subsystem_metrics_pipe_execute_calls', 'Number of calls to pipe_execute'),
            FloatM('subsystem_metrics_send_metrics_seconds', 'Time spent sending metrics to other nodes'),
            SetFloatM('task_manager_get_tasks_seconds', 'Time spent in loading tasks from db'),
            SetFloatM('task_manager_start_task_seconds', 'Time spent starting task'),
            SetFloatM('task_manager_process_running_tasks_seconds', 'Time spent processing running tasks'),
            SetFloatM('task_manager_process_pending_tasks_seconds', 'Time spent processing pending tasks'),
            SetFloatM('task_manager__schedule_seconds', 'Time spent in running the entire _schedule'),
            IntM('task_manager_schedule_calls', 'Number of calls to task manager schedule'),
            SetFloatM('task_manager_recorded_timestamp', 'Unix timestamp when metrics were last recorded'),
            SetIntM('task_manager_tasks_started', 'Number of tasks started'),
            SetIntM('task_manager_running_processed', 'Number of running tasks processed'),
            SetIntM('task_manager_pending_processed', 'Number of pending tasks processed'),
            SetIntM('task_manager_tasks_blocked', 'Number of tasks blocked from running'),
            SetFloatM('dependency_manager_get_tasks_seconds', 'Time spent in loading tasks from db'),
            SetFloatM('dependency_manager_generate_dependencies_seconds', 'Time spent generating dependencies for pending tasks'),
            SetFloatM('dependency_manager__schedule_seconds', 'Time spent in running the entire _schedule'),
            IntM('dependency_manager_schedule_calls', 'Number of calls to task manager schedule'),
            SetFloatM('dependency_manager_recorded_timestamp', 'Unix timestamp when metrics were last recorded'),
            SetIntM('dependency_manager_pending_processed', 'Number of pending tasks processed'),
            SetFloatM('workflow_manager__schedule_seconds', 'Time spent in running the entire _schedule'),
            IntM('workflow_manager_schedule_calls', 'Number of calls to task manager schedule'),
            SetFloatM('workflow_manager_recorded_timestamp', 'Unix timestamp when metrics were last recorded'),
            SetFloatM('workflow_manager_spawn_workflow_graph_jobs_seconds', 'Time spent spawning workflow jobs'),
            SetFloatM('workflow_manager_get_tasks_seconds', 'Time spent in loading tasks from db'),
        ]
        # turn metric list into dictionary with the metric name as a key
        self.METRICS = {}
        for m in METRICSLIST:
            self.METRICS[m.field] = m

        # track last time metrics were sent to other nodes
        self.previous_send_metrics = SetFloatM('send_metrics_time', 'Timestamp of previous send_metrics call')

    def reset_values(self):
        # intended to be called once on app startup to reset all metric
        # values to 0
        for m in self.METRICS.values():
            m.reset_value(self.conn)
        self.metrics_have_changed = True
        self.conn.delete(root_key + "_lock")
        for m in self.conn.scan_iter(root_key + '_instance_*'):
            self.conn.delete(m)

    def inc(self, field, value):
        if value != 0:
            self.METRICS[field].inc(value)
            self.metrics_have_changed = True
            if self.auto_pipe_execute is True:
                self.pipe_execute()

    def set(self, field, value):
        self.METRICS[field].set(value)
        self.metrics_have_changed = True
        if self.auto_pipe_execute is True:
            self.pipe_execute()

    def get(self, field):
        return self.METRICS[field].get()

    def decode(self, field):
        return self.METRICS[field].decode(self.conn)

    def observe(self, field, value):
        self.METRICS[field].observe(value)
        self.metrics_have_changed = True
        if self.auto_pipe_execute is True:
            self.pipe_execute()

    def serialize_local_metrics(self):
        data = self.load_local_metrics()
        return json.dumps(data)

    def load_local_metrics(self):
        # generate python dictionary of key values from metrics stored in redis
        data = {}
        for field in self.METRICS:
            data[field] = self.METRICS[field].decode(self.conn)
        return data

    def store_metrics(self, data_json):
        # called when receiving metrics from other instances
        data = json.loads(data_json)
        if self.instance_name != data['instance']:
            logger.debug(f"{self.instance_name} received subsystem metrics from {data['instance']}")
        self.conn.set(root_key + "_instance_" + data['instance'], data['metrics'])

    def should_pipe_execute(self):
        if self.metrics_have_changed is False:
            return False
        if time.time() - self.last_pipe_execute > self.pipe_execute_interval:
            return True
        else:
            return False

    def pipe_execute(self):
        if self.metrics_have_changed is True:
            duration_to_save = time.perf_counter()
            for m in self.METRICS:
                self.METRICS[m].store_value(self.pipe)
            self.pipe.execute()
            self.last_pipe_execute = time.time()
            self.metrics_have_changed = False
            duration_to_save = time.perf_counter() - duration_to_save
            self.METRICS['subsystem_metrics_pipe_execute_seconds'].inc(duration_to_save)
            self.METRICS['subsystem_metrics_pipe_execute_calls'].inc(1)

            duration_to_save = time.perf_counter()
            self.send_metrics()
            duration_to_save = time.perf_counter() - duration_to_save
            self.METRICS['subsystem_metrics_send_metrics_seconds'].inc(duration_to_save)

    def send_metrics(self):
        # more than one thread could be calling this at the same time, so should
        # acquire redis lock before sending metrics
        lock = self.conn.lock(root_key + '_lock')
        if not lock.acquire(blocking=False):
            return
        try:
            current_time = time.time()
            if current_time - self.previous_send_metrics.decode(self.conn) > self.send_metrics_interval:
                payload = {
                    'instance': self.instance_name,
                    'metrics': self.serialize_local_metrics(),
                }
                # store a local copy as well
                self.store_metrics(json.dumps(payload))
                emit_channel_notification("metrics", payload)
                self.previous_send_metrics.set(current_time)
                self.previous_send_metrics.store_value(self.conn)
        finally:
            lock.release()

    def load_other_metrics(self, request):
        # data received from other nodes are stored in their own keys
        # e.g., awx_metrics_instance_awx-1, awx_metrics_instance_awx-2
        # this method looks for keys with "_instance_" in the name and loads the data
        # also filters data based on request query params
        # if additional filtering is added, update metrics_view.md
        instances_filter = request.query_params.getlist("node")
        # get a sorted list of instance names
        instance_names = [self.instance_name]
        for m in self.conn.scan_iter(root_key + '_instance_*'):
            instance_names.append(m.decode('UTF-8').split('_instance_')[1])
        instance_names.sort()
        # load data, including data from the this local instance
        instance_data = {}
        for instance in instance_names:
            if len(instances_filter) == 0 or instance in instances_filter:
                instance_data_from_redis = self.conn.get(root_key + '_instance_' + instance)
                # data from other instances may not be available. That is OK.
                if instance_data_from_redis:
                    instance_data[instance] = json.loads(instance_data_from_redis.decode('UTF-8'))
        return instance_data

    def generate_metrics(self, request):
        # takes the api request, filters, and generates prometheus data
        # if additional filtering is added, update metrics_view.md
        instance_data = self.load_other_metrics(request)
        metrics_filter = request.query_params.getlist("metric")
        output_text = ''
        if instance_data:
            for field in self.METRICS:
                if len(metrics_filter) == 0 or field in metrics_filter:
                    output_text += self.METRICS[field].to_prometheus(instance_data)
        return output_text


def metrics(request):
    m = Metrics()
    return m.generate_metrics(request)
