import datetime
import logging
import re

from prometheus_client import (
    Gauge,
    Counter,
    Enum,
    CollectorRegistry,
)

from django.conf import settings


logger = logging.getLogger('awx.analytics.broadcast_websocket')


def dt_to_seconds(dt):
    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds())


def now_seconds():
    return dt_to_seconds(datetime.datetime.now())


def safe_name(s):
    # Replace all non alpha-numeric characters with _
    return re.sub('[^0-9a-zA-Z]+', '_', s)


class ConnectionState:
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'


class Metrics:
    """
    Attributes with underscores are NOT registered
    Attributes WITHOUT underscores ARE registered
    """

    CONNECTION_STATE = ConnectionState()

    def __init__(self, namespace=settings.METRICS_SERVICE_WEBSOCKET_RELAY):
        self.messages_received_total = Counter(
            f'{namespace}_messages_received_total',
            'Number of messages received, to be forwarded, by the broadcast websocket system',
            ['remote_host'],
            registry=None,
        )
        self.connection = Enum(
            f'{namespace}_connection',
            'Websocket broadcast connection established status',
            ['remote_host'],
            states=[self.CONNECTION_STATE.DISCONNECTED, self.CONNECTION_STATE.CONNECTED],
            registry=None,
        )
        self.connection_start = Gauge(
            f'{namespace}_connection_start_time_seconds', 'Time the connection was established since unix epoch in seconds', ['remote_host'], registry=None
        )
        self.producers = Gauge(
            f'{namespace}_producers_count',
            'Number of async workers',
            ['remote_host'],
            registry=None,
        )

    def record_message_received(self, remote_host):
        self.messages_received_total.labels(remote_host=remote_host).inc()

    def record_connection_established(self, remote_host):
        self.connection.labels(remote_host=remote_host).state(self.CONNECTION_STATE.CONNECTED)
        self.connection_start.labels(remote_host=remote_host).set_to_current_time()

    def record_connection_lost(self, remote_host):
        self.connection.labels(remote_host=remote_host).state(self.CONNECTION_STATE.DISCONNECTED)

    def record_producer_start(self, remote_host):
        self.producers.labels(remote_host=remote_host).inc()

    def record_producer_stop(self, remote_host):
        self.producers.labels(remote_host=remote_host).dec()

    def init_host(self, remote_host):
        self.messages_received_total.labels(remote_host=remote_host)
        self.connection.labels(remote_host=remote_host)
        self.connection_start.labels(remote_host=remote_host)


class MetricsForHost:
    def __init__(self, metrics: Metrics, remote_host):
        self._metrics = metrics
        self._remote_host = remote_host

        self._metrics.init_host(self._remote_host)

    def record_message_received(self):
        self._metrics.record_message_received(self._remote_host)

    def record_producer_start(self):
        self._metrics.record_producer_start(self._remote_host)

    def record_producer_stop(self):
        self._metrics.record_producer_stop(self._remote_host)

    def record_connection_established(self):
        self._metrics.record_connection_established(self._remote_host)

    def record_connection_lost(self):
        self._metrics.record_connection_lost(self._remote_host)


class MetricsRegistryBridge:
    """
    Scope: Prometheus CollectorRegistry, Metrics
    """

    def __init__(self, metrics: Metrics, registry: CollectorRegistry, autoregister=True):
        self._metrics = metrics
        self._registry = registry
        self.registered = False

        if autoregister:
            self.register_all_metrics()
            self.registered = True

    def register_all_metrics(self):
        for metric in [v for k, v in vars(self._metrics).items() if not k.startswith('_')]:
            self._registry.register(metric)


class MetricsManager:
    def __init__(self, metrics: Metrics):
        self._metrics = metrics

    def allocate(self, remote_hostname):
        return MetricsForHost(self._metrics, safe_name(remote_hostname))

    def deallocate(self, remote_hostname):
        """
        Intentionally do nothing.

        Keep this function around. The code responsible for calling allocate() should call deallocate().
        Knowing where deallocation should happen is useful.

        It seems to be a patterns and best practice to _not_ delete metrics.
        """
        pass
