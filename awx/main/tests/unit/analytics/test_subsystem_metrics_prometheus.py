from unittest import mock

from django.test import RequestFactory
from rest_framework.request import Request

from awx.main.analytics.subsystem_metrics import (
    CallbackReceiverMetrics,
    DispatcherMetrics,
    FloatM,
    metrics,
)


SHARED_SUBSYSTEM_METRICS = (
    'subsystem_metrics_pipe_execute_seconds',
    'subsystem_metrics_pipe_execute_calls',
    'subsystem_metrics_send_metrics_seconds',
)


def test_to_prometheus_can_omit_help_type_header():
    metric = FloatM('subsystem_metrics_pipe_execute_seconds', 'Time spent saving metrics to redis')
    instance_data = {'node.example.com': {'subsystem_metrics_pipe_execute_seconds': 1.25}}

    with_header = metric.to_prometheus(instance_data, namespace='dispatcher', include_header=True)
    without_header = metric.to_prometheus(instance_data, namespace='callback_receiver', include_header=False)

    assert with_header.startswith('# HELP subsystem_metrics_pipe_execute_seconds')
    assert '# TYPE subsystem_metrics_pipe_execute_seconds gauge' in with_header
    assert '# HELP' not in without_header
    assert '# TYPE' not in without_header
    assert 'subsystem="callback_receiver"' in without_header


@mock.patch.object(CallbackReceiverMetrics, 'load_other_metrics')
@mock.patch.object(DispatcherMetrics, 'load_other_metrics')
@mock.patch('awx.main.analytics.subsystem_metrics.get_redis_client')
@mock.patch('awx.main.analytics.subsystem_metrics.get_dispatcherd_metrics', return_value='')
@mock.patch('awx.main.analytics.subsystem_metrics.IndirectCountingMetrics')
def test_metrics_emits_single_help_type_for_shared_subsystem_metrics(
    mock_indirect, _mock_dispatcherd, _mock_redis, mock_dispatcher_load, mock_callback_load
):
    """AAP-84834: shared operational metrics must not repeat HELP/TYPE across subsystems."""
    mock_indirect.return_value.generate_metrics.return_value = ''
    mock_dispatcher_load.return_value = {
        'node.example.com': {
            'subsystem_metrics_pipe_execute_seconds': 0.1,
            'subsystem_metrics_pipe_execute_calls': 2,
            'subsystem_metrics_send_metrics_seconds': 0.2,
            'task_manager__schedule_calls': 1,
        }
    }
    mock_callback_load.return_value = {
        'node.example.com': {
            'subsystem_metrics_pipe_execute_seconds': 0.3,
            'subsystem_metrics_pipe_execute_calls': 4,
            'subsystem_metrics_send_metrics_seconds': 0.5,
            'callback_receiver_events_insert_db': 7,
        }
    }

    request = Request(RequestFactory().get('/api/v2/metrics/'))
    payload = metrics(request)

    for metric_name in SHARED_SUBSYSTEM_METRICS:
        assert payload.count(f'# HELP {metric_name} ') == 1
        assert payload.count(f'# TYPE {metric_name} ') == 1
        assert f'{metric_name}{{node="node.example.com",subsystem="dispatcher"}}' in payload
        assert f'{metric_name}{{node="node.example.com",subsystem="callback_receiver"}}' in payload
