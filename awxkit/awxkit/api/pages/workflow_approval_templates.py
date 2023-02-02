from awxkit.api.pages.unified_job_templates import UnifiedJobTemplate
from awxkit.api.resources import resources
from . import page


class WorkflowApprovalTemplate(UnifiedJobTemplate):
    pass


page.register_page(
    [
        resources.workflow_approval_template,
        resources.workflow_job_template_node_create_approval_template,
    ],
    WorkflowApprovalTemplate,
)


class WorkflowApprovalTemplates(page.PageList, WorkflowApprovalTemplate):
    pass


page.register_page(resources.workflow_approval_templates, WorkflowApprovalTemplates)
