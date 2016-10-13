from datetime import timedelta
from django.utils.timezone import now as tz_now

from awx.main.scheduler.partial import JobDict, ProjectUpdateDict, InventoryUpdateDict
class DependencyGraph(object):
    PROJECT_UPDATES = 'project_updates'
    INVENTORY_UPDATES = 'inventory_updates'
    JOB_TEMPLATE_JOBS = 'job_template_jobs'
    LATEST_PROJECT_UPDATES = 'latest_project_updates'

    def __init__(self, *args, **kwargs):
        self.data = {}
        # project_id -> True / False
        self.data[self.PROJECT_UPDATES] = {}
        # inventory_id -> True / False
        self.data[self.INVENTORY_UPDATES] = {}
        # job_template_id -> True / False
        self.data[self.JOB_TEMPLATE_JOBS] = {}

        # project_id -> latest ProjectUpdateDict
        self.data[self.LATEST_PROJECT_UPDATES] = {}

    def add_latest_project_update(self, job):
        self.data[self.LATEST_PROJECT_UPDATES][job['project_id']] = job

    def get_now(self):
        return tz_now()

    '''
    JobDict
    
    Presume that job is related to a project that is update on launch
    '''
    def should_update_related_project(self, job):
        now = self.get_now()
        latest_project_update = self.data[self.LATEST_PROJECT_UPDATES].get(job['project_id'], None)
        if not latest_project_update:
            return True

        # TODO: Other finished, failed cases? i.e. error ?
        if latest_project_update['status'] == 'failed':
            return True

        '''
        This is a bit of fuzzy logic.
        If the latest project update has a created time == job_created_time-1 
        then consider the project update found. This is so we don't enter an infinite loop
        of updating the project when cache timeout is 0.
        '''
        if latest_project_update['project__scm_update_cache_timeout'] == 0 and \
                latest_project_update['launch_type'] == 'dependency' and \
                latest_project_update['created'] == job['created'] - timedelta(seconds=1):
            return False

        '''
        Normal, expected, cache timeout logic
        '''
        timeout_seconds = timedelta(seconds=latest_project_update['project__scm_update_cache_timeout'])
        if (latest_project_update['finished'] + timeout_seconds) < now:
            return True

        return False

    def add_project_update(self, job):
        self.data[self.PROJECT_UPDATES][job['project_id']] = False

    def add_inventory_update(self, job):
        self.data[self.INVENTORY_UPDATES][job['inventory_id']] = False

    def add_job_template_job(self, job):
        self.data[self.JOB_TEMPLATE_JOBS][job['job_template_id']] = False


    def can_project_update_run(self, job):
        return self.data[self.PROJECT_UPDATES].get(job['project_id'], True)

    def can_inventory_update_run(self, job):
        return self.data[self.INVENTORY_UPDATES].get(job['inventory_id'], True)

    def can_job_run(self, job):
        if self.can_project_update_run(job) is True and \
                self.can_inventory_update_run(job) is True:
            if job['allow_simultaneous'] is False:
                return self.data[self.JOB_TEMPLATE_JOBS].get(job['job_template_id'], True)
            else:
                return True
        return False

    def is_job_blocked(self, job):
        if type(job) is ProjectUpdateDict:
            return not self.can_project_update_run(job)
        elif type(job) is InventoryUpdateDict:
            return not self.can_inventory_update_run(job)
        elif type(job) is JobDict:
            return not self.can_job_run(job)

    def add_job(self, job):
        if type(job) is ProjectUpdateDict:
            self.add_project_update(job)
        elif type(job) is InventoryUpdateDict:
            self.add_inventory_update(job)
        elif type(job) is JobDict:
            self.add_job_template_job(job)

    def add_jobs(self, jobs):
        for j in jobs:
            self.add_job(j)
 
