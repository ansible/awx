"""Failure scenarios about canceling, capacity and launches around orphaned jobs (write-up section 4).

Tests marked xfail reproduce a defect found on devel and assert the behavior it should
have. The others guard behavior devel already gets right.

Several devel bugs share one cause: when a lost controller's job is marked failed, its
playbook keeps running on the execution node. Whatever depends on the job being active
(launch blocking, relaunch, instance group limits, execution node capacity, workflow
branching) then sees a finished job. test_reaped_job_does_not_leave_its_playbook_running
covers each of those bugs with the job shape its scenario used.
"""

import pytest

from awx.main.models import InstanceGroup, Job, JobTemplate, WorkflowJob, WorkflowJobNode
from awx.main.tasks.system import adopt_job
from awx.main.tests.adoption_cluster import (
    EXEC,
    PEER,
    UNIT,
    adoption_env,
    assert_playbook_not_left_running,
    configure,
    make_cluster,
    mesh,
    run_lost_instance_handling,
)
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, make_events


@pytest.fixture(autouse=True)
def env(settings, tmp_path):
    configure(settings)
    with adoption_env(settings, tmp_path):
        yield


def peer_job(**fields):
    """A job controlled by ctrl-1 and running on receptor-1."""
    fields.setdefault('work_unit_id', UNIT)
    return Job.objects.create(controller_node=PEER, execution_node=EXEC, status='running', celery_task_id='peer-task', **fields)


def running_unit():
    return FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})


# ── Canceling an orphaned job ─────────────────────────────────────────────────


@pytest.mark.xfail(strict=True, reason='AAP-96830: canceling a job whose controller is down is dropped; the job never ends canceled')
@pytest.mark.django_db
def test_cancel_requested_while_orphaned_cancels_the_unit(me_inst):
    # 4.1 Cancel while orphaned. The user canceled while the controller was down, so the
    # cancel reached no one. Today adoption never reads cancel_flag: it waits for the unit
    # and finishes the job, successful, with cancel_flag set.
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, cancel_flag=True)
    work = running_unit()

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert ('cancel', UNIT) in work.calls
    assert job.status == 'canceled'


@pytest.mark.xfail(strict=True, reason='AAP-96835: canceling a job while it is finalized after a resume leaves it running forever')
@pytest.mark.django_db
def test_canceled_job_whose_unit_is_gone_is_finalized_canceled(me_inst):
    # 4.14 Cancel during the adopter's finalize. The cancel stopped the adoption after the
    # unit was released but before the status was saved. Today every later adoption finds
    # no unit and defers, so the job stays running forever.
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, cancel_flag=True)

    adopt_job(job.id, open_work=lambda: FakeReceptorWork())

    job.refresh_from_db()
    assert job.status == 'canceled'


@pytest.mark.xfail(strict=True, reason='AAP-96836: canceling many orphaned jobs marks them failed one by one instead of canceled')
@pytest.mark.django_db
def test_canceled_orphans_of_a_lost_controller_end_canceled():
    # 4.15 Canceling many orphans at once. Twenty jobs of a dead controller were canceled
    # while it was down. Today they are marked failed, "Job reaped due to instance shutdown".
    make_cluster()
    canceled = [peer_job(work_unit_id=f'unit-{n}', cancel_flag=True) for n in range(20)]

    run_lost_instance_handling(mesh(EXEC))

    statuses = {job.status for job in Job.objects.filter(pk__in=[j.pk for j in canceled])}
    assert statuses == {'canceled'}


@pytest.mark.xfail(strict=True, reason='AAP-96840: canceling a sliced job leaves the orphaned slice failed with its playbook running')
@pytest.mark.django_db
def test_canceled_slice_of_a_lost_controller_ends_canceled_and_stops():
    # 4.21 Canceling a sliced job. The parent was canceled, so the orphaned slice has
    # cancel_flag set. Today it ends failed and its playbook runs to the end.
    make_cluster()
    job = peer_job(job_slice_number=1, job_slice_count=2, cancel_flag=True)
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)

    job.refresh_from_db()
    assert job.status == 'canceled'
    assert ('cancel', UNIT) in work.calls


# ── A reaped job whose playbook keeps running ─────────────────────────────────


def job_of_template_without_simultaneous_runs():
    return peer_job(job_template=JobTemplate.objects.create(name='same-hosts', allow_simultaneous=False))


def job_in_workflow():
    workflow = WorkflowJob.objects.create(name='outer', status='running')
    job = peer_job()
    WorkflowJobNode.objects.create(workflow_job=workflow, job=job)
    return job


def job_in_limited_instance_group():
    return peer_job(instance_group=InstanceGroup.objects.create(name='limited', max_concurrent_jobs=2))


def xfail(bug):
    return pytest.mark.xfail(strict=True, reason=f'{bug}: a reaped job leaves its playbook running')


@pytest.mark.parametrize(
    'make_job',
    [
        pytest.param(job_of_template_without_simultaneous_runs, id='AAP-96832-same-hosts', marks=xfail('AAP-96832')),
        pytest.param(job_in_workflow, id='AAP-96833-nested-workflow', marks=xfail('AAP-96833')),
        pytest.param(job_of_template_without_simultaneous_runs, id='AAP-96834-relaunch', marks=xfail('AAP-96834')),
        pytest.param(job_in_limited_instance_group, id='AAP-96837-instance-group-limit', marks=xfail('AAP-96837')),
        pytest.param(peer_job, id='AAP-96841-execution-node-capacity', marks=xfail('AAP-96841')),
        pytest.param(job_in_workflow, id='AAP-96844-workflow-branch', marks=xfail('AAP-96844')),
        pytest.param(job_in_workflow, id='AAP-96845-set-stats-artifacts', marks=xfail('AAP-96845')),
    ],
)
@pytest.mark.django_db
def test_reaped_job_does_not_leave_its_playbook_running(make_job):
    # ctrl-1 is lost while its job runs on receptor-1, which is still up. Today the job is
    # marked failed and nothing cancels its work unit, so the playbook runs on unobserved:
    # the next launch overlaps it (4.6, 4.12), it stops counting toward instance group and
    # execution node limits (4.17, 4.23), and a workflow takes the failure branch for a
    # playbook that succeeds (4.11, 5.5, 5.6). Either the unit is canceled when the job is
    # marked failed, or the job stays active until the unit ends.
    make_cluster()
    job = make_job()
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)

    assert_playbook_not_left_running(job, work)


# ── Waiting jobs of a lost controller ─────────────────────────────────────────


@pytest.mark.django_db
def test_waiting_jobs_of_a_lost_controller_return_to_pending():
    # 4.5 Jobs waiting when the controller dies. They had not started, so they go back to
    # the task manager and run once, elsewhere.
    make_cluster()
    waiting = Job.objects.create(controller_node=PEER, execution_node=EXEC, status='waiting')

    run_lost_instance_handling(mesh(EXEC))

    waiting.refresh_from_db()
    assert waiting.status == 'pending'
    assert waiting.controller_node == ''
    assert waiting.execution_node == ''
