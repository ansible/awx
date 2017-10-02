import pytest

from awx.main.access import (
    WorkflowJobTemplateAccess,
    WorkflowJobTemplateNodeAccess,
    WorkflowJobAccess,
    # WorkflowJobNodeAccess
)

from awx.main.models import InventorySource


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

    def test_no_jt_access_to_edit(self, wfjt_node, org_admin):
        # without access to the related job template, admin to the WFJT can
        # not change the prompted parameters
        access = WorkflowJobTemplateNodeAccess(org_admin)
        assert not access.can_change(wfjt_node, {'job_type': 'scan'})

    def test_add_JT_no_start_perm(self, wfjt, job_template, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        job_template.read_role.members.add(rando)
        assert not access.can_add({
            'workflow_job_template': wfjt,
            'unified_job_template': job_template})

    def test_add_node_with_minimum_permissions(self, wfjt, job_template, inventory, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        job_template.execute_role.members.add(rando)
        inventory.use_role.members.add(rando)
        assert access.can_add({
            'workflow_job_template': wfjt,
            'inventory': inventory,
            'unified_job_template': job_template})

    def test_remove_unwanted_foreign_node(self, wfjt_node, job_template, rando):
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        wfjt_node.unified_job_template = job_template
        access = WorkflowJobTemplateNodeAccess(rando)
        assert access.can_delete(wfjt_node)


@pytest.mark.django_db
class TestWorkflowJobAccess:

    def test_org_admin_can_delete_workflow_job(self, workflow_job, org_admin):
        access = WorkflowJobAccess(org_admin)
        assert access.can_delete(workflow_job)

    def test_wfjt_admin_can_delete_workflow_job(self, workflow_job, rando):
        workflow_job.workflow_job_template.admin_role.members.add(rando)
        access = WorkflowJobAccess(rando)
        assert not access.can_delete(workflow_job)

    def test_cancel_your_own_job(self, wfjt, workflow_job, rando):
        wfjt.execute_role.members.add(rando)
        workflow_job.created_by = rando
        workflow_job.save()
        access = WorkflowJobAccess(rando)
        assert access.can_cancel(workflow_job)

    def test_admin_cancel_access(self, wfjt, workflow_job, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobAccess(rando)
        assert access.can_cancel(workflow_job)


@pytest.mark.django_db
class TestWFJTCopyAccess:

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
        assert 'inventories_unable_to_copy' in warnings


    def test_workflow_copy_no_start(self, wfjt, inventory, admin_user):
        # Test that un-startable resource doesn't block copy
        inv_src = InventorySource.objects.create(
            inventory = inventory,
            source = 'custom',
            source_script = None
        )
        assert not inv_src.can_update
        wfjt.workflow_job_template_nodes.create(unified_job_template=inv_src)
        access = WorkflowJobTemplateAccess(admin_user, save_messages=True)
        access.can_copy(wfjt)
        assert not access.messages

    def test_workflow_copy_warnings_jt(self, wfjt, rando, job_template):
        wfjt.workflow_job_template_nodes.create(unified_job_template=job_template)
        access = WorkflowJobTemplateAccess(rando, save_messages=True)
        assert not access.can_copy(wfjt)
        warnings = access.messages
        assert 'templates_unable_to_copy' in warnings
