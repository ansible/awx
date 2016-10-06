import pytest

from awx.main.access import (
    WorkflowJobTemplateAccess,
    WorkflowJobTemplateNodeAccess,
    WorkflowJobAccess,
    # WorkflowJobNodeAccess
)

@pytest.fixture
def wfjt(workflow_job_template_factory, organization):
    objects = workflow_job_template_factory('test_workflow', organization=organization, persisted=True)
    return objects.workflow_job_template

@pytest.fixture
def wfjt_with_nodes(workflow_job_template_factory, organization, job_template):
    objects = workflow_job_template_factory(
        'test_workflow', organization=organization, workflow_job_template_nodes=[{'unified_job_template': job_template}], persisted=True)
    return objects.workflow_job_template

@pytest.fixture
def wfjt_node(wfjt_with_nodes):
    return wfjt_with_nodes.workflow_job_template_nodes.all()[0]

@pytest.fixture
def workflow_job(wfjt):
    return wfjt.jobs.create(name='test_workflow')


@pytest.mark.django_db
class TestWorkflowJobTemplateAccess:

    def test_random_user_no_edit(self, wfjt, rando):
        access = WorkflowJobTemplateAccess(rando)
        assert not access.can_change(wfjt, {'name': 'new name'})

    def test_org_admin_edit(self, wfjt, org_admin):
        access = WorkflowJobTemplateAccess(org_admin)
        assert access.can_change(wfjt, {'name': 'new name'})

    def test_org_admin_role_inheritance(self, wfjt, org_admin):
        assert org_admin in wfjt.admin_role
        assert org_admin in wfjt.execute_role
        assert org_admin in wfjt.read_role

    def test_jt_blocks_copy(self, wfjt_with_nodes, org_admin):
        """I want to copy a workflow JT in my organization, but someone
        included a job template that I don't have access to, so I can
        not copy the WFJT as-is"""
        access = WorkflowJobTemplateAccess(org_admin)
        assert not access.can_add({'reference_obj': wfjt_with_nodes})

@pytest.mark.django_db
class TestWorkflowJobTemplateNodeAccess:

    def test_jt_access_to_edit(self, wfjt_node, org_admin):
        access = WorkflowJobTemplateNodeAccess(org_admin)
        assert not access.can_change(wfjt_node, {'job_type': 'scan'})

@pytest.mark.django_db
class TestWorkflowJobAccess:

    def test_wfjt_admin_delete(self, wfjt, workflow_job, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobAccess(rando)
        assert access.can_delete(workflow_job)

    def test_cancel_your_own_job(self, wfjt, workflow_job, rando):
        wfjt.execute_role.members.add(rando)
        workflow_job.created_by = rando
        workflow_job.save()
        access = WorkflowJobAccess(rando)
        assert access.can_cancel(workflow_job)
