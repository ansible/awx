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

    INVENTORY_SOURCES = 'inventory_source_ids'

    def __init__(self):
        self.data = {}
        self.data[self.PROJECT_UPDATES] = {}
        # The reason for tracking both inventory and inventory sources:
        # Consider InvA, which has two sources, InvSource1, InvSource2.
        # JobB might depend on InvA, which launches two updates, one for each source.
        # To determine if JobB can run, we can just check InvA, which is marked in
        # INVENTORY_UPDATES, instead of having to check for both entries in
        # INVENTORY_SOURCE_UPDATES.
        self.data[self.INVENTORY_UPDATES] = {}
        self.data[self.INVENTORY_SOURCE_UPDATES] = {}
        self.data[self.JOB_TEMPLATE_JOBS] = {}
        self.data[self.SYSTEM_JOB] = {}
        self.data[self.WORKFLOW_JOB_TEMPLATES_JOBS] = {}

    def mark_if_no_key(self, job_type, id, job):
        # only mark first occurrence of a task. If 10 of JobA are launched
        # (concurrent disabled), the dependency graph should return that jobs
        # 2 through 10 are blocked by job1
        if id not in self.data[job_type]:
            self.data[job_type][id] = job

    def get_item(self, job_type, id):
        return self.data[job_type].get(id, None)

    def mark_system_job(self, job):
        # Don't track different types of system jobs, so that only one can run
        # at a time. Therefore id in this case is just 'system_job'.
        self.mark_if_no_key(self.SYSTEM_JOB, 'system_job', job)

    def mark_project_update(self, job):
        self.mark_if_no_key(self.PROJECT_UPDATES, job.project_id, job)

    def mark_inventory_update(self, job):
        if type(job) is AdHocCommand:
            self.mark_if_no_key(self.INVENTORY_UPDATES, job.inventory_id, job)
        else:
            self.mark_if_no_key(self.INVENTORY_UPDATES, job.inventory_source.inventory_id, job)

    def mark_inventory_source_update(self, job):
        self.mark_if_no_key(self.INVENTORY_SOURCE_UPDATES, job.inventory_source_id, job)

    def mark_job_template_job(self, job):
        self.mark_if_no_key(self.JOB_TEMPLATE_JOBS, job.job_template_id, job)

    def mark_workflow_job(self, job):
        self.mark_if_no_key(self.WORKFLOW_JOB_TEMPLATES_JOBS, job.workflow_job_template_id, job)

    def project_update_blocked_by(self, job):
        return self.get_item(self.PROJECT_UPDATES, job.project_id)

    def inventory_update_blocked_by(self, job):
        return self.get_item(self.INVENTORY_SOURCE_UPDATES, job.inventory_source_id)

    def job_blocked_by(self, job):
        project_block = self.get_item(self.PROJECT_UPDATES, job.project_id)
        inventory_block = self.get_item(self.INVENTORY_UPDATES, job.inventory_id)
        if job.allow_simultaneous is False:
            job_block = self.get_item(self.JOB_TEMPLATE_JOBS, job.job_template_id)
        else:
            job_block = None
        return project_block or inventory_block or job_block

    def workflow_job_blocked_by(self, job):
        if job.allow_simultaneous is False:
            return self.get_item(self.WORKFLOW_JOB_TEMPLATES_JOBS, job.workflow_job_template_id)
        return None

    def system_job_blocked_by(self, job):
        return self.get_item(self.SYSTEM_JOB, 'system_job')

    def ad_hoc_command_blocked_by(self, job):
        return self.get_item(self.INVENTORY_UPDATES, job.inventory_id)

    def task_blocked_by(self, job):
        if type(job) is ProjectUpdate:
            return self.project_update_blocked_by(job)
        elif type(job) is InventoryUpdate:
            return self.inventory_update_blocked_by(job)
        elif type(job) is Job:
            return self.job_blocked_by(job)
        elif type(job) is SystemJob:
            return self.system_job_blocked_by(job)
        elif type(job) is AdHocCommand:
            return self.ad_hoc_command_blocked_by(job)
        elif type(job) is WorkflowJob:
            return self.workflow_job_blocked_by(job)

    def add_job(self, job):
        if type(job) is ProjectUpdate:
            self.mark_project_update(job)
        elif type(job) is InventoryUpdate:
            self.mark_inventory_update(job)
            self.mark_inventory_source_update(job)
        elif type(job) is Job:
            self.mark_job_template_job(job)
        elif type(job) is WorkflowJob:
            self.mark_workflow_job(job)
        elif type(job) is SystemJob:
            self.mark_system_job(job)
        elif type(job) is AdHocCommand:
            self.mark_inventory_update(job)

    def add_jobs(self, jobs):
        for j in jobs:
            self.add_job(j)
