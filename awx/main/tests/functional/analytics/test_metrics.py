from unittest import mock

import pytest

from django.test import RequestFactory
from prometheus_client.parser import text_string_to_metric_families
from rest_framework.request import Request
from awx.main import models
from awx.main.analytics.metrics import metrics
from awx.main.analytics.analytics_tasks import send_subsystem_metrics
import awx.main.analytics.subsystem_metrics as subsystem_metrics_module
from awx.main.analytics.subsystem_metrics import IndirectCountingMetrics
from awx.main.analytics.dispatcherd_metrics import get_dispatcherd_metrics
from awx.api.versioning import reverse

EXPECTED_VALUES = {
    'awx_system_info': 1.0,
    'awx_organizations_total': 1.0,
    'awx_users_total': 1.0,
    'awx_teams_total': 1.0,
    'awx_inventories_total': 1.0,
    'awx_projects_total': 1.0,
    'awx_job_templates_total': 1.0,
    'awx_workflow_job_templates_total': 1.0,
    'awx_hosts_total': 1.0,
    'awx_hosts_total': 1.0,
    'awx_schedules_total': 1.0,
    'awx_sessions_total': 0.0,
    'awx_status_total': 0.0,
    'awx_running_jobs_total': 0.0,
    'awx_instance_capacity': 100.0,
    'awx_instance_consumed_capacity': 0.0,
    'awx_instance_remaining_capacity': 100.0,
    'awx_instance_cpu': 0.0,
    'awx_instance_memory': 0.0,
    'awx_instance_info': 1.0,
    'awx_license_instance_total': 0,
    'awx_license_instance_free': 0,
    'awx_pending_jobs_total': 0,
    'awx_database_connections_total': 1,
    'awx_license_expiry': 0,
}


@pytest.mark.django_db
def test_metrics_counts(organization_factory, job_template_factory, workflow_job_template_factory):
    objs = organization_factory('org', superusers=['admin'])
    jt = job_template_factory('test', organization=objs.organization, inventory='test_inv', project='test_project', credential='test_cred')
    workflow_job_template_factory('test')
    models.Team(organization=objs.organization).save()
    models.Host(inventory=jt.inventory).save()
    models.Schedule(rrule='DTSTART;TZID=America/New_York:20300504T150000', unified_job_template=jt.job_template).save()

    output = metrics()
    gauges = text_string_to_metric_families(output.decode('UTF-8'))

    for gauge in gauges:
        for sample in gauge.samples:
            # name, label, value, timestamp, exemplar
            name, _, value, _, _, _ = sample
            assert EXPECTED_VALUES[name] == value


def get_metrics_view_db_only():
    return reverse('api:metrics_view') + '?dbonly=1'


@pytest.mark.django_db
def test_metrics_permissions(get, admin, org_admin, alice, bob, organization):
    assert get(get_metrics_view_db_only(), user=admin).status_code == 200
    assert get(get_metrics_view_db_only(), user=org_admin).status_code == 403
    assert get(get_metrics_view_db_only(), user=alice).status_code == 403
    assert get(get_metrics_view_db_only(), user=bob).status_code == 403
    organization.auditor_role.members.add(bob)
    assert get(get_metrics_view_db_only(), user=bob).status_code == 403

    bob.is_system_auditor = True
    assert get(get_metrics_view_db_only(), user=bob).status_code == 200


@pytest.mark.django_db
def test_metrics_http_methods(get, post, patch, put, options, admin):
    assert get(get_metrics_view_db_only(), user=admin).status_code == 200
    assert put(get_metrics_view_db_only(), user=admin).status_code == 405
    assert patch(get_metrics_view_db_only(), user=admin).status_code == 405
    assert post(get_metrics_view_db_only(), user=admin).status_code == 405
    assert options(get_metrics_view_db_only(), user=admin).status_code == 200


class DummyMetricsResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dispatcherd_metrics_node_filter_match(mocker, settings):
    settings.CLUSTER_HOST_ID = "awx-1"
    payload = b'# HELP test_metric A test metric\n# TYPE test_metric gauge\ntest_metric 1\n'

    def fake_urlopen(url, timeout=1.0):
        return DummyMetricsResponse(payload)

    mocker.patch('urllib.request.urlopen', fake_urlopen)

    request = Request(RequestFactory().get('/api/v2/metrics/', {'node': 'awx-1'}))

    assert get_dispatcherd_metrics(request) == payload.decode('utf-8')


def test_dispatcherd_metrics_node_filter_excludes_local(mocker, settings):
    settings.CLUSTER_HOST_ID = "awx-1"

    def fake_urlopen(*args, **kwargs):
        raise AssertionError("urlopen should not be called when node filter excludes local node")

    mocker.patch('urllib.request.urlopen', fake_urlopen)

    request = Request(RequestFactory().get('/api/v2/metrics/', {'node': 'awx-2'}))

    assert get_dispatcherd_metrics(request) == ''


def test_dispatcherd_metrics_metric_filter_excludes_unrelated(mocker):
    def fake_urlopen(*args, **kwargs):
        raise AssertionError("urlopen should not be called when metric filter excludes dispatcherd metrics")

    mocker.patch('urllib.request.urlopen', fake_urlopen)

    request = Request(RequestFactory().get('/api/v2/metrics/', {'metric': 'awx_system_info'}))

    assert get_dispatcherd_metrics(request) == ''


@mock.patch('awx.main.analytics.analytics_tasks.IndirectCountingMetrics')
@mock.patch('awx.main.analytics.analytics_tasks.CallbackReceiverMetrics')
@mock.patch('awx.main.analytics.analytics_tasks.DispatcherMetrics')
def test_send_subsystem_metrics(mock_dispatcher, mock_callback, mock_indirect):
    """send_subsystem_metrics calls send_metrics on all subsystem metric classes."""
    send_subsystem_metrics()
    mock_dispatcher.return_value.send_metrics.assert_called_once()
    mock_callback.return_value.send_metrics.assert_called_once()
    mock_indirect.return_value.send_metrics.assert_called_once()


@pytest.mark.django_db
def test_indirect_counting_metrics_init():
    """IndirectCountingMetrics can be instantiated and has expected metric fields."""
    m = IndirectCountingMetrics(metrics_have_changed=False)
    assert 'indirect_node_audit_records_created' in m.METRICS
    assert 'indirect_node_query_execution_seconds' in m.METRICS
    assert 'indirect_node_jq_query_errors' in m.METRICS
    assert 'indirect_node_fallback_cleanup_seconds' in m.METRICS


@mock.patch.object(subsystem_metrics_module, 'IndirectCountingMetrics')
@mock.patch.object(subsystem_metrics_module, 'CallbackReceiverMetrics')
@mock.patch.object(subsystem_metrics_module, 'DispatcherMetrics')
@mock.patch.object(subsystem_metrics_module, 'get_dispatcherd_metrics', return_value='')
def test_subsystem_metrics_function_includes_indirect_counting(mock_dispatcherd, mock_dispatcher, mock_callback, mock_indirect):
    """subsystem_metrics.metrics() calls generate_metrics on IndirectCountingMetrics."""
    for m in (mock_dispatcher, mock_callback, mock_indirect):
        m.return_value.generate_metrics.return_value = ''
    request = mock.MagicMock()
    subsystem_metrics_module.metrics(request)
    mock_indirect.return_value.generate_metrics.assert_called_once_with(request)


def _family_of(sample_name, known_families):
    """Map a sample name (e.g. foo_bucket) back to its metric family (foo)."""
    for suffix in ('_bucket', '_sum', '_count'):
        if sample_name.endswith(suffix) and sample_name[: -len(suffix)] in known_families:
            return sample_name[: -len(suffix)]
    return sample_name


def assert_valid_exposition(text):
    """
    Check the rules of the prometheus text format that strict parsers enforce:
    one HELP and one TYPE per family, TYPE directly after HELP, and all of a
    family's samples contiguous, directly beneath its header.
    """
    helps, types, current, closed = set(), set(), None, set()
    families = {line.split()[2] for line in text.splitlines() if line.startswith('# HELP ')}
    for line in filter(None, text.splitlines()):
        if line.startswith('# HELP '):
            name = line.split()[2]
            assert name not in helps, f'duplicate HELP for {name}'
            helps.add(name)
            if current:
                closed.add(current)
            current = name
        elif line.startswith('# TYPE '):
            name = line.split()[2]
            assert name not in types, f'duplicate TYPE for {name}'
            assert name == current, f'TYPE for {name} does not follow its HELP'
            types.add(name)
        else:
            name = _family_of(line.split('{')[0].split(' ')[0], families)
            assert name == current, f'sample for {name} found under {current}'
            assert name not in closed, f'samples for {name} are not contiguous'


def test_merge_metric_families_groups_shared_families():
    """A family emitted by two collectors gets one header with both samples directly beneath it."""
    dispatcher = (
        '# HELP shared_seconds Shared metric\n# TYPE shared_seconds gauge\nshared_seconds{subsystem="dispatcherd"} 1\n'
        '# HELP only_dispatcher Only here\n# TYPE only_dispatcher gauge\nonly_dispatcher 2\n'
    )
    callback = (
        '# HELP only_callback Only there\n# TYPE only_callback gauge\nonly_callback 3\n'
        '# HELP shared_seconds Shared metric\n# TYPE shared_seconds gauge\nshared_seconds{subsystem="callback_receiver"} 4\n'
    )
    merged = subsystem_metrics_module.merge_metric_families(dispatcher, callback)

    assert merged == (
        '# HELP shared_seconds Shared metric\n# TYPE shared_seconds gauge\n'
        'shared_seconds{subsystem="dispatcherd"} 1\nshared_seconds{subsystem="callback_receiver"} 4\n'
        '# HELP only_dispatcher Only here\n# TYPE only_dispatcher gauge\nonly_dispatcher 2\n'
        '# HELP only_callback Only there\n# TYPE only_callback gauge\nonly_callback 3\n'
    )
    assert_valid_exposition(merged)


def test_merge_metric_families_edge_cases():
    """Empty inputs, histograms and non-metric lines are handled."""
    assert subsystem_metrics_module.merge_metric_families() == ''
    assert subsystem_metrics_module.merge_metric_families('', '') == ''

    histogram = '# HELP h Some histogram\n# TYPE h histogram\nh_bucket{le="1"} 1\nh_bucket{le="+Inf"} 2\nh_count 2\nh_sum 3\n'
    merged = subsystem_metrics_module.merge_metric_families(histogram, '# HELP g Gauge\n# TYPE g gauge\ng 1\n', histogram)
    assert merged.count('# HELP h ') == 1
    assert merged.count('# TYPE h ') == 1
    # the repeated histogram's samples were appended under the single header
    assert merged.count('h_bucket{le="+Inf"} 2') == 2
    assert_valid_exposition(merged)


@mock.patch.object(subsystem_metrics_module, 'get_dispatcherd_metrics')
@mock.patch.object(subsystem_metrics_module, 'get_redis_client')
def test_subsystem_metrics_output_is_valid_with_shared_families(mock_redis, mock_dispatcherd):
    """
    The metrics exported by every subsystem (pipe_execute_seconds etc.) must be
    valid prometheus text once all subsystems have reported (AAP-102021).
    """
    mock_dispatcherd.return_value = '# HELP dispatcher_messages_received_total Number of messages\n# TYPE dispatcher_messages_received_total counter\ndispatcher_messages_received_total 1.0\n'

    def fake_load_other_metrics(self, request):
        data = {}
        for field, metric in self.METRICS.items():
            if isinstance(metric, subsystem_metrics_module.HistogramM):
                data[field] = {'counts': [0] * len(metric.buckets), 'sum': 0, 'inf': 0}
            else:
                data[field] = 1
        return {'awx-1': data}

    request = mock.MagicMock()
    request.query_params.getlist.return_value = []
    with mock.patch.object(subsystem_metrics_module.Metrics, 'load_other_metrics', autospec=True, side_effect=fake_load_other_metrics):
        output = subsystem_metrics_module.metrics(request)

    assert_valid_exposition(output)
    for field in ('subsystem_metrics_pipe_execute_seconds', 'subsystem_metrics_pipe_execute_calls', 'subsystem_metrics_send_metrics_seconds'):
        assert output.count(f'# HELP {field} ') == 1
        assert output.count(f'# TYPE {field} ') == 1
        # one sample per subsystem that exports the metric
        for subsystem in ('dispatcherd', 'callback_receiver', 'indirect_counting'):
            assert f'{field}{{node="awx-1",subsystem="{subsystem}"}} 1' in output
    assert 'dispatcher_messages_received_total 1.0' in output
