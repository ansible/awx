from awxkit.api.pages import UnifiedJob
from awxkit.api.resources import resources
from . import page


class SystemJob(UnifiedJob):

    pass


page.register_page(resources.system_job, SystemJob)


class SystemJobs(page.PageList, SystemJob):

    pass


page.register_page(resources.system_jobs, SystemJobs)


class SystemJobCancel(UnifiedJob):

    pass


page.register_page(resources.system_job_cancel, SystemJobCancel)
