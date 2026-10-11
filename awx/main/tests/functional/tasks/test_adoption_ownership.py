"""Who may write a job's final status once adoption claims it.

A claim records the adoption task's id in celery_task_id before the task is dispatched.
After that, a final status write from any other task is refused with NotOwner, so a
controller that only looked dead can't overwrite the adopted job when it comes back.
"""

from unittest import mock

import pytest

from awx.main.models import Job
from awx.main.tasks.callback import RunnerCallback
from awx.main.tasks.jobs import _finalize_job_run
from awx.main.tasks.system import _process_running_jobs, adopt_job, claim_for_adoption
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events
from awx.main.utils.update_model import NotOwner, update_model

UNIT = 'unit-1'
ORIGINAL = 'original-task'


@pytest.fixture(autouse=True)
def adoption_env(settings, tmp_path):
    settings.AWX_ISOLATION_BASE_PATH = str(tmp_path)
    RecordingDispatcher.reset()
    with (
        mock.patch('awx.main.tasks.receptor.connections'),
        mock.patch('awx.main.tasks.callback.CallbackQueueDispatcher', RecordingDispatcher),
        mock.patch('awx.main.tasks.jobs.ScheduleTaskManager'),
        mock.patch('awx.main.tasks.jobs.ScheduleWorkflowManager'),
        mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status'),
    ):
        yield


@pytest.fixture
def running_job(me_inst):
    return Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, celery_task_id=ORIGINAL)


def finalize_as(job, owner_task_id, status):
    callback = RunnerCallback(model=Job)
    callback.instance = job
    return _finalize_job_run(Job, job.pk, callback, status, owner_task_id=owner_task_id)


# ── update_model ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_owner_may_write(running_job):
    update_model(Job, running_job.pk, owner_task_id=ORIGINAL, job_explanation='mine')
    running_job.refresh_from_db()
    assert running_job.job_explanation == 'mine'


@pytest.mark.django_db
def test_former_owner_is_refused_and_nothing_is_written(running_job):
    Job.objects.filter(pk=running_job.pk).update(celery_task_id='adoption-task')

    with pytest.raises(NotOwner) as exc:
        update_model(Job, running_job.pk, owner_task_id=ORIGINAL, status='error')

    assert exc.value.current_task_id == 'adoption-task'
    running_job.refresh_from_db()
    assert running_job.status == 'running'


@pytest.mark.django_db
def test_write_without_an_owner_is_not_fenced(running_job):
    Job.objects.filter(pk=running_job.pk).update(celery_task_id='adoption-task')
    update_model(Job, running_job.pk, job_explanation='unfenced')
    running_job.refresh_from_db()
    assert running_job.job_explanation == 'unfenced'


# ── The claim ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_claim_records_a_new_task_id(running_job):
    task_id = claim_for_adoption(running_job)

    assert task_id and task_id != ORIGINAL
    running_job.refresh_from_db()
    assert running_job.celery_task_id == task_id


@pytest.mark.django_db
def test_only_one_of_two_claims_from_the_same_read_wins(running_job):
    # Two heartbeats read the job before either claims it.
    first_read = Job.objects.get(pk=running_job.pk)
    second_read = Job.objects.get(pk=running_job.pk)

    assert claim_for_adoption(first_read) is not None
    assert claim_for_adoption(second_read) is None


@pytest.mark.django_db
def test_heartbeat_claims_before_dispatching_under_the_claimed_id(running_job, me_inst):
    with mock.patch('awx.main.tasks.system.adopt_job_async') as task:
        _process_running_jobs(me_inst, ['some-other-task'], None)

    running_job.refresh_from_db()
    kwargs = task.apply_async.call_args.kwargs
    assert kwargs['uuid'] == running_job.celery_task_id
    assert kwargs['kwargs'] == {'owner_task_id': running_job.celery_task_id}


# ── Stale writers after a claim ───────────────────────────────────────────────


@pytest.mark.django_db
def test_returning_controller_cannot_overwrite_the_adopted_result(running_job):
    # The original controller looked dead, so this one claimed and adopted the job.
    task_id = claim_for_adoption(running_job)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    adopt_job(running_job.id, open_work=lambda: work, owner_task_id=task_id)
    running_job.refresh_from_db()
    assert running_job.status == 'successful'

    # The original controller comes back and tries to write its own final status.
    with pytest.raises(NotOwner):
        finalize_as(running_job, ORIGINAL, 'error')

    running_job.refresh_from_db()
    assert running_job.status == 'successful'


@pytest.mark.django_db
def test_original_owner_finishing_first_is_refused_while_adoption_proceeds(running_job):
    # The claim lands while the original task is still streaming. When it finishes,
    # its write is refused; the adoption then streams and finalizes.
    task_id = claim_for_adoption(running_job)

    with pytest.raises(NotOwner):
        finalize_as(running_job, ORIGINAL, 'successful')
    running_job.refresh_from_db()
    assert running_job.status == 'running'

    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    adopt_job(running_job.id, open_work=lambda: work, owner_task_id=task_id)
    running_job.refresh_from_db()
    assert running_job.status == 'successful'


@pytest.mark.django_db
def test_adoption_claimed_again_before_it_starts_does_nothing(running_job):
    stale = claim_for_adoption(running_job)
    claim_for_adoption(Job.objects.get(pk=running_job.pk))
    opened = mock.Mock()

    adopt_job(running_job.id, open_work=opened, owner_task_id=stale)

    opened.assert_not_called()
    running_job.refresh_from_db()
    assert running_job.status == 'running'


@pytest.mark.django_db
def test_adoption_that_loses_ownership_mid_stream_leaves_the_unit(running_job):
    stale = claim_for_adoption(running_job)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    def reclaim_then_open():
        # Another claim lands after this adoption started but before it finalizes.
        claim_for_adoption(Job.objects.get(pk=running_job.pk))
        return work

    adopt_job(running_job.id, open_work=reclaim_then_open, owner_task_id=stale)

    running_job.refresh_from_db()
    assert running_job.status == 'running', 'the new owner finalizes, not the stale adoption'
    assert UNIT in work.units, 'the stale adoption does not release the new owner\'s unit'
