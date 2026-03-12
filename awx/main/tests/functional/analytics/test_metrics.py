import pytest

from django.test import RequestFactory
from prometheus_client.parser import text_string_to_metric_families
from rest_framework.request import Request
from awx.main import models
from awx.main.analytics.metrics import metrics
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
