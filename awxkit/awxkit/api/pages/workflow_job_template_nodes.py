import awxkit.exceptions as exc

from awxkit.api.pages import base, WorkflowJobTemplate, UnifiedJobTemplate, JobTemplate
from awxkit.api.mixins import HasCreate, DSAdapter
from awxkit.api.resources import resources
from awxkit.utils import update_payload, PseudoNamespace, suppress
from . import page


class WorkflowJobTemplateNode(HasCreate, base.Base):

    dependencies = [WorkflowJobTemplate, UnifiedJobTemplate]

    def payload(self, workflow_job_template, unified_job_template, **kwargs):
        payload = PseudoNamespace(workflow_job_template=workflow_job_template.id,
                                  unified_job_template=unified_job_template.id)

        optional_fields = ('diff_mode', 'extra_data', 'limit', 'job_tags', 'job_type', 'skip_tags', 'verbosity',
                           'extra_data')

        update_payload(payload, optional_fields, kwargs)

        if 'inventory' in kwargs:
            payload['inventory'] = kwargs['inventory'].id

        return payload

    def create_payload(self, workflow_job_template=WorkflowJobTemplate, unified_job_template=JobTemplate, **kwargs):
        self.create_and_update_dependencies(workflow_job_template, unified_job_template)
        payload = self.payload(workflow_job_template=self.ds.workflow_job_template,
                               unified_job_template=self.ds.unified_job_template, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, workflow_job_template=WorkflowJobTemplate, unified_job_template=JobTemplate, **kwargs):
        payload = self.create_payload(workflow_job_template=workflow_job_template,
                                      unified_job_template=unified_job_template, **kwargs)
        return self.update_identity(WorkflowJobTemplateNodes(self.connection).post(payload))

    def _add_node(self, endpoint, unified_job_template):
        node = endpoint.post(dict(unified_job_template=unified_job_template.id))
        node.create_and_update_dependencies(self.ds.workflow_job_template, unified_job_template)
        return node

    def add_always_node(self, unified_job_template):
        return self._add_node(self.related.always_nodes, unified_job_template)

    def add_failure_node(self, unified_job_template):
        return self._add_node(self.related.failure_nodes, unified_job_template)

    def add_success_node(self, unified_job_template):
        return self._add_node(self.related.success_nodes, unified_job_template)

    def add_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(
                dict(id=credential.id, associate=True))

    def remove_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(
                dict(id=credential.id, disassociate=True))

    def remove_all_credentials(self):
        for cred in self.related.credentials.get().results:
            with suppress(exc.NoContent):
                self.related.credentials.post(
                    dict(id=cred.id, disassociate=True))


page.register_page([resources.workflow_job_template_node,
                    (resources.workflow_job_template_nodes, 'post')], WorkflowJobTemplateNode)


class WorkflowJobTemplateNodes(page.PageList, WorkflowJobTemplateNode):

    pass


page.register_page([resources.workflow_job_template_nodes,
                    resources.workflow_job_template_workflow_nodes,
                    resources.workflow_job_template_node_always_nodes,
                    resources.workflow_job_template_node_failure_nodes,
                    resources.workflow_job_template_node_success_nodes], WorkflowJobTemplateNodes)
