
# Python
import pytest
from datetime import timedelta

class TestJobBlocked():
    def test_inventory_update_waiting(self, scheduler_factory, waiting_inventory_update, pending_job):
        scheduler = scheduler_factory(tasks=[waiting_inventory_update, pending_job])

        scheduler._schedule()

        scheduler.start_task.assert_not_called()

    def test_inventory_update_running(self, scheduler_factory, running_inventory_update, pending_job, inventory_source_factory, inventory_id_sources):
        scheduler = scheduler_factory(tasks=[running_inventory_update, pending_job],
                                      inventory_sources=inventory_id_sources)

        scheduler._schedule()

        scheduler.start_task.assert_not_called()

    def test_project_update_running(self, scheduler_factory, pending_job, running_project_update):
        scheduler = scheduler_factory(tasks=[running_project_update, pending_job])

        scheduler._schedule()

        scheduler.start_task.assert_not_called()
        assert scheduler.create_project_update.call_count == 0

    def test_project_update_waiting(self, scheduler_factory, pending_job, waiting_project_update):
        scheduler = scheduler_factory(tasks=[waiting_project_update, pending_job],
                                      latest_project_updates=[waiting_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_not_called()
        assert scheduler.create_project_update.call_count == 0

class TestJob():
    @pytest.fixture
    def successful_project_update(self, project_update_factory):
        project_update = project_update_factory() 
        project_update['status'] = 'successful'
        project_update['finished'] = project_update['created'] + timedelta(seconds=10)
        project_update['project__scm_update_cache_timeout'] = 3600
        return project_update

    def test_existing_dependencies_finished(self, scheduler_factory, successful_project_update, successful_inventory_update_latest, pending_job):
        scheduler = scheduler_factory(tasks=[successful_project_update, pending_job],
                                      latest_project_updates=[successful_project_update],
                                      latest_inventory_updates=[successful_inventory_update_latest])

        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_job)

