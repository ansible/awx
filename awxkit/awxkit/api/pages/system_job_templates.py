from awxkit.api.mixins import HasNotifications
from awxkit.api.pages import UnifiedJobTemplate
from awxkit.api.resources import resources
from . import page


class SystemJobTemplate(UnifiedJobTemplate, HasNotifications):
    NATURAL_KEY = ('name', 'organization')

    def launch(self, payload={}):
        """Launch the system_job_template using related->launch endpoint."""
        result = self.related.launch.post(payload)

        # return job
        jobs_pg = self.get_related('jobs', id=result.json['system_job'])
        assert jobs_pg.count == 1, "system_job_template launched (id:%s) but unable to find matching " "job at %s/jobs/" % (result.json['job'], self.url)
        return jobs_pg.results[0]


page.register_page(resources.system_job_template, SystemJobTemplate)


class SystemJobTemplates(page.PageList, SystemJobTemplate):

    pass


page.register_page(resources.system_job_templates, SystemJobTemplates)
