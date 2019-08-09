from awxkit.api.pages import UnifiedJob
from awxkit.api.resources import resources
from . import base
from . import page


class Job(UnifiedJob):

    def relaunch(self, payload={}):
        result = self.related.relaunch.post(payload)
        return self.walk(result.endpoint)


page.register_page(resources.job, Job)


class Jobs(page.PageList, Job):

    pass


page.register_page([resources.jobs,
                    resources.job_template_jobs,
                    resources.system_job_template_jobs], Jobs)


class JobCancel(UnifiedJob):

    pass


page.register_page(resources.job_cancel, JobCancel)


class JobEvent(base.Base):

    pass


page.register_page([resources.job_event,
                    resources.job_job_event], JobEvent)


class JobEvents(page.PageList, JobEvent):

    pass


page.register_page([resources.job_events,
                    resources.job_job_events,
                    resources.job_event_children,
                    resources.group_related_job_events], JobEvents)


class JobPlay(base.Base):

    pass


page.register_page(resources.job_play, JobPlay)


class JobPlays(page.PageList, JobPlay):

    pass


page.register_page(resources.job_plays, JobPlays)


class JobTask(base.Base):

    pass


page.register_page(resources.job_task, JobTask)


class JobTasks(page.PageList, JobTask):

    pass


page.register_page(resources.job_tasks, JobTasks)


class JobHostSummary(base.Base):

    pass


page.register_page(resources.job_host_summary, JobHostSummary)


class JobHostSummaries(page.PageList, JobHostSummary):

    pass


page.register_page([resources.job_host_summaries,
                    resources.group_related_job_host_summaries], JobHostSummaries)


class JobRelaunch(base.Base):

    pass


page.register_page(resources.job_relaunch, JobRelaunch)


class JobStdout(base.Base):

    pass


page.register_page(resources.related_stdout, JobStdout)
