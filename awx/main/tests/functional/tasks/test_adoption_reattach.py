"""reattach_to_work_unit, run for real against FakeReceptorWork.

These replace #16669 unit tests that mocked the job, receptorctl, the finalize, the dedup,
the release and the private data dir around reattach_to_work_unit. Here a real job is
streamed from a fake unit: the outcome, the events sent to the callback receiver, and the
operations performed on the unit are checked as they happen.

The process phase is patched only where the fake cannot produce the condition itself: a
shutdown detach, which comes from a signal.
"""

from unittest import mock

import pytest

from awx.main.models import Job
from awx.main.tasks.receptor import AWXReceptorJob, reattach_to_work_unit
from awx.main.tests.adoption_cluster import adoption_env
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

UNIT = 'unit-1'


@pytest.fixture(autouse=True)
def env(settings, tmp_path):
    with adoption_env(settings, tmp_path):
        yield


@pytest.fixture
def job(me_inst):
    return Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT)


# ── Detach and cancel ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_detach_on_shutdown_leaves_the_job_running_and_the_unit_alive(job):
    # This controller is shutting down; the next one to come up adopts the job.
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    def detached(receptor_job, _work):
        receptor_job.detached = True
        return None

    with mock.patch.object(AWXReceptorJob, '_process_phase', detached):
        assert reattach_to_work_unit(job, work) is False

    job.refresh_from_db()
    assert job.status == 'running'
    assert UNIT in work.units, 'a detached adoption releases nothing'


@pytest.mark.django_db
def test_unit_canceled_by_its_user_finalizes_canceled(job):
    # A canceled run is a nonzero exit, but it is not a failure.
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), status='canceled')})

    assert reattach_to_work_unit(job, work) is True

    job.refresh_from_db()
    assert job.status == 'canceled'


@pytest.mark.django_db
def test_a_unit_that_refuses_the_cancel_still_ends_the_job(me_inst):
    # The user asked for the job to stop; receptor refusing the command must not hide that.
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, cancel_flag=True)

    class CancelRefused(FakeReceptorWork):
        def cancel(self, unit_id):
            self.calls.append(('cancel', unit_id))
            raise RuntimeError('receptor said no')

    assert reattach_to_work_unit(job, CancelRefused({UNIT: FakeWorkUnit(make_events(10), state='Running')})) is True

    job.refresh_from_db()
    assert job.status == 'canceled'


# ── Events carry the job's identity ───────────────────────────────────────────


@pytest.mark.django_db
def test_streamed_events_carry_the_jobs_created_time(job):
    # The event tables are partitioned on job_created, so every event has to carry it.
    reattach_to_work_unit(job, FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5))}))

    events = [e for e in RecordingDispatcher.dispatched if 'counter' in e]
    assert events and all(e['job_created'] == str(job.created) for e in events)
    assert not any('workflow_job_id' in e for e in events), 'a job outside a workflow names no workflow'


@pytest.mark.django_db
def test_streamed_events_of_a_workflow_child_name_its_workflow(job):
    with (
        mock.patch.object(Job, 'spawned_by_workflow', new_callable=mock.PropertyMock, return_value=True),
        mock.patch.object(Job, 'get_workflow_job', return_value=mock.Mock(id=999)),
    ):
        reattach_to_work_unit(job, FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5))}))

    events = [e for e in RecordingDispatcher.dispatched if 'counter' in e]
    assert events and all(e['workflow_job_id'] == 999 for e in events)


@pytest.mark.django_db
def test_a_failed_workflow_lookup_does_not_stop_the_adoption(job):
    with (
        mock.patch.object(Job, 'spawned_by_workflow', new_callable=mock.PropertyMock, return_value=True),
        mock.patch.object(Job, 'get_workflow_job', side_effect=Exception('workflow lookup failed')),
    ):
        assert reattach_to_work_unit(job, FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5))})) is True

    job.refresh_from_db()
    assert job.status == 'successful'


# ── The unit status given and the status read ─────────────────────────────────


@pytest.mark.django_db
def test_status_handed_in_by_the_caller_is_not_read_again(job):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5))})

    reattach_to_work_unit(job, work, unit_status={'StateName': 'Succeeded'})

    assert ('status', UNIT) not in work.calls


@pytest.mark.django_db
def test_unit_the_execution_node_cannot_hand_over_is_left_alone(job):
    # Unknown to this controller's receptor, and the execution node is unreachable as well.
    Job.objects.filter(pk=job.pk).update(execution_node='receptor-1')
    job.refresh_from_db()
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5), remote_only=True, status_error=RuntimeError('EE unreachable'))})

    assert reattach_to_work_unit(job, work) is False

    job.refresh_from_db()
    assert job.status == 'running'


# ── When streaming fails, the unit's status decides ──────────────────────────


@pytest.mark.django_db
def test_unit_is_released_after_finalizing_from_its_status(job):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5), results_error=ConnectionError('network timeout'))})

    assert reattach_to_work_unit(job, work) is True

    job.refresh_from_db()
    assert job.status == 'successful'
    assert UNIT not in work.units


@pytest.mark.django_db
def test_stream_failure_while_the_unit_still_runs_defers(job):
    # A transient stream error must not finalize a job whose playbook is still going.
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(5), state='Running', results_error=ConnectionError('network timeout'))})

    assert reattach_to_work_unit(job, work) is False

    job.refresh_from_db()
    assert job.status == 'running'
    assert UNIT in work.units


@pytest.mark.django_db
@pytest.mark.parametrize('first_state', ['', 'Running'], ids=['state-unknown', 'running'])
def test_stream_failure_with_no_readable_status_defers(job, first_state):
    # Neither the stream nor the status can be read after it: there is no truthful result yet.
    unit = FakeWorkUnit(make_events(5), results_error=ConnectionError('network timeout'), status_error=ConnectionError('receptor unreachable'))
    work = FakeReceptorWork({UNIT: unit})

    assert reattach_to_work_unit(job, work, unit_status={'StateName': first_state}) is False

    job.refresh_from_db()
    assert job.status == 'running'
    assert UNIT in work.units
