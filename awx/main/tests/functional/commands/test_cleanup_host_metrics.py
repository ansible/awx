import pytest

from awx.main.tasks.host_metrics import HostMetricTask
from awx.main.models.inventory import HostMetric
from awx.main.tests.factories.fixtures import mk_host_metric
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone


@pytest.mark.django_db
def test_no_host_metrics():
    """No-crash test"""
    assert HostMetric.objects.count() == 0
    HostMetricTask().cleanup(soft_threshold=0, hard_threshold=0)
    HostMetricTask().cleanup(soft_threshold=24, hard_threshold=42)
    assert HostMetric.objects.count() == 0


@pytest.mark.django_db
def test_delete_exception():
    """Crash test"""
    with pytest.raises(ValueError):
        HostMetricTask().soft_cleanup("")
    with pytest.raises(TypeError):
        HostMetricTask().hard_cleanup(set())


@pytest.mark.django_db
@pytest.mark.parametrize('threshold', [settings.CLEANUP_HOST_METRICS_SOFT_THRESHOLD, 20])
def test_soft_delete(threshold):
    """Metrics with last_automation < threshold are updated to deleted=True"""
    mk_host_metric('host_1', first_automation=ago(months=1), last_automation=ago(months=1), deleted=False)
    mk_host_metric('host_2', first_automation=ago(months=1), last_automation=ago(months=1), deleted=True)
    mk_host_metric('host_3', first_automation=ago(months=1), last_automation=ago(months=threshold, hours=-1), deleted=False)
    mk_host_metric('host_4', first_automation=ago(months=1), last_automation=ago(months=threshold, hours=-1), deleted=True)
    mk_host_metric('host_5', first_automation=ago(months=1), last_automation=ago(months=threshold, hours=1), deleted=False)
    mk_host_metric('host_6', first_automation=ago(months=1), last_automation=ago(months=threshold, hours=1), deleted=True)
    mk_host_metric('host_7', first_automation=ago(months=1), last_automation=ago(months=42), deleted=False)
    mk_host_metric('host_8', first_automation=ago(months=1), last_automation=ago(months=42), deleted=True)

    assert HostMetric.objects.count() == 8
    assert HostMetric.active_objects.count() == 4

    for i in range(2):
        HostMetricTask().cleanup(soft_threshold=threshold)
        assert HostMetric.objects.count() == 8

        hostnames = set(HostMetric.objects.filter(deleted=False).order_by('hostname').values_list('hostname', flat=True))
        assert hostnames == {'host_1', 'host_3'}


@pytest.mark.django_db
@pytest.mark.parametrize('threshold', [settings.CLEANUP_HOST_METRICS_HARD_THRESHOLD, 20])
def test_hard_delete(threshold):
    """Metrics with last_deleted < threshold and deleted=True are deleted from the db"""
    mk_host_metric('host_1', first_automation=ago(months=1), last_deleted=ago(months=1), deleted=False)
    mk_host_metric('host_2', first_automation=ago(months=1), last_deleted=ago(months=1), deleted=True)
    mk_host_metric('host_3', first_automation=ago(months=1), last_deleted=ago(months=threshold, hours=-1), deleted=False)
    mk_host_metric('host_4', first_automation=ago(months=1), last_deleted=ago(months=threshold, hours=-1), deleted=True)
    mk_host_metric('host_5', first_automation=ago(months=1), last_deleted=ago(months=threshold, hours=1), deleted=False)
    mk_host_metric('host_6', first_automation=ago(months=1), last_deleted=ago(months=threshold, hours=1), deleted=True)
    mk_host_metric('host_7', first_automation=ago(months=1), last_deleted=ago(months=42), deleted=False)
    mk_host_metric('host_8', first_automation=ago(months=1), last_deleted=ago(months=42), deleted=True)

    assert HostMetric.objects.count() == 8
    assert HostMetric.active_objects.count() == 4

    for i in range(2):
        HostMetricTask().cleanup(hard_threshold=threshold)
        assert HostMetric.objects.count() == 6

        hostnames = set(HostMetric.objects.order_by('hostname').values_list('hostname', flat=True))
        assert hostnames == {'host_1', 'host_2', 'host_3', 'host_4', 'host_5', 'host_7'}


def ago(months=0, hours=0):
    return timezone.now() - relativedelta(months=months, hours=hours)
