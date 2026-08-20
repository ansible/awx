import copy
import json
import logging
import os
import tempfile
import shutil
from unittest import mock

import pytest

from awx.main.tasks.system import (
    CleanupImagesAndFiles,
    awx_periodic_scheduler,
    execution_node_health_check,
    inspect_established_receptor_connections,
    clear_setting_cache,
    _batched_delete_inventory,
)
from awx.main.management.commands.dispatcherd import Command
from django.db import DatabaseError

from awx.main.models import (
    Instance,
    Inventory,
    Job,
    JobTemplate,
    Organization,
    ReceptorAddress,
    InstanceLink,
    Schedule,
    TowerScheduleState,
)
from awx.main.models.inventory import Group, Host


@pytest.mark.django_db
class TestLinkState:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.IS_K8S = True

    def test_inspect_established_receptor_connections(self):
        """
        Change link state from ADDING to ESTABLISHED
        if the receptor status KnownConnectionCosts field
        has an entry for the source and target node.
        """
        hop1 = Instance.objects.create(hostname="hop1")
        hop2 = Instance.objects.create(hostname="hop2")
        hop2addr = ReceptorAddress.objects.create(
            instance=hop2, address="hop2", port=5678
        )
        InstanceLink.objects.create(
            source=hop1, target=hop2addr, link_state=InstanceLink.States.ADDING
        )

        # calling with empty KnownConnectionCosts should not change the link state
        inspect_established_receptor_connections({"KnownConnectionCosts": {}})
        assert (
            InstanceLink.objects.get(source=hop1, target=hop2addr).link_state
            == InstanceLink.States.ADDING
        )

        mesh_state = {"KnownConnectionCosts": {"hop1": {"hop2": 1}}}
        inspect_established_receptor_connections(mesh_state)
        assert (
            InstanceLink.objects.get(source=hop1, target=hop2addr).link_state
            == InstanceLink.States.ESTABLISHED
        )


@pytest.fixture
def job_folder_factory(request):
    def _rf(job_id="1234"):
        pdd_path = tempfile.mkdtemp(prefix=f"awx_{job_id}_")

        def test_folder_cleanup():
            if os.path.exists(pdd_path):
                shutil.rmtree(pdd_path)

        request.addfinalizer(test_folder_cleanup)

        return pdd_path

    return _rf


@pytest.fixture
def mock_job_folder(job_folder_factory):
    return job_folder_factory()


@pytest.mark.django_db
@pytest.mark.parametrize("node_type", ("control. hybrid"))
def test_no_worker_info_on_AWX_nodes(node_type):
    hostname = "us-south-3-compute.invalid"
    Instance.objects.create(hostname=hostname, node_type=node_type)
    assert execution_node_health_check(hostname) is None


@pytest.mark.django_db
def test_folder_cleanup_stale_file(mock_job_folder, mock_me):
    CleanupImagesAndFiles.run()
    assert os.path.exists(
        mock_job_folder
    )  # grace period should protect folder from deletion

    CleanupImagesAndFiles.run(grace_period=0)
    assert not os.path.exists(mock_job_folder)  # should be deleted


@pytest.mark.django_db
def test_folder_cleanup_running_job(mock_job_folder, me_inst):
    job = Job.objects.create(
        id=1234, controller_node=me_inst.hostname, status="running"
    )
    CleanupImagesAndFiles.run(grace_period=0)
    assert os.path.exists(
        mock_job_folder
    )  # running job should prevent folder from getting deleted

    job.status = "failed"
    job.save(update_fields=["status"])
    CleanupImagesAndFiles.run(grace_period=0)
    assert not os.path.exists(
        mock_job_folder
    )  # job is finished and no grace period, should delete


@pytest.mark.django_db
def test_folder_cleanup_multiple_running_jobs(job_folder_factory, me_inst):
    jobs = []
    dirs = []
    num_jobs = 3

    for i in range(num_jobs):
        job = Job.objects.create(controller_node=me_inst.hostname, status="running")
        dirs.append(job_folder_factory(job.id))
        jobs.append(job)

    CleanupImagesAndFiles.run(grace_period=0)

    assert [os.path.exists(d) for d in dirs] == [True for i in range(num_jobs)]


@pytest.mark.django_db
class TestBatchedDeleteInventory:
    def _make_inventory_with_hosts(self, count):
        from django.utils import timezone

        now = timezone.now()
        org = Organization.objects.create(name="test-org")
        inv = Inventory.objects.create(name="test-inv", organization=org)
        group = Group.objects.create(name="test-group", inventory=inv)
        hosts = [
            Host(name=f"host-{i}", inventory=inv, created=now, modified=now)
            for i in range(count)
        ]
        Host.objects.bulk_create(hosts)
        group.hosts.set(Host.objects.filter(inventory=inv))
        return inv

    def test_deletes_all_hosts_and_inventory(self):
        inv = self._make_inventory_with_hosts(10)
        inv_id = inv.id
        _batched_delete_inventory(inv, batch_size=3)
        assert not Host.objects.filter(inventory_id=inv_id).exists()
        assert not Group.objects.filter(inventory_id=inv_id).exists()
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_no_hosts(self):
        inv = self._make_inventory_with_hosts(0)
        inv_id = inv.id
        _batched_delete_inventory(inv)
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_exactly_one_batch(self):
        inv = self._make_inventory_with_hosts(5)
        inv_id = inv.id
        _batched_delete_inventory(inv, batch_size=5)
        assert not Host.objects.filter(inventory_id=inv_id).exists()
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_idempotent_after_partial_delete(self):
        """Simulate a crash mid-way: delete some hosts manually, then run
        _batched_delete_inventory — it should finish the job cleanly."""
        inv = self._make_inventory_with_hosts(10)
        inv_id = inv.id

        # Simulate a partial deletion (as if the task crashed after 4 hosts)
        partial_pks = list(
            Host.objects.filter(inventory=inv).values_list("pk", flat=True)[:4]
        )
        Host.objects.filter(pk__in=partial_pks).delete()
        assert Host.objects.filter(inventory_id=inv_id).count() == 6

        # Re-running should delete the remaining hosts and the inventory
        inv.refresh_from_db()
        _batched_delete_inventory(inv, batch_size=3)
        assert not Host.objects.filter(inventory_id=inv_id).exists()
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_delete_inventory_retries_on_database_error(self):
        """DatabaseError during deletion triggers a retry."""
        from awx.main.tasks.system import delete_inventory

        inv = self._make_inventory_with_hosts(3)
        inv_id = inv.id

        call_count = {"n": 0}
        original = (
            _batched_delete_inventory.__wrapped__
            if hasattr(_batched_delete_inventory, "__wrapped__")
            else _batched_delete_inventory
        )

        def flaky_delete(inventory, batch_size=500):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise DatabaseError("connection reset")
            return original(inventory, batch_size=batch_size)

        with mock.patch(
            "awx.main.tasks.system._batched_delete_inventory", side_effect=flaky_delete
        ):
            with mock.patch("awx.main.tasks.system.emit_channel_notification"):
                with mock.patch("awx.main.tasks.system.time.sleep"):
                    delete_inventory(inv_id, None, retries=2)

        assert call_count["n"] == 2
        assert not Inventory.objects.filter(id=inv_id).exists()


@pytest.mark.django_db
def test_clear_setting_cache_log_level_branch(settings):
    settings.LOG_AGGREGATOR_LEVEL = "DEBUG"
    settings.CLUSTER_HOST_ID = "control-node"
    published_messages = []

    class DummyBroker:
        def publish_message(self, channel, message):
            published_messages.append((channel, message))

        def close(self):
            pass

    dummy_broker = DummyBroker()

    with mock.patch(
        "dispatcherd.control.get_broker", return_value=dummy_broker
    ) as mock_get_broker:
        clear_setting_cache(["LOG_AGGREGATOR_LEVEL"])

    mock_get_broker.assert_called_once()
    assert published_messages, "control command was not sent through the broker"
    queue, payload = published_messages[-1]
    assert queue == "control-node"
    body = json.loads(payload)
    assert body["control"] == "set_log_level"
    assert body["control_data"] == {"level": "DEBUG"}


@pytest.mark.django_db
def test_configure_dispatcher_logging_updates_level(settings):
    original_logging_settings = copy.deepcopy(settings.LOGGING)
    settings.LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "dynamic_level_filter": {
                "()": "logging.Filter",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "filters": ["dynamic_level_filter"],
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "dispatcherd": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            }
        },
    }
    settings.LOG_AGGREGATOR_LEVEL = "WARNING"

    Command().configure_dispatcher_logging()

    assert logging.getLogger("dispatcherd").level == logging.WARNING
    settings.LOGGING = original_logging_settings


@pytest.mark.django_db
def test_periodic_scheduler_survives_invalid_schedule(inventory, project):
    """A schedule whose update_computed_fields raises should not prevent the
    periodic scheduler from processing other healthy schedules.

    Simulates the scenario where a corrupt rrule causes update_computed_fields
    to raise ValueError (the exact error from the BYHOUR/DST bug). Verifies
    the scheduler completes, creates a job for the healthy schedule, and skips
    the broken one.
    """
    from datetime import datetime, timedelta, timezone as dt_tz

    jt = JobTemplate.objects.create(
        name="test-jt", project=project, playbook="helloworld.yml", inventory=inventory
    )

    run_now = datetime(2026, 7, 1, 14, 0, 0, tzinfo=dt_tz.utc)
    last_run = run_now - timedelta(seconds=30)

    healthy_schedule = Schedule.objects.create(
        name="healthy-schedule",
        rrule="DTSTART:20260101T120000Z RRULE:FREQ=DAILY;INTERVAL=1",
        unified_job_template=jt,
    )
    Schedule.objects.filter(pk=healthy_schedule.pk).update(
        next_run=last_run + timedelta(seconds=10)
    )

    bad_schedule = Schedule.objects.create(
        name="bad-schedule",
        rrule="DTSTART:20260101T120000Z RRULE:FREQ=DAILY;INTERVAL=1",
        unified_job_template=jt,
    )
    bad_schedule_id = bad_schedule.pk
    Schedule.objects.filter(pk=bad_schedule_id).update(
        next_run=last_run + timedelta(seconds=10)
    )

    state = TowerScheduleState.get_solo()
    state.schedule_last_run = last_run
    state.save()

    # Make update_computed_fields raise for the bad schedule, simulating the
    # ValueError that occurs when _fast_forward_rrule hits a corrupt rrule.
    original_ucf = Schedule.update_computed_fields
    bad_schedule_raised = False

    def update_or_raise(self):
        nonlocal bad_schedule_raised
        if self.pk == bad_schedule_id:
            bad_schedule_raised = True
            raise ValueError("Invalid rrule byxxx generates an empty set.")
        return original_ucf(self)

    with (
        mock.patch("awx.main.tasks.system.now", return_value=run_now),
        mock.patch("awx.main.models.schedules.now", return_value=run_now),
        mock.patch("awx.main.models.schedules.emit_channel_notification"),
        mock.patch("awx.main.tasks.system.emit_channel_notification"),
        mock.patch.object(Schedule, "update_computed_fields", update_or_raise),
    ):
        awx_periodic_scheduler()

    assert bad_schedule_raised, (
        "The bad schedule's update_computed_fields should have been called and raised"
    )

    healthy_jobs = Job.objects.filter(schedule=healthy_schedule)
    assert healthy_jobs.count() == 1, (
        "Healthy schedule should have created exactly one job"
    )

    bad_jobs = Job.objects.filter(schedule=bad_schedule)
    assert bad_jobs.count() == 0, "Bad schedule should not have created a job"
