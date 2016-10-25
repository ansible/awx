
# TODO: wherever get_latest_rpoject_update_task() is stubbed and returns a
# ProjectUpdateDict. We should instead return a ProjectUpdateLatestDict()
# For now, this is ok since the fields on deviate that much.

class TestStartProjectUpdate():
    def test(self, scheduler_factory, pending_project_update):
        scheduler = scheduler_factory(tasks=[pending_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_project_update)
        assert scheduler.create_project_update.call_count == 0

    '''
    Explicit project update should always run. They should not use cache logic.
    '''
    def test_cache_oblivious(self, scheduler_factory, successful_project_update, pending_project_update):
        scheduler = scheduler_factory(tasks=[pending_project_update],
                                      latest_project_updates=[successful_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_project_update)
        assert scheduler.create_project_update.call_count == 0


class TestCreateDependentProjectUpdate():

    def test(self, scheduler_factory, pending_job, waiting_project_update):
        scheduler = scheduler_factory(tasks=[pending_job], 
                                      create_project_update=waiting_project_update)

        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_project_update, [pending_job])

    def test_cache_hit(self, scheduler_factory, pending_job, successful_project_update):
        scheduler = scheduler_factory(tasks=[successful_project_update, pending_job], 
                                      latest_project_updates=[successful_project_update])
        scheduler._schedule()

        scheduler.start_task.assert_called_with(pending_job)

    def test_cache_miss(self, scheduler_factory, pending_job, successful_project_update_cache_expired, waiting_project_update):
        scheduler = scheduler_factory(tasks=[successful_project_update_cache_expired, pending_job], 
                                      latest_project_updates=[successful_project_update_cache_expired], 
                                      create_project_update=waiting_project_update)
        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_project_update, [pending_job])

    def test_last_update_failed(self, scheduler_factory, pending_job, failed_project_update, waiting_project_update):
        scheduler = scheduler_factory(tasks=[failed_project_update, pending_job], 
                                      latest_project_updates=[failed_project_update], 
                                      create_project_update=waiting_project_update)
        scheduler._schedule()

        scheduler.start_task.assert_called_with(waiting_project_update, [pending_job])

class TestProjectUpdateBlocked():
    def test_projct_update_running(self, scheduler_factory, running_project_update, pending_project_update):
        scheduler = scheduler_factory(tasks=[running_project_update, pending_project_update])
        scheduler._schedule()

        scheduler.start_task.assert_not_called()
        assert scheduler.create_project_update.call_count == 0

    def test_job_running(self, scheduler_factory, running_job, pending_project_update):
        scheduler = scheduler_factory(tasks=[running_job, pending_project_update])

        scheduler._schedule()

        scheduler.start_task.assert_not_called()

