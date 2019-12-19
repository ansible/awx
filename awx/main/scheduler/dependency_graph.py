from django.utils.timezone import now as tz_now

from awx.main.models import (
    Job,
    ProjectUpdate,
    InventoryUpdate,
    SystemJob,
    AdHocCommand,
    WorkflowJob,
)


class DependencyGraph(object):
    PROJECT_UPDATES = 'project_updates'
    INVENTORY_UPDATES = 'inventory_updates'

    JOB_TEMPLATE_JOBS = 'job_template_jobs'

    SYSTEM_JOB = 'system_job'
    INVENTORY_SOURCE_UPDATES = 'inventory_source_updates'
    WORKFLOW_JOB_TEMPLATES_JOBS = 'workflow_job_template_jobs'

    LATEST_PROJECT_UPDATES = 'latest_project_updates'
    LATEST_INVENTORY_UPDATES = 'latest_inventory_updates'

    INVENTORY_SOURCES = 'inventory_source_ids'

    def __init__(self, queue):
        self.queue = queue
        self.data = {}
        # project_id -> True / False
        self.data[self.PROJECT_UPDATES] = {}
        # inventory_id -> True / False
        self.data[self.INVENTORY_UPDATES] = {}
        # job_template_id -> True / False
        self.data[self.JOB_TEMPLATE_JOBS] = {}

        '''
        Track runnable job related project and inventory to ensure updates
        don't run while a job needing those resources is running.
        '''

        # inventory_source_id -> True / False
        self.data[self.INVENTORY_SOURCE_UPDATES] = {}
        # True / False
        self.data[self.SYSTEM_JOB] = True
        # workflow_job_template_id -> True / False
        self.data[self.WORKFLOW_JOB_TEMPLATES_JOBS] = {}

        # project_id -> latest ProjectUpdateLatestDict'
        self.data[self.LATEST_PROJECT_UPDATES] = {}
        # inventory_source_id -> latest InventoryUpdateLatestDict
        self.data[self.LATEST_INVENTORY_UPDATES] = {}

        # inventory_id -> [inventory_source_ids]
        self.data[self.INVENTORY_SOURCES] = {}

    def add_latest_project_update(self, job):
        self.data[self.LATEST_PROJECT_UPDATES][job.project_id] = job

    def get_now(self):
        return tz_now()

    def mark_system_job(self):
        self.data[self.SYSTEM_JOB] = False

    def mark_project_update(self, job):
        self.data[self.PROJECT_UPDATES][job.project_id] = False

    def mark_inventory_update(self, inventory_id):
        self.data[self.INVENTORY_UPDATES][inventory_id] = False

    def mark_inventory_source_update(self, inventory_source_id):
        self.data[self.INVENTORY_SOURCE_UPDATES][inventory_source_id] = False

    def mark_job_template_job(self, job):
        self.data[self.JOB_TEMPLATE_JOBS][job.job_template_id] = False

    def mark_workflow_job(self, job):
        self.data[self.WORKFLOW_JOB_TEMPLATES_JOBS][job.workflow_job_template_id] = False

    def can_project_update_run(self, job):
        return self.data[self.PROJECT_UPDATES].get(job.project_id, True)

    def can_inventory_update_run(self, job):
        return self.data[self.INVENTORY_SOURCE_UPDATES].get(job.inventory_source_id, True)

    def can_job_run(self, job):
        if self.data[self.PROJECT_UPDATES].get(job.project_id, True) is True and \
                self.data[self.INVENTORY_UPDATES].get(job.inventory_id, True) is True:
            if job.allow_simultaneous is False:
                return self.data[self.JOB_TEMPLATE_JOBS].get(job.job_template_id, True)
            else:
                return True
        return False

    def can_workflow_job_run(self, job):
        if job.allow_simultaneous:
            return True
        return self.data[self.WORKFLOW_JOB_TEMPLATES_JOBS].get(job.workflow_job_template_id, True)

    def can_system_job_run(self):
        return self.data[self.SYSTEM_JOB]

    def can_ad_hoc_command_run(self, job):
        return self.data[self.INVENTORY_UPDATES].get(job.inventory_id, True)

    def is_job_blocked(self, job):
        if type(job) is ProjectUpdate:
            return not self.can_project_update_run(job)
        elif type(job) is InventoryUpdate:
            return not self.can_inventory_update_run(job)
        elif type(job) is Job:
            return not self.can_job_run(job)
        elif type(job) is SystemJob:
            return not self.can_system_job_run()
        elif type(job) is AdHocCommand:
            return not self.can_ad_hoc_command_run(job)
        elif type(job) is WorkflowJob:
            return not self.can_workflow_job_run(job)

    def add_job(self, job):
        if type(job) is ProjectUpdate:
            self.mark_project_update(job)
        elif type(job) is InventoryUpdate:
            self.mark_inventory_update(job.inventory_source.inventory_id)
            self.mark_inventory_source_update(job.inventory_source_id)
        elif type(job) is Job:
            self.mark_job_template_job(job)
        elif type(job) is WorkflowJob:
            self.mark_workflow_job(job)
        elif type(job) is SystemJob:
            self.mark_system_job()
        elif type(job) is AdHocCommand:
            self.mark_inventory_update(job.inventory_id)

    def add_jobs(self, jobs):
        for j in jobs:
            self.add_job(j)
