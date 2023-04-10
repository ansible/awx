from unittest import mock
import pytest

from django.utils.timezone import now

from django.db.models import Q

from awx.main.models import Job, JobEvent, Inventory, Host, JobHostSummary, HostMetric


@pytest.mark.django_db
class TestEvents:
    def setup_method(self):
        self.hostnames = []
        self.host_map = dict()
        self.inventory = None
        self.job = None

    @mock.patch('awx.main.models.events.emit_event_detail')
    def test_parent_changed(self, emit):
        j = Job()
        j.save()
        JobEvent.create_from_data(job_id=j.pk, uuid='abc123', event='playbook_on_task_start').save()
        assert JobEvent.objects.count() == 1
        for e in JobEvent.objects.all():
            assert e.changed is False

        JobEvent.create_from_data(job_id=j.pk, parent_uuid='abc123', event='runner_on_ok', event_data={'res': {'changed': ['localhost']}}).save()
        # the `playbook_on_stats` event is where we update the parent changed linkage
        JobEvent.create_from_data(job_id=j.pk, parent_uuid='abc123', event='playbook_on_stats').save()
        events = JobEvent.objects.filter(event__in=['playbook_on_task_start', 'runner_on_ok'])
        assert events.count() == 2
        for e in events.all():
            assert e.changed is True

    @pytest.mark.parametrize('event', JobEvent.FAILED_EVENTS)
    @mock.patch('awx.main.models.events.emit_event_detail')
    def test_parent_failed(self, emit, event):
        j = Job()
        j.save()
        JobEvent.create_from_data(job_id=j.pk, uuid='abc123', event='playbook_on_task_start').save()
        assert JobEvent.objects.count() == 1
        for e in JobEvent.objects.all():
            assert e.failed is False

        JobEvent.create_from_data(job_id=j.pk, parent_uuid='abc123', event=event).save()

        # the `playbook_on_stats` event is where we update the parent failed linkage
        JobEvent.create_from_data(job_id=j.pk, parent_uuid='abc123', event='playbook_on_stats').save()
        events = JobEvent.objects.filter(event__in=['playbook_on_task_start', event])
        assert events.count() == 2
        for e in events.all():
            assert e.failed is True

    def test_host_summary_generation(self):
        self._generate_hosts(100)
        self._create_job_event(ok=dict((hostname, len(hostname)) for hostname in self.hostnames))

        assert self.job.job_host_summaries.count() == len(self.hostnames)
        assert sorted([s.host_name for s in self.job.job_host_summaries.all()]) == sorted(self.hostnames)

        for s in self.job.job_host_summaries.all():
            assert self.host_map[s.host_name] == s.host_id
            assert s.ok == len(s.host_name)
            assert s.changed == 0
            assert s.dark == 0
            assert s.failures == 0
            assert s.ignored == 0
            assert s.processed == 0
            assert s.rescued == 0
            assert s.skipped == 0

        for host in Host.objects.all():
            assert host.last_job_id == self.job.id
            assert host.last_job_host_summary.host == host

    def test_host_summary_generation_with_deleted_hosts(self):
        self._generate_hosts(10)

        # delete half of the hosts during the playbook run
        for h in self.inventory.hosts.all()[:5]:
            h.delete()

        self._create_job_event(ok=dict((hostname, len(hostname)) for hostname in self.hostnames))

        ids = sorted([s.host_id or -1 for s in self.job.job_host_summaries.order_by('id').all()])
        names = sorted([s.host_name for s in self.job.job_host_summaries.all()])
        assert ids == [-1, -1, -1, -1, -1, 6, 7, 8, 9, 10]
        assert names == ['Host 0', 'Host 1', 'Host 2', 'Host 3', 'Host 4', 'Host 5', 'Host 6', 'Host 7', 'Host 8', 'Host 9']

    def test_host_summary_generation_with_limit(self):
        # Make an inventory with 10 hosts, run a playbook with a --limit
        # pointed at *one* host,
        # Verify that *only* that host has an associated JobHostSummary and that
        # *only* that host has an updated value for .last_job.
        self._generate_hosts(10)

        # by making the playbook_on_stats *only* include Host 1, we're emulating
        # the behavior of a `--limit=Host 1`
        matching_host = Host.objects.get(name='Host 1')
        self._create_job_event(ok={matching_host.name: len(matching_host.name)})  # effectively, limit=Host 1

        # since the playbook_on_stats only references one host,
        # there should *only* be on JobHostSummary record (and it should
        # be related to the appropriate Host)
        assert JobHostSummary.objects.count() == 1
        for h in Host.objects.all():
            if h.name == 'Host 1':
                assert h.last_job_id == self.job.id
                assert h.last_job_host_summary_id == JobHostSummary.objects.first().id
            else:
                # all other hosts in the inventory should remain untouched
                assert h.last_job_id is None
                assert h.last_job_host_summary_id is None

    def test_host_metrics_insert(self):
        self._generate_hosts(10)

        self._create_job_event(
            ok=dict((hostname, len(hostname)) for hostname in self.hostnames[0:3]),
            failures=dict((hostname, len(hostname)) for hostname in self.hostnames[3:6]),
            processed=dict((hostname, len(hostname)) for hostname in self.hostnames[6:9]),
            skipped=dict((hostname, len(hostname)) for hostname in [self.hostnames[9]]),
        )

        metrics = HostMetric.objects.all()
        assert len(metrics) == 10
        for hm in metrics:
            assert hm.automated_counter == 1
            assert hm.last_automation is not None
            assert hm.deleted is False

    def test_host_metrics_update(self):
        self._generate_hosts(12)

        self._create_job_event(ok=dict((hostname, len(hostname)) for hostname in self.hostnames))

        # Soft delete 6 host metrics
        for hm in HostMetric.objects.filter(id__in=[1, 3, 5, 7, 9, 11]):
            hm.soft_delete()

        assert len(HostMetric.objects.filter(Q(deleted=False) & Q(deleted_counter=0) & Q(last_deleted__isnull=True))) == 6
        assert len(HostMetric.objects.filter(Q(deleted=True) & Q(deleted_counter=1) & Q(last_deleted__isnull=False))) == 6

        # hostnames in 'ignored' and 'rescued' stats are ignored
        self.job = Job(inventory=self.inventory)
        self.job.save()
        self._create_job_event(
            ignored=dict((hostname, len(hostname)) for hostname in self.hostnames[0:6]),
            rescued=dict((hostname, len(hostname)) for hostname in self.hostnames[6:11]),
        )

        assert len(HostMetric.objects.filter(Q(deleted=False) & Q(deleted_counter=0) & Q(last_deleted__isnull=True))) == 6
        assert len(HostMetric.objects.filter(Q(deleted=True) & Q(deleted_counter=1) & Q(last_deleted__isnull=False))) == 6

        # hostnames in 'changed', 'dark', 'failures', 'ok', 'processed', 'skipped' are processed
        self.job = Job(inventory=self.inventory)
        self.job.save()
        self._create_job_event(
            changed=dict((hostname, len(hostname)) for hostname in self.hostnames[0:2]),
            dark=dict((hostname, len(hostname)) for hostname in self.hostnames[2:4]),
            failures=dict((hostname, len(hostname)) for hostname in self.hostnames[4:6]),
            ok=dict((hostname, len(hostname)) for hostname in self.hostnames[6:8]),
            processed=dict((hostname, len(hostname)) for hostname in self.hostnames[8:10]),
            skipped=dict((hostname, len(hostname)) for hostname in self.hostnames[10:12]),
        )
        assert len(HostMetric.objects.filter(Q(deleted=False) & Q(deleted_counter=0) & Q(last_deleted__isnull=True))) == 6
        assert len(HostMetric.objects.filter(Q(deleted=False) & Q(deleted_counter=1) & Q(last_deleted__isnull=False))) == 6

    def _generate_hosts(self, cnt, id_from=0):
        self.hostnames = [f'Host {i}' for i in range(id_from, id_from + cnt)]
        self.inventory = Inventory()
        self.inventory.save()
        Host.objects.bulk_create([Host(created=now(), modified=now(), name=h, inventory_id=self.inventory.id) for h in self.hostnames])
        self.job = Job(inventory=self.inventory)
        self.job.save()

        # host map is a data structure that tracks a mapping of host name --> ID
        # for the inventory, _regardless_ of whether or not there's a limit
        # applied to the actual playbook run
        self.host_map = dict((host.name, host.id) for host in self.inventory.hosts.all())

    def _create_job_event(
        self,
        parent_uuid='abc123',
        event='playbook_on_stats',
        ok=None,
        changed=None,
        dark=None,
        failures=None,
        ignored=None,
        processed=None,
        rescued=None,
        skipped=None,
    ):
        JobEvent.create_from_data(
            job_id=self.job.pk,
            parent_uuid=parent_uuid,
            event=event,
            event_data={
                'ok': ok or {},
                'changed': changed or {},
                'dark': dark or {},
                'failures': failures or {},
                'ignored': ignored or {},
                'processed': processed or {},
                'rescued': rescued or {},
                'skipped': skipped or {},
            },
            host_map=self.host_map,
        ).save()
