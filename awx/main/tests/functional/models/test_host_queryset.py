import pytest

from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils.timezone import now

from awx.main.models import Job, JobEvent, Inventory, Host, JobHostSummary


@pytest.mark.django_db
class TestHostLatestSummaryQuerySet:
    """Tests for HostLatestSummaryQuerySet and Host.latest_summary property."""

    def _create_inventory_with_hosts(self, count=5):
        inventory = Inventory()
        inventory.save()
        Host.objects.bulk_create([Host(created=now(), modified=now(), name=f'host-{i}', inventory_id=inventory.id) for i in range(count)])
        return inventory

    def _run_job(self, inventory, host_names=None):
        """Run a fake job that creates JobHostSummary records for the given hosts."""
        if host_names is None:
            host_names = list(inventory.hosts.values_list('name', flat=True))
        job = Job(inventory=inventory)
        job.save()
        host_map = dict(inventory.hosts.values_list('name', 'id'))
        JobEvent.create_from_data(
            job_id=job.pk,
            parent_uuid='abc123',
            event='playbook_on_stats',
            event_data={
                'ok': {name: 1 for name in host_names},
                'changed': {},
                'dark': {},
                'failures': {},
                'ignored': {},
                'processed': {},
                'rescued': {},
                'skipped': {},
            },
            host_map=host_map,
        ).save()
        return job

    def test_with_latest_summary_id_annotates_hosts(self):
        inventory = self._create_inventory_with_hosts(3)
        job = self._run_job(inventory)

        hosts = Host.objects.filter(inventory=inventory).with_latest_summary_id()
        for host in hosts:
            assert hasattr(host, '_latest_summary_id')
            summary = JobHostSummary.objects.filter(host=host, job=job).first()
            assert host._latest_summary_id == summary.id

    def test_with_latest_summary_id_returns_most_recent(self):
        inventory = self._create_inventory_with_hosts(1)
        self._run_job(inventory)
        job2 = self._run_job(inventory)

        host = Host.objects.filter(inventory=inventory).with_latest_summary_id().first()
        latest = JobHostSummary.objects.filter(host_id=host.id).order_by('-id').first()
        assert latest.job_id == job2.id
        assert host._latest_summary_id == latest.id

    def test_with_latest_summary_id_none_for_no_summaries(self):
        inventory = self._create_inventory_with_hosts(1)
        # No job run — no summaries
        host = Host.objects.filter(inventory=inventory).with_latest_summary_id().first()
        assert host._latest_summary_id is None

    def test_fetch_all_bulk_attaches_summaries(self):
        inventory = self._create_inventory_with_hosts(5)
        self._run_job(inventory)

        hosts = list(Host.objects.filter(inventory=inventory).with_latest_summary_id())
        for host in hosts:
            assert hasattr(host, '_latest_summary_cache')
            assert host._latest_summary_cache is not None
            assert isinstance(host._latest_summary_cache, JobHostSummary)

    def test_fetch_all_skips_non_annotated_querysets(self):
        """Non-annotated querysets should NOT set _latest_summary_cache,
        preserving the per-object fallback in Host.latest_summary."""
        inventory = self._create_inventory_with_hosts(3)
        self._run_job(inventory)

        hosts = list(Host.objects.filter(inventory=inventory))
        for host in hosts:
            assert not hasattr(host, '_latest_summary_cache')

    def test_count_does_not_trigger_fetch_all(self):
        """Calling .count() should not trigger _fetch_all or the bulk-attach logic."""
        inventory = self._create_inventory_with_hosts(5)
        self._run_job(inventory)

        qs = Host.objects.filter(inventory=inventory).with_latest_summary_id()
        with CaptureQueriesContext(connection) as ctx:
            result = qs.count()

        assert result == 5
        # count() should produce a single COUNT query, not fetch all rows + summaries
        assert len(ctx.captured_queries) == 1
        assert 'COUNT' in ctx.captured_queries[0]['sql'].upper()

    def test_exists_does_not_trigger_fetch_all(self):
        inventory = self._create_inventory_with_hosts(1)
        self._run_job(inventory)

        qs = Host.objects.filter(inventory=inventory).with_latest_summary_id()
        with CaptureQueriesContext(connection) as ctx:
            result = qs.exists()

        assert result is True
        assert len(ctx.captured_queries) == 1

    def test_latest_summary_property_uses_cache(self):
        """When loaded via with_latest_summary_id(), Host.latest_summary
        should use the bulk-attached cache without extra queries."""
        inventory = self._create_inventory_with_hosts(3)
        self._run_job(inventory)

        hosts = list(Host.objects.filter(inventory=inventory).with_latest_summary_id())

        with CaptureQueriesContext(connection) as ctx:
            for host in hosts:
                summary = host.latest_summary
                assert summary is not None

        # No additional queries — all data came from the bulk-attach
        assert len(ctx.captured_queries) == 0

    def test_latest_summary_property_fallback(self):
        """When loaded without annotation, Host.latest_summary should
        fall back to a per-object query."""
        inventory = self._create_inventory_with_hosts(1)
        job = self._run_job(inventory)

        host = Host.objects.filter(inventory=inventory).first()
        assert not hasattr(host, '_latest_summary_cache')

        summary = host.latest_summary
        assert summary is not None
        assert summary.job_id == job.id
        # After first access, the cache should be populated
        assert hasattr(host, '_latest_summary_cache')

    def test_latest_summary_none_when_no_summaries(self):
        inventory = self._create_inventory_with_hosts(1)
        host = Host.objects.filter(inventory=inventory).with_latest_summary_id().first()
        assert host.latest_summary is None

    def test_latest_job_property(self):
        inventory = self._create_inventory_with_hosts(1)
        job = self._run_job(inventory)

        host = Host.objects.filter(inventory=inventory).with_latest_summary_id().first()
        assert host.latest_job is not None
        assert host.latest_job.id == job.id

    def test_latest_job_none_when_no_summaries(self):
        inventory = self._create_inventory_with_hosts(1)
        host = Host.objects.filter(inventory=inventory).first()
        assert host.latest_job is None

    def test_bulk_attach_select_related(self):
        """The bulk-attach should select_related job and job__job_template
        so accessing them doesn't cause extra queries."""
        inventory = self._create_inventory_with_hosts(3)
        self._run_job(inventory)

        hosts = list(Host.objects.filter(inventory=inventory).with_latest_summary_id())

        with CaptureQueriesContext(connection) as ctx:
            for host in hosts:
                summary = host.latest_summary
                _ = summary.job  # should not query

        assert len(ctx.captured_queries) == 0

    def test_chaining_preserves_annotation(self):
        """Chaining .filter() after .with_latest_summary_id() should
        preserve the annotation and bulk-attach behavior."""
        inventory = self._create_inventory_with_hosts(5)
        self._run_job(inventory)

        hosts = list(Host.objects.filter(inventory=inventory).with_latest_summary_id().filter(name__startswith='host-').order_by('name'))
        assert len(hosts) == 5
        for host in hosts:
            assert hasattr(host, '_latest_summary_cache')
            assert host._latest_summary_cache is not None

    def test_multiple_jobs_latest_wins(self):
        """After multiple jobs, latest_summary should return the most recent."""
        inventory = self._create_inventory_with_hosts(1)
        self._run_job(inventory)
        self._run_job(inventory)
        job3 = self._run_job(inventory)

        host = Host.objects.filter(inventory=inventory).with_latest_summary_id().first()
        assert host.latest_summary.job_id == job3.id

    def test_partial_host_coverage(self):
        """When a job only touches some hosts, only those hosts get summaries."""
        inventory = self._create_inventory_with_hosts(5)
        self._run_job(inventory, host_names=['host-0', 'host-1'])

        hosts = list(Host.objects.filter(inventory=inventory).with_latest_summary_id().order_by('name'))
        with_summary = [h for h in hosts if h.latest_summary is not None]
        without_summary = [h for h in hosts if h.latest_summary is None]

        assert len(with_summary) == 2
        assert len(without_summary) == 3
        assert sorted([h.name for h in with_summary]) == ['host-0', 'host-1']
