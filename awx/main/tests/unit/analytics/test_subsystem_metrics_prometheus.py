from unittest import mock

from django.test import RequestFactory
from rest_framework.request import Request

from awx.main.analytics.subsystem_metrics import (
    SHARED_SUBSYSTEM_METRIC_FIELDS,
    CallbackReceiverMetrics,
    DispatcherMetrics,
    FloatM,
    IndirectCountingMetrics,
    metrics,
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


def _family_line_indexes(payload, metric_name):
    indexes = []
    for i, line in enumerate(payload.splitlines()):
        if (
            line.startswith(f'# HELP {metric_name} ')
            or line.startswith(f'# TYPE {metric_name} ')
            or line.startswith(f'{metric_name}{{')
        ):
            indexes.append(i)
    return indexes


@mock.patch.object(IndirectCountingMetrics, 'load_other_metrics', return_value={})
@mock.patch.object(CallbackReceiverMetrics, 'load_other_metrics')
@mock.patch.object(DispatcherMetrics, 'load_other_metrics')
@mock.patch('awx.main.analytics.subsystem_metrics.get_redis_client')
@mock.patch('awx.main.analytics.subsystem_metrics.get_dispatcherd_metrics', return_value='')
def test_metrics_emits_single_help_type_for_shared_subsystem_metrics(
    _mock_dispatcherd, _mock_redis, mock_dispatcher_load, mock_callback_load, _mock_indirect_load
):
    """AAP-84834: shared metrics — one HELP/TYPE and contiguous samples across subsystems."""
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

    for metric_name in SHARED_SUBSYSTEM_METRIC_FIELDS:
        assert payload.count(f'# HELP {metric_name} ') == 1
        assert payload.count(f'# TYPE {metric_name} ') == 1
        assert f'{metric_name}{{node="node.example.com",subsystem="dispatcher"}}' in payload
        assert f'{metric_name}{{node="node.example.com",subsystem="callback_receiver"}}' in payload

        indexes = _family_line_indexes(payload, metric_name)
        assert indexes, metric_name
        assert indexes == list(range(indexes[0], indexes[0] + len(indexes))), (
            f'{metric_name} family is not contiguous: indexes={indexes}\n{payload}'
        )
