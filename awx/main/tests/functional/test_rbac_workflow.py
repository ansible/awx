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
    return wfjt.workflow_jobs.create(name='test_workflow')


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

    def test_copy_permissions_org_admin(self, wfjt, org_admin, org_member):
        admin_access = WorkflowJobTemplateAccess(org_admin)
        assert admin_access.can_copy(wfjt)

    def test_copy_permissions_user(self, wfjt, org_admin, org_member):
        '''
        Only org admins are able to add WFJTs, only org admins
        are able to copy them
        '''
        wfjt.admin_role.members.add(org_member)
        member_access = WorkflowJobTemplateAccess(org_member)
        assert not member_access.can_copy(wfjt)

    def test_workflow_copy_warnings_inv(self, wfjt, rando, inventory):
        '''
        The user `rando` does not have access to the prompted inventory in a
        node inside the workflow - test surfacing this information
        '''
        wfjt.workflow_job_template_nodes.create(inventory=inventory)
        access = WorkflowJobTemplateAccess(rando, save_messages=True)
        assert not access.can_copy(wfjt)
        warnings = access.messages
        assert 1 in warnings
        assert 'inventory' in warnings[1]

    def test_workflow_copy_warnings_jt(self, wfjt, rando, job_template):
        wfjt.workflow_job_template_nodes.create(unified_job_template=job_template)
        access = WorkflowJobTemplateAccess(rando, save_messages=True)
        assert not access.can_copy(wfjt)
        warnings = access.messages
        assert 1 in warnings
        assert 'unified_job_template' in warnings[1]
