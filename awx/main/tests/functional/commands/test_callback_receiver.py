import pytest
import time
from unittest import mock
from uuid import uuid4

from django.test import TransactionTestCase

from awx.main.dispatch.worker.callback import job_stats_wrapup, CallbackBrokerWorker

from awx.main.models.jobs import Job
from awx.main.models.inventory import InventoryUpdate, InventorySource
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
        from django.db import IntegrityError as DjangoIntegrityError
        from django.utils.timezone import now as tz_now

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
