from contextlib import suppress

import awxkit.exceptions as exc
from awxkit.api.pages import base, WorkflowJobTemplate, UnifiedJobTemplate, JobTemplate
from awxkit.api.mixins import HasCreate, DSAdapter
from awxkit.api.resources import resources
from awxkit.utils import update_payload, PseudoNamespace, random_title
from . import page


class WorkflowJobTemplateNode(HasCreate, base.Base):
    dependencies = [WorkflowJobTemplate, UnifiedJobTemplate]
    NATURAL_KEY = ('workflow_job_template', 'identifier')

    def payload(self, workflow_job_template, unified_job_template, **kwargs):
        if not unified_job_template:
            # May pass "None" to explicitly create an approval node
            payload = PseudoNamespace(workflow_job_template=workflow_job_template.id)
        else:
            payload = PseudoNamespace(workflow_job_template=workflow_job_template.id, unified_job_template=unified_job_template.id)

        optional_fields = (
            'diff_mode',
            'extra_data',
            'limit',
            'scm_branch',
            'job_tags',
            'job_type',
            'skip_tags',
            'verbosity',
            'extra_data',
            'identifier',
            'all_parents_must_converge',
            # prompt fields for JTs
            'job_slice_count',
            'forks',
            'timeout',
            'execution_environment',
        )

        update_payload(payload, optional_fields, kwargs)

        if 'inventory' in kwargs:
            payload['inventory'] = kwargs['inventory'].id

        return payload

    def create_payload(self, workflow_job_template=WorkflowJobTemplate, unified_job_template=JobTemplate, **kwargs):
        if not unified_job_template:
            self.create_and_update_dependencies(workflow_job_template)
            payload = self.payload(workflow_job_template=self.ds.workflow_job_template, unified_job_template=None, **kwargs)
        else:
            self.create_and_update_dependencies(workflow_job_template, unified_job_template)
            payload = self.payload(workflow_job_template=self.ds.workflow_job_template, unified_job_template=self.ds.unified_job_template, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, workflow_job_template=WorkflowJobTemplate, unified_job_template=JobTemplate, **kwargs):
        payload = self.create_payload(workflow_job_template=workflow_job_template, unified_job_template=unified_job_template, **kwargs)
        return self.update_identity(WorkflowJobTemplateNodes(self.connection).post(payload))

    def _add_node(self, endpoint, unified_job_template, **kwargs):
        node = endpoint.post(dict(unified_job_template=unified_job_template.id, **kwargs))
        node.create_and_update_dependencies(self.ds.workflow_job_template, unified_job_template)
        return node

    def add_always_node(self, unified_job_template, **kwargs):
        return self._add_node(self.related.always_nodes, unified_job_template, **kwargs)

    def add_failure_node(self, unified_job_template, **kwargs):
        return self._add_node(self.related.failure_nodes, unified_job_template, **kwargs)

    def add_success_node(self, unified_job_template, **kwargs):
        return self._add_node(self.related.success_nodes, unified_job_template, **kwargs)

    def add_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(dict(id=credential.id, associate=True))

    def remove_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(dict(id=credential.id, disassociate=True))

    def remove_all_credentials(self):
        for cred in self.related.credentials.get().results:
            with suppress(exc.NoContent):
                self.related.credentials.post(dict(id=cred.id, disassociate=True))

    def make_approval_node(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = 'approval node {}'.format(random_title())
        self.related.create_approval_template.post(kwargs)
        return self.get()

    def get_job_node(self, workflow_job):
        candidates = workflow_job.get_related('workflow_nodes', identifier=self.identifier)
        return candidates.results.pop()

    def add_label(self, label):
        with suppress(exc.NoContent):
            self.related.labels.post(dict(id=label.id))

    def add_instance_group(self, instance_group):
        with suppress(exc.NoContent):
            self.related.instance_groups.post(dict(id=instance_group.id))


page.register_page(
    [resources.workflow_job_template_node, (resources.workflow_job_template_nodes, 'post'), (resources.workflow_job_template_workflow_nodes, 'post')],
    WorkflowJobTemplateNode,
)


class WorkflowJobTemplateNodes(page.PageList, WorkflowJobTemplateNode):
    pass


page.register_page(
    [
        resources.workflow_job_template_nodes,
        resources.workflow_job_template_workflow_nodes,
        resources.workflow_job_template_node_always_nodes,
        resources.workflow_job_template_node_failure_nodes,
        resources.workflow_job_template_node_success_nodes,
    ],
    WorkflowJobTemplateNodes,
)
