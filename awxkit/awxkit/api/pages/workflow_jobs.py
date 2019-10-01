from awxkit.api.pages import UnifiedJob
from awxkit.api.resources import resources
from . import page


class WorkflowJob(UnifiedJob):

    def __str__(self):
        # TODO: Update after endpoint's fields are finished filling out
        return super(UnifiedJob, self).__str__()

    def relaunch(self, payload={}):
        result = self.related.relaunch.post(payload)
        return self.walk(result.url)

    @property
    def result_stdout(self):
        # workflow jobs do not have result_stdout
        # which is problematic for the UnifiedJob.is_successful reliance on
        # related stdout endpoint.
        if 'result_stdout' not in self.json:
            return 'Unprovided AWX field.'
        else:
            return super(WorkflowJob, self).result_stdout


page.register_page(resources.workflow_job, WorkflowJob)


class WorkflowJobs(page.PageList, WorkflowJob):

    pass


page.register_page([resources.workflow_jobs,
                    resources.workflow_job_template_jobs,
                    resources.job_template_slice_workflow_jobs],
                   WorkflowJobs)
