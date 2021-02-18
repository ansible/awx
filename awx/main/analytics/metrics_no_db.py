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
broadcast_interval = 10 # seconds
logger = logging.getLogger('awx.main.wsbroadcast')

def get_local_host():
    Instance = apps.get_model('main', 'Instance')
    return Instance.objects.me().hostname

def store_metrics(data_json):
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        data = json.loads(data_json)
        logger.debug(f"node {get_local_host()} received metrics from node {data['node']}")
        conn.set(redis_key + "_node_" + data['node'], data['metrics'])

def send_broadcast(conn):
    from awx.main.consumers import emit_channel_notification
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        should_broadcast = False
        if not conn.exists(redis_key + '_last_broadcast'):
            should_broadcast = True
        else:
            last_broadcast = float(conn.get(redis_key + '_last_broadcast'))
            if time.time() - last_broadcast > broadcast_interval:
                should_broadcast = True
        if should_broadcast:
            payload = {
                'node': get_local_host(),
                'metrics': local_metrics().decode('UTF-8'),
            }
            emit_channel_notification("metrics", payload)
            conn.set(redis_key + '_last_broadcast', time.time())

def get_help_text(field):
    return field + "_help_text"

def set_help_text(conn, field, help_text):
    if not conn.hexists(redis_key, get_help_text(field)):
        conn.hset(redis_key, get_help_text(field), help_text)

def hincrby(field, increment_by, help_text=''):
    if increment_by != 0:
        with redis.Redis.from_url(settings.BROKER_URL) as conn:
            conn.hincrby(redis_key, field, increment_by)
            set_help_text(conn, field, help_text)
            send_broadcast(conn)

def hset(field, value, help_text=''):
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        conn.hset(redis_key, field, value)
        set_help_text(conn, field, help_text)
        send_broadcast(conn)

def hincrbyfloat(field, increment_by, help_text=''):
    if increment_by != 0:
        with redis.Redis.from_url(settings.BROKER_URL) as conn:
            conn.hincrbyfloat(redis_key, field, increment_by)
            set_help_text(conn, field, help_text)
            send_broadcast(conn)

# class RedisPipeline():
#     def __init__(self):
#         self.pipeline = redis.Redis.pipeline()
#     def hincrbyfloat(self, field, increment_by, help_text=''):
#         pass
#     def hincrby(self, field, increment_by, help_text=''):
#         if increment_by != 0:
#             with redis.Redis.from_url(settings.BROKER_URL) as conn:
#                 conn.hincrby(redis_key, field, increment_by)
#                 set_help_text(conn, field, help_text)
#                 send_broadcast(conn)
#     def hset(self, field, value, help_text=''):
#         with redis.Redis.from_url(settings.BROKER_URL) as conn:
#             conn.hset(redis_key, field, value)
#             set_help_text(conn, field, help_text)
#             send_broadcast(conn)

def metrics(request):
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        node_metrics = ''
        for m in conn.scan_iter(redis_key + '_node_*'):
            node_metrics += conn.get(m).decode('UTF-8')
        node_metrics += local_metrics().decode('UTF-8')
        return node_metrics

def local_metrics():
    REGISTRY = CollectorRegistry()
    # query_params = request.query_params.copy()
    # tags = ['callbackreceiver', 'events']
    # if not any([i in query_params for i in tags]):
    #     # if query_params does not include anything in tags list, then grab everything
    #     query_params['all'] = ''
    #
    # if tags_in_query_params(['callbackreceiver', 'events', 'all'], query_params):
    #     EVENTS_INSERT_DB.set(bytes_to_int(get('metrics.callbackreceiver', 'events_insert_db')))
    #     EVENTS_BATCH_INSERT_DB.set(bytes_to_int(get('metrics.callbackreceiver', 'events_batch_insert_db')))
    with redis.Redis.from_url(settings.BROKER_URL) as conn:
        # maybe use scan iter
        allfields = conn.hkeys(redis_key)
        for field in allfields:
            field_str = field.decode('UTF-8')
            if field_str.endswith('help_text'):
                continue
            help_text = conn.hget(redis_key, get_help_text(field_str)).decode()
            g = Gauge(field_str + '_total', help_text, ['node'], registry=REGISTRY)
            g.labels(node=get_local_host()).set(float(conn.hget(redis_key, field_str)))
    return generate_latest(registry=REGISTRY)
# def hset(data):
#     with redis.Redis.from_url(settings.BROKER_URL) as conn:
#         conn.hset(data)
# def set(subsystem, field, value, prometheus_type):
#     with redis.Redis.from_url(settings.BROKER_URL) as conn:
#         data_json = json.dumps(value)
#         conn.hset(key, field, data_json)
#
# def get(key, field):
#     with redis.Redis.from_url(settings.BROKER_URL) as conn:
#         data_json = conn.hget(key, field)
#         data = data_json.loads(data_json)
#         return data
#     return None

# def render():
#     pass
#
# def render_to_prometheus():
#     pass
#
# def tags_in_query_params(keywords, query_params):
#     return any([i in query_params for i in keywords])
#
# def bytes_to_int(value):
#     try:
#         return int(value)
#     except:
#         return None


# bash-4.4# awx-manage run_wsbroadcast --status
# Broadcast websocket connection status from "awx-1" to:
# hostname     state            start time                     duration (sec)
# awx          disconnected     N/A                            N/A
# awx-2        connected        2021-02-09 23:53:59.374506     192
# awx-3        connected        2021-02-09 23:53:59.484018     192
#
#======================================================================
# bash-4.4# awx-manage run_dispatcher --status
# Recorded at: 2021-02-09 23:50:52 UTC
# awx[pid:469] workers total=4 min=4 max=80
# .  worker[pid:502] sent=6 finished=6 qsize=0 rss=138.113MB [IDLE]
# .  worker[pid:525] sent=9 finished=8 qsize=1 rss=140.562MB
#      - running d11a492d-dacc-45c8-9aa5-1b7c7e4ea51f RunJob(*[10])
# .  worker[pid:570] sent=7 finished=6 qsize=1 rss=139.105MB
#      - running for: 0.0s f9b48010-7e4f-47e1-b889-d6083a61edf5 run_task_manager(*[])
# .  worker[pid:820] sent=1 finished=1 qsize=0 rss=138.992MB [IDLE]
# ======================================================================
# bash-4.4# awx-manage callback_stats
# main_jobevent
# ↳  last minute 0
# main_inventoryupdateevent
# ↳  last minute 0
# main_projectupdateevent
# ↳  last minute 0
# main_adhoccommandevent
# ↳  last minute 0
