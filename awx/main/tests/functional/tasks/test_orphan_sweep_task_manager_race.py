"""REQ-04: the orphan sweep and the TaskManager cannot overfill a controller together.

The TaskManager schedules from a capacity snapshot taken under `task_manager_lock`. A sweep claim
that lands while it runs is not in that snapshot, so both could fill the same last slot. These tests
run the real TaskManager and a real sweep on two database connections against PostgreSQL, because an
advisory lock is a PostgreSQL feature and a mocked lock cannot show that two connections exclude each other.

The TaskManager runs on the test's own thread (it installs a signal handler, which only the main thread
may do) and the sweep runs on a second thread, started from inside `start_task`: after the TaskManager
holds the lock and has built its snapshot, and before it writes the placement.
"""

import threading
from unittest import mock

import pytest
from django.conf import settings
from django.db import connection
from django.utils.timezone import now, timedelta

from awx.main.models import Instance, Job
from awx.main.scheduler import TaskManager
from awx.main.tasks.system import _sweep_orphaned_jobs
from awx.main.tests.functional.task_management import create_job

pytestmark = pytest.mark.django_db(transaction=True)

WAIT = 30  # seconds; a stuck sweep fails the test instead of hanging it


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != 'postgresql':
        pytest.skip('task_manager_lock is a PostgreSQL advisory lock')


@pytest.fixture
def adopter(controlplane_instance_group):
    return controlplane_instance_group.instances.get()


@pytest.fixture
def orphan():
    """A running job of a controller that is gone, on an execution node the adopter does not control."""
    # The TaskManager reaps a running job whose execution node is not a registered instance.
    Instance.objects.create(hostname='exec-1', node_type='execution', node_state='ready', capacity=100)
    return Job.objects.create(
        controller_node='dead-controller', execution_node='exec-1', status='running', work_unit_id='unit-orphan', started=now() - timedelta(seconds=600)
    )


def sweep(adopter):
    """Run one sweep as `adopter`, with the mesh and route lookups that need receptor stubbed out."""
    with (
        mock.patch.object(Instance.objects, 'me', return_value=Instance.objects.get(pk=adopter.pk)),
        mock.patch('awx.main.tasks.system._receptor_mesh_hostnames', return_value=set()),
        mock.patch('awx.main.tasks.system._exclude_unreachable_execution_nodes', side_effect=lambda orphans, route_lookup, clock=None: orphans),
        mock.patch('awx.main.tasks.system._publish_adoption'),
    ):
        _sweep_orphaned_jobs(Instance.objects.get(pk=adopter.pk))


def run_task_manager_with_a_sweep_mid_run(adopter, orphan):
    """Run one real TaskManager pass; mid-run, run a sweep on another connection. Return who owned the orphan after it."""
    seen = {}

    def sweep_on_another_connection():
        try:
            sweep(adopter)
        except BaseException as exc:  # reported on the test thread below
            seen['error'] = exc
        finally:
            connection.close()

    original = TaskManager.start_task

    def start_task(tm, *args, **kwargs):
        thread = threading.Thread(target=sweep_on_another_connection)
        thread.start()
        thread.join(WAIT)
        assert not thread.is_alive(), 'the sweep blocked on the TaskManager'
        seen['controller_node'] = Job.objects.get(pk=orphan.pk).controller_node
        return original(tm, *args, **kwargs)

    with (
        mock.patch.object(TaskManager, 'start_task', start_task),
        mock.patch('awx.main.utils.common.ScheduleManager._schedule'),
        mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status'),
    ):
        TaskManager().schedule()
    assert 'error' not in seen, seen.get('error')
    assert 'controller_node' in seen, 'the TaskManager never started the pending job'
    return seen['controller_node']


def pend_one_job(adopter, job_template_factory, spare_slots):
    """Pend one job and size the adopter to hold it plus `spare_slots` control slots."""
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred')
    pending = create_job(objects.job_template)
    Instance.objects.filter(pk=adopter.pk).update(capacity=pending.task_impact + spare_slots * settings.AWX_CONTROL_NODE_TASK_IMPACT)
    return pending


def test_sweep_claims_nothing_while_the_task_manager_runs_and_the_node_is_never_overfilled(adopter, orphan, job_template_factory):
    pending = pend_one_job(adopter, job_template_factory, spare_slots=1)

    owner_mid_run = run_task_manager_with_a_sweep_mid_run(adopter, orphan)

    assert Job.objects.get(pk=pending.pk).status == 'waiting'
    refreshed = Instance.objects.get(pk=adopter.pk)
    assert refreshed.consumed_capacity <= refreshed.capacity, 'the sweep and the TaskManager both took the last slot'
    # The TaskManager counted on the last slot; a claim made mid-run would have taken it.
    assert owner_mid_run == 'dead-controller'
    sweep(adopter)  # the next heartbeat: the node is full, so the orphan waits for another controller
    assert Job.objects.get(pk=orphan.pk).controller_node == 'dead-controller'


def test_sweep_adopts_once_the_task_manager_is_done_and_there_is_room(adopter, orphan, job_template_factory):
    pending = pend_one_job(adopter, job_template_factory, spare_slots=2)

    owner_mid_run = run_task_manager_with_a_sweep_mid_run(adopter, orphan)

    assert owner_mid_run == 'dead-controller', 'the sweep claimed while the TaskManager held the lock'
    assert Job.objects.get(pk=pending.pk).status == 'waiting'
    sweep(adopter)
    assert Job.objects.get(pk=orphan.pk).controller_node == adopter.hostname
    refreshed = Instance.objects.get(pk=adopter.pk)
    assert refreshed.consumed_capacity <= refreshed.capacity
