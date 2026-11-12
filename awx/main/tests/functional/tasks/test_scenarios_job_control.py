"""Failure scenarios about canceling, capacity and launches around orphaned jobs (write-up section 4).

Tests marked xfail reproduce a defect found on devel and assert the behavior it should
have. The others guard behavior devel already gets right.

Several devel bugs share one cause: when a lost controller's job is marked failed, its
playbook keeps running on the execution node. Whatever depends on the job being active
(launch blocking, relaunch, instance group limits, execution node capacity, workflow
branching) then sees a finished job. test_lost_controllers_job_does_not_leave_its_playbook_running
covers each of those bugs with the job shape its scenario used; adoption fixes them by
keeping the job active.
"""

import pytest

from awx.main.models import Instance, InstanceGroup, Job, JobTemplate, WorkflowJob, WorkflowJobNode
from awx.main.tasks.system import adopt_job
from awx.main.tests.adoption_cluster import (
    EXEC,
    PEER,
    THIS,
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


def adopt_claimed(jobs, work):
    """Run the adoptions lost-instance handling queued for ctrl-0, as its dispatcher would."""
    for job in Job.objects.filter(pk__in=[j.pk for j in jobs], controller_node=THIS):
        adopt_job(job.id, open_work=lambda: work, owner_task_id=job.celery_task_id)


# ── Canceling an orphaned job ─────────────────────────────────────────────────


@pytest.mark.django_db
def test_cancel_requested_while_orphaned_cancels_the_unit(me_inst):
    # 4.1 Cancel while orphaned (AAP-96830). The user canceled while the controller was
    # down, so the cancel reached no one. Adoption reads cancel_flag, cancels the unit and
    # ends the job canceled.
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


@pytest.mark.django_db
def test_canceled_orphans_of_a_lost_controller_end_canceled():
    # 4.15 Canceling many orphans at once (AAP-96836). Twenty jobs of a dead controller were canceled
    # while it was down. On devel they are marked failed, "Job reaped due to instance
    # shutdown". A controller that adopts them carries out the cancel when it adopts.
    make_cluster()
    canceled = [peer_job(work_unit_id=f'unit-{n}', cancel_flag=True) for n in range(20)]
    work = FakeReceptorWork({job.work_unit_id: FakeWorkUnit(make_events(10), state='Running') for job in canceled})

    run_lost_instance_handling(mesh(EXEC))
    adopt_claimed(canceled, work)

    statuses = {job.status for job in Job.objects.filter(pk__in=[j.pk for j in canceled])}
    assert statuses == {'canceled'}


@pytest.mark.django_db
def test_canceled_slice_of_a_lost_controller_ends_canceled_and_stops():
    # 4.21 Canceling a sliced job (AAP-96840). The parent was canceled, so the orphaned
    # slice has cancel_flag set. On devel it ends failed and its playbook runs to the end;
    # the controller that adopts it cancels the unit and ends it canceled.
    make_cluster()
    job = peer_job(job_slice_number=1, job_slice_count=2, cancel_flag=True)
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)
    adopt_claimed([job], work)

    job.refresh_from_db()
    assert job.status == 'canceled'
    assert ('cancel', UNIT) in work.calls


@pytest.mark.django_db
def test_canceled_workflow_cancels_its_orphaned_node():
    # 4.13 Canceling a workflow with an orphaned node. The workflow was canceled while
    # ctrl-1, which controls one of its node jobs, was down; the cancel set the node job's
    # cancel_flag but its signal reached no one. On devel the job is marked failed and its
    # playbook runs on. The controller that adopts it cancels the unit and ends it canceled.
    make_cluster()
    workflow = WorkflowJob.objects.create(name='outer', status='running', cancel_flag=True)
    job = peer_job(cancel_flag=True)
    WorkflowJobNode.objects.create(workflow_job=workflow, job=job)
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)
    adopt_claimed([job], work)

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


@pytest.mark.parametrize(
    'make_job',
    [
        pytest.param(job_of_template_without_simultaneous_runs, id='AAP-96832-same-hosts'),
        pytest.param(job_in_workflow, id='AAP-96833-nested-workflow'),
        pytest.param(job_of_template_without_simultaneous_runs, id='AAP-96834-relaunch'),
        pytest.param(job_in_limited_instance_group, id='AAP-96837-instance-group-limit'),
        pytest.param(peer_job, id='AAP-96841-execution-node-capacity'),
        pytest.param(job_in_workflow, id='AAP-96844-workflow-branch'),
        pytest.param(job_in_workflow, id='AAP-96845-set-stats-artifacts'),
    ],
)
@pytest.mark.django_db
def test_lost_controllers_job_does_not_leave_its_playbook_running(make_job):
    # ctrl-1 is lost while its job runs on receptor-1, which is still up. On devel the job
    # is marked failed and nothing cancels its work unit, so the playbook runs on
    # unobserved: the next launch overlaps it (4.6, 4.12), it stops counting toward
    # instance group and execution node limits (4.17, 4.23), and a workflow takes the
    # failure branch for a playbook that succeeds (4.11, 5.5, 5.6). ctrl-0 claims the job
    # instead, so it stays active and its adoption streams the unit to the end.
    make_cluster()
    job = make_job()
    work = running_unit()

    run_lost_instance_handling(mesh(EXEC), work=work)

    assert_playbook_not_left_running(job, work)
    assert job.controller_node == THIS


# Each card symptom above, asserted directly rather than through the shared "unit was canceled" check.


@pytest.mark.django_db
def test_relaunch_of_an_orphaned_job_stays_blocked():
    # 4.12 Relaunching an orphaned job (AAP-96834). The template does not allow simultaneous
    # runs, so a relaunch waits while the job is active. Devel ends the orphaned job, so the
    # relaunch starts on the same hosts while the playbook still runs.
    make_cluster()
    job = job_of_template_without_simultaneous_runs()

    run_lost_instance_handling(mesh(EXEC), work=running_unit())

    job.refresh_from_db()
    assert job.status in ('running', 'waiting')


@pytest.mark.django_db
def test_orphaned_job_still_counts_toward_its_instance_group_limit():
    # 4.17 Instance group job limits (AAP-96837). The group's limit counts active jobs. Devel
    # ends the orphaned job, so the group shows a free slot while the playbook still runs.
    make_cluster()
    job = job_in_limited_instance_group()

    run_lost_instance_handling(mesh(EXEC), work=running_unit())

    job.refresh_from_db()
    assert Job.objects.filter(instance_group=job.instance_group, status__in=('running', 'waiting')).count() == 1


@pytest.mark.django_db
def test_orphaned_job_still_uses_its_execution_node_capacity():
    # 4.23 Execution node at full capacity (AAP-96841). The node's consumed capacity counts
    # running and waiting jobs. Devel ends the orphaned job, so the node reports 0 of 84 while
    # the playbook still runs.
    make_cluster()
    peer_job(task_impact=84)

    run_lost_instance_handling(mesh(EXEC), work=running_unit())

    assert Instance.objects.get(hostname=EXEC).consumed_capacity == 84


@pytest.mark.parametrize(
    'make_job',
    [
        pytest.param(job_in_workflow, id='AAP-96833-nested-workflow'),
        pytest.param(job_in_workflow, id='AAP-96844-workflow-branch'),
    ],
)
@pytest.mark.django_db
def test_orphaned_job_that_succeeds_ends_successful(make_job):
    # 4.11 Nested workflows (AAP-96833) and 5.5 Workflow with an orphaned node (AAP-96844). A
    # workflow takes its success branch when the job ends successful. Devel ends the orphaned
    # job failed, so the workflow takes the failure branch although the playbook succeeds.
    make_cluster()
    job = make_job()
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    run_lost_instance_handling(mesh(EXEC), work=work)
    adopt_claimed([job], work)

    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_set_stats_artifacts_of_an_orphaned_job_are_kept():
    # 5.6 set_stats artifacts in a workflow (AAP-96845). The playbook's set_stats becomes the
    # job's artifacts, which later workflow nodes read. Devel ends the orphaned job failed, so
    # its artifacts are never recorded.
    make_cluster()
    job = job_in_workflow()
    events = make_events(10)
    events[-1]['event_data']['artifact_data'] = {'release': '2.5'}
    work = FakeReceptorWork({UNIT: FakeWorkUnit(events)})

    run_lost_instance_handling(mesh(EXEC), work=work)
    adopt_claimed([job], work)

    job.refresh_from_db()
    assert job.artifacts == {'release': '2.5'}


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
