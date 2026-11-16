import pytest
import time
from types import SimpleNamespace
from unittest import mock
from uuid import uuid4

import redis

from django.db import connection, DatabaseError, IntegrityError as DjangoIntegrityError
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now as tz_now

from awx.main.dispatch.worker.callback import job_stats_wrapup, CallbackBrokerWorker, _null_missing_host_ids

from awx.main.models import Organization
from awx.main.models.jobs import Job
from awx.main.models.inventory import Host, Inventory, InventoryUpdate, InventorySource
from awx.main.models.events import InventoryUpdateEvent, JobEvent


@pytest.mark.django_db
def test_wrapup_does_not_send_notifications(mocker):
    job = Job.objects.create(status='running')
    assert job.host_status_counts is None
    mock = mocker.patch('awx.main.models.notifications.JobNotificationMixin.send_notification_templates')
    job_stats_wrapup(job.id)
    job.refresh_from_db()
    assert job.host_status_counts == {}
    mock.assert_not_called()


@pytest.mark.django_db
def test_wrapup_does_send_notifications(mocker):
    job = Job.objects.create(status='successful')
    assert job.host_status_counts is None
    mock = mocker.patch('awx.main.models.notifications.JobNotificationMixin.send_notification_templates')
    job_stats_wrapup(job.id)
    job.refresh_from_db()
    assert job.host_status_counts == {}
    mock.assert_called_once_with('succeeded')


@pytest.mark.django_db
def test_wrapup_skips_notifications_if_already_processed(mocker):
    """Fix 2 (AAP-96718): if host_status_counts is already set, another controller already ran
    stats_wrapup. The second call must not fire a duplicate notification."""
    job = Job.objects.create(status='successful', host_status_counts={'ok': 3})
    notification_mock = mocker.patch('awx.main.models.notifications.JobNotificationMixin.send_notification_templates')
    job_stats_wrapup(job.id)
    notification_mock.assert_not_called()


@pytest.mark.django_db
def test_read_survives_a_redis_connection_error():
    # 5.17 Redis restart across the cluster. A worker mid-blpop when Redis restarts must not
    # crash: it logs, backs off, and returns FLUSH so the dispatcher's main loop keeps running
    # and retries on the next read instead of losing the whole callback receiver.
    worker = CallbackBrokerWorker.__new__(CallbackBrokerWorker)
    worker.queue_name = 'callback_tasks'
    worker.redis = mock.Mock()
    worker.redis.blpop.side_effect = redis.exceptions.ConnectionError('Connection refused')

    with mock.patch('time.sleep'), mock.patch.object(CallbackBrokerWorker, 'record_statistics') as record_stats:
        assert worker.read() == {'event': 'FLUSH'}

    record_stats.assert_not_called()  # has_redis_error skips the statistics path


class TestCallbackBrokerWorker(TransactionTestCase):
    @pytest.fixture(autouse=True)
    def turn_off_websockets_and_redis(self, fake_redis):
        with mock.patch('awx.main.dispatch.worker.callback.emit_event_detail', lambda *a, **kw: None):
            yield

    def event_create_kwargs(self):
        inventory_update = InventoryUpdate.objects.create(source='file', inventory_source=InventorySource.objects.create(source='file'))
        return dict(inventory_update=inventory_update, created=inventory_update.created)

    def test_flush_with_valid_event(self):
        worker = CallbackBrokerWorker()
        events = [InventoryUpdateEvent(uuid=str(uuid4()), **self.event_create_kwargs())]
        worker.buff = {InventoryUpdateEvent: events}
        worker.flush(force=True)
        assert worker.buff.get(InventoryUpdateEvent, []) == []
        assert InventoryUpdateEvent.objects.filter(uuid=events[0].uuid).count() == 1

    def test_flush_nulls_host_id_of_deleted_host(self):
        """The event host FK has no DB constraint, so a host deleted mid-job would leave a dangling id."""
        inventory = Inventory.objects.create(name='inv', organization=Organization.objects.create(name='org'))
        live_host = Host.objects.create(name='live', inventory=inventory)
        gone_host = Host.objects.create(name='gone', inventory=inventory)
        gone_id = gone_host.id
        gone_host.delete()
        job = Job.objects.create(status='running')

        worker = CallbackBrokerWorker()
        events = [
            JobEvent(job=job, counter=1, job_created=job.created, uuid=str(uuid4()), created=job.created, host_id=live_host.id, host_name='live'),
            JobEvent(job=job, counter=2, job_created=job.created, uuid=str(uuid4()), created=job.created, host_id=gone_id, host_name='gone'),
        ]
        worker.buff = {JobEvent: events.copy()}
        worker.flush(force=True)

        live_event = JobEvent.objects.get(uuid=events[0].uuid)
        gone_event = JobEvent.objects.get(uuid=events[1].uuid)
        assert (live_event.host_id, live_event.host_name) == (live_host.id, 'live')
        assert (gone_event.host_id, gone_event.host_name) == (None, 'gone')

    def test_host_check_error_does_not_lose_the_events(self):
        """The host check is optional: if it fails, the events are saved rather than dropped."""
        job = Job.objects.create(status='running')
        worker = CallbackBrokerWorker()
        events = [JobEvent(job=job, counter=1, job_created=job.created, uuid=str(uuid4()), created=job.created, host_id=1, host_name='h')]
        worker.buff = {JobEvent: events}
        with mock.patch.object(Host.objects, 'filter', side_effect=DatabaseError('statement timeout')):
            worker.flush(force=True)
        assert worker.buff == {JobEvent: []}
        assert JobEvent.objects.filter(uuid=events[0].uuid).count() == 1

    def test_null_missing_host_ids_ignores_ids_that_are_not_integers(self):
        events = [
            SimpleNamespace(host_id=''),
            SimpleNamespace(host_id=None),
            SimpleNamespace(host_id='abc'),
            SimpleNamespace(host_id=987654),
            SimpleNamespace(),
        ]
        _null_missing_host_ids(events)
        assert [getattr(e, 'host_id', 'unset') for e in events] == ['', None, 'abc', None, 'unset']

    def test_flush_without_host_ids_runs_no_host_query(self):
        worker = CallbackBrokerWorker()
        worker.buff = {InventoryUpdateEvent: [InventoryUpdateEvent(uuid=str(uuid4()), **self.event_create_kwargs())]}
        with CaptureQueriesContext(connection) as queries:
            worker.flush(force=True)
        assert not [q['sql'] for q in queries if 'main_host' in q['sql']]

    def test_flush_with_invalid_event(self):
        worker = CallbackBrokerWorker()
        kwargs = self.event_create_kwargs()
        events = [
            InventoryUpdateEvent(uuid=str(uuid4()), stdout='good1', **kwargs),
            InventoryUpdateEvent(uuid=str(uuid4()), stdout='bad', counter=-2, **kwargs),
            InventoryUpdateEvent(uuid=str(uuid4()), stdout='good2', **kwargs),
        ]
        worker.buff = {InventoryUpdateEvent: events.copy()}
        worker.flush(force=True)
        assert InventoryUpdateEvent.objects.filter(uuid=events[0].uuid).count() == 1
        assert InventoryUpdateEvent.objects.filter(uuid=events[1].uuid).count() == 0
        assert InventoryUpdateEvent.objects.filter(uuid=events[2].uuid).count() == 1
        assert worker.buff == {InventoryUpdateEvent: [events[1]]}

    def test_duplicate_key_not_saved_twice(self):
        worker = CallbackBrokerWorker()
        events = [InventoryUpdateEvent(uuid=str(uuid4()), **self.event_create_kwargs())]
        worker.buff = {InventoryUpdateEvent: events.copy()}
        worker.flush(force=True)

        # put current saved event in buffer (error case)
        worker.buff = {InventoryUpdateEvent: [InventoryUpdateEvent.objects.get(uuid=events[0].uuid)]}
        worker.last_flush = time.time() - 2.0
        # here, the bulk_create will fail with UNIQUE constraint violation, but individual saves should resolve it
        worker.flush()
        assert InventoryUpdateEvent.objects.filter(uuid=events[0].uuid).count() == 1
        assert worker.buff.get(InventoryUpdateEvent, []) == []

    def test_give_up_on_bad_event(self):
        worker = CallbackBrokerWorker()
        events = [InventoryUpdateEvent(uuid=str(uuid4()), counter=-2, **self.event_create_kwargs())]
        worker.buff = {InventoryUpdateEvent: events.copy()}

        for i in range(5):
            worker.last_flush = time.time() - 2.0
            worker.flush()

        # Could not save, should be logged, and buffer should be cleared
        assert worker.buff.get(InventoryUpdateEvent, []) == []
        assert InventoryUpdateEvent.objects.filter(uuid=events[0].uuid).count() == 0  # sanity

    def test_flush_ignores_duplicate_job_counter(self):
        """Fix (AAP-96718): when two controllers stream the same receptor work unit, bulk_create
        raises IntegrityError on the (job_id, counter, job_created) unique constraint. The worker
        must silently discard the duplicate in the individual-save fallback, not keep it in the
        buffer for retry."""
        job = Job.objects.create(status='running')
        created_ts = tz_now()

        worker = CallbackBrokerWorker()
        duplicate = JobEvent(job=job, counter=1, job_created=created_ts, uuid=str(uuid4()), created=created_ts)
        worker.buff = {JobEvent: [duplicate]}

        # Simulate the unique constraint firing on bulk_create and on individual save.
        unique_error = DjangoIntegrityError('UNIQUE constraint failed: main_jobevent.job_id, main_jobevent.counter, main_jobevent.job_created')
        with mock.patch.object(JobEvent.objects, 'bulk_create', side_effect=unique_error):
            with mock.patch.object(duplicate, 'save', side_effect=unique_error):
                worker.flush(force=True)

        assert worker.buff.get(JobEvent, []) == [], "duplicate event must not remain in buffer"

    def test_flush_finishes_the_stats_wrapup_of_a_replayed_stats_event(self):
        """A receiver that died after storing the stats event but before the wrapup never ran
        it, so the replay hits the unique constraint and must complete the wrapup."""
        job = Job.objects.create(status='running')
        created_ts = tz_now()

        worker = CallbackBrokerWorker()
        duplicate = JobEvent(job=job, counter=1, job_created=created_ts, uuid=str(uuid4()), created=created_ts)
        duplicate._notification_trigger_event = True
        worker.buff = {JobEvent: [duplicate]}

        unique_error = DjangoIntegrityError('UNIQUE constraint failed: main_jobevent.job_id, main_jobevent.counter, main_jobevent.job_created')
        with mock.patch.object(JobEvent.objects, 'bulk_create', side_effect=unique_error):
            with mock.patch.object(duplicate, 'save', side_effect=unique_error):
                with mock.patch('awx.main.dispatch.worker.callback.job_stats_wrapup') as wrapup:
                    worker.flush(force=True)

        wrapup.assert_called_once_with(job.id, event=duplicate)
        assert worker.buff.get(JobEvent, []) == []

    def test_flush_with_empty_buffer(self):
        worker = CallbackBrokerWorker()
        worker.buff = {InventoryUpdateEvent: []}
        with mock.patch.object(InventoryUpdateEvent.objects, 'bulk_create') as flush_mock:
            worker.flush()
        flush_mock.assert_not_called()

    def test_postgres_invalid_NUL_char(self):
        # In postgres, text fields reject NUL character, 0x00
        # tests use sqlite3 which will not raise an error
        # but we can still test that it is sanitized before saving
        worker = CallbackBrokerWorker()
        kwargs = self.event_create_kwargs()
        events = [InventoryUpdateEvent(uuid=str(uuid4()), stdout="\x00", **kwargs)]
        assert "\x00" in events[0].stdout  # sanity
        worker.buff = {InventoryUpdateEvent: events.copy()}

        with mock.patch.object(InventoryUpdateEvent.objects, 'bulk_create', side_effect=ValueError):
            with mock.patch.object(events[0], 'save', side_effect=ValueError):
                worker.flush(force=True)

            assert "\x00" not in events[0].stdout

            worker.last_flush = time.time() - 2.0
            worker.flush()

            event = InventoryUpdateEvent.objects.get(uuid=events[0].uuid)
            assert "\x00" not in event.stdout
