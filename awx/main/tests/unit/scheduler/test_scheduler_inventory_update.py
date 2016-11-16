
# Python
import pytest
from datetime import timedelta


@pytest.fixture
def pending_job(job_factory):
    return job_factory(project__scm_update_on_launch=False, inventory__inventory_sources=['1'])


@pytest.fixture
def successful_inventory_update_latest(inventory_update_latest_factory):
    iu = inventory_update_latest_factory()
    iu['inventory_source__update_cache_timeout'] = 100
    iu['status'] = 'successful'
    iu['finished'] = iu['created'] + timedelta(seconds=10)
    return iu


@pytest.fixture
def successful_inventory_update_latest_cache_expired(inventory_update_latest_factory):
    iu = inventory_update_latest_factory()
    iu['inventory_source__update_cache_timeout'] = 1
    iu['finished'] = iu['created'] + timedelta(seconds=2)
    return iu


class TestStartInventoryUpdate():
    def test_pending(self, scheduler_factory, pending_inventory_update):
        scheduler = scheduler_factory(tasks=[pending_inventory_update])

        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_inventory_update)


class TestInventoryUpdateBlocked():
    def test_running_inventory_update(self, epoch, scheduler_factory, running_inventory_update, pending_inventory_update):
        running_inventory_update['created'] = epoch - timedelta(seconds=100)
        pending_inventory_update['created'] = epoch - timedelta(seconds=90)

        scheduler = scheduler_factory(tasks=[running_inventory_update, pending_inventory_update])

        scheduler._schedule()

    def test_waiting_inventory_update(self, epoch, scheduler_factory, waiting_inventory_update, pending_inventory_update):
        waiting_inventory_update['created'] = epoch - timedelta(seconds=100)
        pending_inventory_update['created'] = epoch - timedelta(seconds=90)

        scheduler = scheduler_factory(tasks=[waiting_inventory_update, pending_inventory_update])

        scheduler._schedule()


class TestCreateDependentInventoryUpdate():
    def test(self, scheduler_factory, pending_job, waiting_inventory_update, inventory_id_sources):
        scheduler = scheduler_factory(tasks=[pending_job], 
                                      create_inventory_update=waiting_inventory_update,
                                      inventory_sources=inventory_id_sources)

        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_inventory_update, [pending_job])

    def test_cache_hit(self, scheduler_factory, pending_job, successful_inventory_update, successful_inventory_update_latest):
        scheduler = scheduler_factory(tasks=[successful_inventory_update, pending_job], 
                                      latest_inventory_updates=[successful_inventory_update_latest])
        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_job)

    def test_cache_miss(self, scheduler_factory, pending_job, successful_inventory_update, successful_inventory_update_latest_cache_expired, waiting_inventory_update, inventory_id_sources):
        scheduler = scheduler_factory(tasks=[successful_inventory_update, pending_job], 
                                      latest_inventory_updates=[successful_inventory_update_latest_cache_expired], 
                                      create_inventory_update=waiting_inventory_update,
                                      inventory_sources=inventory_id_sources)
        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_inventory_update, [pending_job])

    def test_last_update_failed(self, scheduler_factory, pending_job, failed_inventory_update, failed_inventory_update_latest, waiting_inventory_update, inventory_id_sources):
        scheduler = scheduler_factory(tasks=[failed_inventory_update, pending_job], 
                                      latest_inventory_updates=[failed_inventory_update_latest], 
                                      create_inventory_update=waiting_inventory_update,
                                      inventory_sources=inventory_id_sources)
        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_inventory_update, [pending_job])
