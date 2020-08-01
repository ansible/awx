import json

from awxkit.api.mixins import HasCreate, HasNotifications, HasSurvey, HasCopy, DSAdapter
from awxkit.api.pages import Organization, UnifiedJobTemplate
from awxkit.utils import filter_by_class, not_provided, update_payload, random_title, suppress, PseudoNamespace
from awxkit.api.resources import resources
import awxkit.exceptions as exc

from . import base
from . import page


class WorkflowJobTemplate(HasCopy, HasCreate, HasNotifications, HasSurvey, UnifiedJobTemplate):

    optional_dependencies = [Organization]
    NATURAL_KEY = ('organization', 'name')

    def launch(self, payload={}):
        """Launch using related->launch endpoint."""
        # get related->launch
        launch_pg = self.get_related('launch')

        # launch the workflow_job_template
        result = launch_pg.post(payload)

        # return job
        jobs_pg = self.related.workflow_jobs.get(id=result.workflow_job)
        if jobs_pg.count != 1:
            msg = "workflow_job_template launched (id:{}) but job not found in response at {}/workflow_jobs/".format(
                result.json['workflow_job'], self.url
            )
            raise exc.UnexpectedAWXState(msg)
        return jobs_pg.results[0]

    def payload(self, **kwargs):
        payload = PseudoNamespace(name=kwargs.get('name') or 'WorkflowJobTemplate - {}'.format(random_title()),
                                  description=kwargs.get('description') or random_title(10))

        optional_fields = (
            "allow_simultaneous",
            "ask_variables_on_launch",
            "ask_inventory_on_launch",
            "ask_scm_branch_on_launch",
            "ask_limit_on_launch",
            "limit",
            "scm_branch",
            "survey_enabled",
            "webhook_service",
            "webhook_credential",
        )
        update_payload(payload, optional_fields, kwargs)

        extra_vars = kwargs.get('extra_vars', not_provided)
        if extra_vars != not_provided:
            if isinstance(extra_vars, dict):
                extra_vars = json.dumps(extra_vars)
            payload.update(extra_vars=extra_vars)

        if kwargs.get('organization'):
            payload.organization = kwargs.get('organization').id

        if kwargs.get('inventory'):
            payload.inventory = kwargs.get('inventory').id

        if kwargs.get('webhook_credential'):
            webhook_cred = kwargs.get('webhook_credential')
            if isinstance(webhook_cred, int):
                payload.update(webhook_credential=int(webhook_cred))
            elif hasattr(webhook_cred, 'id'):
                payload.update(webhook_credential=webhook_cred.id)
            else:
                raise AttributeError("Webhook credential must either be integer of pkid or Credential object")

        return payload

    def create_payload(self, name='', description='', organization=None, **kwargs):
        self.create_and_update_dependencies(*filter_by_class((organization, Organization)))
        organization = self.ds.organization if organization else None
        payload = self.payload(name=name, description=description, organization=organization, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, name='', description='', organization=None, **kwargs):
        payload = self.create_payload(name=name, description=description, organization=organization, **kwargs)
        return self.update_identity(WorkflowJobTemplates(self.connection).post(payload))

    def add_label(self, label):
        if isinstance(label, page.Page):
            label = label.json
        with suppress(exc.NoContent):
            self.related.labels.post(label)


page.register_page([resources.workflow_job_template,
                    (resources.workflow_job_templates, 'post'),
                    (resources.workflow_job_template_copy, 'post')], WorkflowJobTemplate)


class WorkflowJobTemplates(page.PageList, WorkflowJobTemplate):

    pass


page.register_page([resources.workflow_job_templates,
                    resources.related_workflow_job_templates], WorkflowJobTemplates)


class WorkflowJobTemplateLaunch(base.Base):

    pass


page.register_page(resources.workflow_job_template_launch, WorkflowJobTemplateLaunch)


class WorkflowJobTemplateCopy(base.Base):

    pass


page.register_page([resources.workflow_job_template_copy], WorkflowJobTemplateCopy)
