"""Adoption of orphaned jobs: adopt_job reattaches to the job's receptor work unit, replays its events
and finalizes it.

These tests drive the real reattach, streaming, dedup and finalize code. Only receptor
(FakeReceptorWork) and the callback-receiver queue (RecordingDispatcher) are replaced.

``TIMEOUT`` is HADR_JOB_ADOPTION_TIMEOUT.
"""

from unittest import mock

import pytest
from django.utils.timezone import now, timedelta

from awx.main.models import Job, JobEvent
from awx.main.tasks.receptor import reattach_to_work_unit
from awx.main.tasks.system import adopt_job, awx_receptor_workunit_reaper
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

TIMEOUT = 300
UNIT = 'unit-1'


@pytest.fixture(autouse=True)
def fake_receptor_env(settings, tmp_path):
    """connections.close_all() would end the test's transaction; events go to the recorder instead of
    Redis.

    The thread that processes a unit's results re-initializes the settings wrapper as a new
    process would. Under the settings fixture that wraps the override, and the nested wrapper
    marks registered settings read-only for the rest of the test process.
    """
    settings.AWX_ISOLATION_BASE_PATH = str(tmp_path)
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    RecordingDispatcher.reset()
    with (
        mock.patch('awx.main.tasks.receptor.connections'),
        mock.patch('awx.conf.settings.SettingsWrapper.initialize'),
        mock.patch('awx.main.tasks.callback.CallbackQueueDispatcher', RecordingDispatcher),
        mock.patch('awx.main.tasks.jobs.ScheduleTaskManager'),
        mock.patch('awx.main.tasks.jobs.ScheduleWorkflowManager'),
        mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status'),
    ):
        yield


@pytest.fixture
def job_with_unit(me_inst):
    return Job.objects.create(controller_node=me_inst.hostname, execution_node='receptor-1', status='running', work_unit_id=UNIT)


def save_events(job, counters):
    for counter in counters:
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)


@pytest.mark.django_db
def test_finished_unit_is_replayed_and_finalized(job_with_unit):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30))})

    assert reattach_to_work_unit(job_with_unit, work) is True

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(1, 31))
    assert UNIT not in work.units, 'work unit released after finalize'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'saved, unit_events, expected',
    [
        pytest.param(list(range(1, 21)), 30, list(range(21, 31)), id='saved-in-order'),
        pytest.param([*range(1, 11), 13], 20, [11, 12, *range(14, 21)], id='saved-out-of-order'),
    ],
)
def test_events_already_saved_are_not_dispatched_again(job_with_unit, saved, unit_events, expected):
    """``saved-out-of-order``: Parallel callback workers can commit counter 13 before 11 and 12."""
    save_events(job_with_unit, saved)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(unit_events))})

    reattach_to_work_unit(job_with_unit, work)

    assert RecordingDispatcher.counters() == expected


@pytest.mark.django_db
def test_failed_playbook_finalizes_failed(job_with_unit):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10, failed_tasks=[5]), status='failed', exit_code=2)})

    reattach_to_work_unit(job_with_unit, work)

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'failed'


@pytest.mark.django_db
def test_unit_still_running_is_deferred(job_with_unit):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    assert reattach_to_work_unit(job_with_unit, work) is False

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'running'
    assert RecordingDispatcher.dispatched == []
    assert UNIT in work.units


@pytest.mark.django_db
def test_unit_gone_is_deferred(job_with_unit):
    """The unit was released, or the node lost it, before adoption."""
    work = FakeReceptorWork()

    assert reattach_to_work_unit(job_with_unit, work) is False

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'running'


@pytest.mark.django_db
def test_stream_broken_mid_replay_fails_a_successful_unit(job_with_unit):
    """The unit succeeded, but the results stream ends after 12 of 30 events. Today the job is finalized
    failed, with only the events read before the break.
    """
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30), break_after=12)})

    reattach_to_work_unit(job_with_unit, work)

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'failed'
    assert RecordingDispatcher.counters() == list(range(1, 13))
    assert 'Unexpected empty line' in job_with_unit.job_explanation


@pytest.mark.django_db
def test_workunit_reaper_releases_units_of_finished_jobs(me_inst, settings):
    settings.RECEPTOR_RELEASE_WORK = True
    finished = Job.objects.create(controller_node=me_inst.hostname, status='successful', work_unit_id='done')
    running = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='live')
    work = FakeReceptorWork({'done': FakeWorkUnit(), 'live': FakeWorkUnit(state='Running')})

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl'),
        mock.patch('awx.main.tasks.system.ReceptorWork', return_value=work),
        mock.patch('awx.main.tasks.system.administrative_workunit_reaper'),
    ):
        awx_receptor_workunit_reaper()

    assert ('cancel', finished.work_unit_id) in work.calls
    assert finished.work_unit_id not in work.units
    assert running.work_unit_id in work.units


@pytest.fixture
def quiet_orphan(me_inst):
    """A running job whose last saved event was written at the returned time."""
    started = now() - timedelta(hours=1)
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, started=started)
    JobEvent.objects.create(job=job, counter=1, event='playbook_on_start', job_created=job.created)
    last_event = now() - timedelta(minutes=10)
    JobEvent.objects.filter(job=job).update(created=last_event)
    return job, last_event


@pytest.mark.django_db
def test_orphan_within_the_deadline_is_adopted(quiet_orphan):
    job, last_event = quiet_orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    clock = FakeClock(last_event + timedelta(seconds=TIMEOUT - 1))

    adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert job.finished == clock()
    assert RecordingDispatcher.counters() == list(range(2, 11))
    assert ('close',) in work.calls


@pytest.mark.django_db
def test_orphan_past_the_deadline_is_failed_without_contacting_receptor(quiet_orphan):
    job, last_event = quiet_orphan
    opened = mock.Mock()

    adopt_job(job.id, open_work=opened, clock=FakeClock(last_event + timedelta(seconds=TIMEOUT + 1)))

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'HADR_JOB_ADOPTION_TIMEOUT' in job.job_explanation
    opened.assert_not_called()
