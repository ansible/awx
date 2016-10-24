from datetime import timedelta
from django.utils.timezone import now as tz_now

from awx.main.scheduler.partial import JobDict, ProjectUpdateDict, InventoryUpdateDict
class DependencyGraph(object):
    PROJECT_UPDATES = 'project_updates'
    INVENTORY_UPDATES = 'inventory_updates'
    JOB_TEMPLATE_JOBS = 'job_template_jobs'
    INVENTORY_SOURCE_UPDATES = 'inventory_source_updates'

    LATEST_PROJECT_UPDATES = 'latest_project_updates'
    LATEST_INVENTORY_UPDATES = 'latest_inventory_updates'

    INVENTORY_SOURCES = 'inventory_source_ids'

    def __init__(self, *args, **kwargs):
        self.data = {}
        # project_id -> True / False
        self.data[self.PROJECT_UPDATES] = {}
        # inventory_id -> True / False
        self.data[self.INVENTORY_UPDATES] = {}
        # job_template_id -> True / False
        self.data[self.JOB_TEMPLATE_JOBS] = {}
        # inventory_source_id -> True / False
        self.data[self.INVENTORY_SOURCE_UPDATES] = {}

        # project_id -> latest ProjectUpdateLatestDict
        self.data[self.LATEST_PROJECT_UPDATES] = {}
        # inventory_source_id -> latest InventoryUpdateLatestDict
        self.data[self.LATEST_INVENTORY_UPDATES] = {}

        # inventory_id -> [inventory_source_ids]
        self.data[self.INVENTORY_SOURCES] = {}

    def add_latest_project_update(self, job):
        self.data[self.LATEST_PROJECT_UPDATES][job['project_id']] = job

    def add_latest_inventory_update(self, job):
        self.data[self.LATEST_INVENTORY_UPDATES][job['inventory_source_id']] = job

    def add_inventory_sources(self, inventory_id, inventory_sources):
        self.data[self.INVENTORY_SOURCES][inventory_id] = inventory_sources

    def get_inventory_sources(self, inventory_id):
        return self.data[self.INVENTORY_SOURCES].get(inventory_id, [])

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
        if latest_project_update['status'] in ['failed', 'canceled']:
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

    def should_update_related_inventory_source(self, job, inventory_source_id):
        now = self.get_now()
        latest_inventory_update = self.data[self.LATEST_INVENTORY_UPDATES].get(inventory_source_id, None)
        if not latest_inventory_update:
            return True

        # TODO: Other finished, failed cases? i.e. error ?
        if latest_inventory_update['status'] in ['failed', 'canceled']:
            return True

        '''
        This is a bit of fuzzy logic.
        If the latest inventory update has a created time == job_created_time-2
        then consider the inventory update found. This is so we don't enter an infinite loop
        of updating the project when cache timeout is 0.
        '''
        if latest_inventory_update['inventory_source__update_cache_timeout'] == 0 and \
                latest_inventory_update['launch_type'] == 'dependency' and \
                latest_inventory_update['created'] == job['created'] - timedelta(seconds=2):
            return False

        '''
        Normal, expected, cache timeout logic
        '''
        timeout_seconds = timedelta(seconds=latest_inventory_update['inventory_source__update_cache_timeout'])
        if (latest_inventory_update['finished'] + timeout_seconds) < now:
            return True
        
        return False

    def mark_project_update(self, job):
        self.data[self.PROJECT_UPDATES][job['project_id']] = False

    def mark_inventory_update(self, inventory_id):
        self.data[self.INVENTORY_UPDATES][inventory_id] = False

    def mark_inventory_source_update(self, inventory_source_id):
        self.data[self.INVENTORY_SOURCE_UPDATES][inventory_source_id] = False

    def mark_job_template_job(self, job):
        self.data[self.INVENTORY_UPDATES][job['inventory_id']] = False
        self.data[self.PROJECT_UPDATES][job['project_id']] = False
        self.data[self.JOB_TEMPLATE_JOBS][job['job_template_id']] = False

    def can_project_update_run(self, job):
        return self.data[self.PROJECT_UPDATES].get(job['project_id'], True)

    def can_inventory_update_run(self, inventory_source_id):
        return self.data[self.INVENTORY_SOURCE_UPDATES].get(inventory_source_id, True)

    def can_job_run(self, job):
        if self.can_project_update_run(job) is True and \
                self.data[self.INVENTORY_UPDATES].get(job['inventory_id'], True) is True:
            if job['allow_simultaneous'] is False:
                return self.data[self.JOB_TEMPLATE_JOBS].get(job['job_template_id'], True)
            else:
                return True
        return False

    def is_job_blocked(self, job):
        if type(job) is ProjectUpdateDict:
            return not self.can_project_update_run(job)
        elif type(job) is InventoryUpdateDict:
            return not self.can_inventory_update_run(job['inventory_source_id'])
        elif type(job) is JobDict:
            return not self.can_job_run(job)

    def add_job(self, job):
        if type(job) is ProjectUpdateDict:
            self.mark_project_update(job)
        elif type(job) is InventoryUpdateDict:
            self.mark_inventory_update(job['inventory_source__inventory_id'])
            self.mark_inventory_source_update(job['inventory_source_id'])
        elif type(job) is JobDict:
            self.mark_job_template_job(job)

    def add_jobs(self, jobs):
        for j in jobs:
            self.add_job(j)
 
