from awxkit.api.pages import base
from awxkit.api.resources import resources
from awxkit.utils import poll_until, seconds_since_date_string
from . import page


class WorkflowJobNode(base.Base):
    def wait_for_job(self, interval=5, timeout=60, **kw):
        """Waits until node's job exists"""
        adjusted_timeout = timeout - seconds_since_date_string(self.created)

        poll_until(self.job_exists, interval=interval, timeout=adjusted_timeout, **kw)

        return self

    def job_exists(self):
        self.get()
        try:
            return self.job
        except AttributeError:
            return False


page.register_page(resources.workflow_job_node, WorkflowJobNode)


class WorkflowJobNodes(page.PageList, WorkflowJobNode):

    pass


page.register_page(
    [
        resources.workflow_job_nodes,
        resources.workflow_job_workflow_nodes,
        resources.workflow_job_node_always_nodes,
        resources.workflow_job_node_failure_nodes,
        resources.workflow_job_node_success_nodes,
    ],
    WorkflowJobNodes,
)
