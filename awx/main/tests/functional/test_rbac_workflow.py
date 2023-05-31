import pytest

from awx.main.access import (
    WorkflowJobTemplateAccess,
    WorkflowJobTemplateNodeAccess,
    WorkflowJobAccess,
    # WorkflowJobNodeAccess
)
from awx.main.models import JobTemplate, WorkflowJobTemplateNode

from rest_framework.exceptions import PermissionDenied

from awx.main.models import InventorySource, JobLaunchConfig


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

    def test_org_workflow_admin_role_inheritance(self, wfjt, org_member):
        wfjt.organization.workflow_admin_role.members.add(org_member)

        assert org_member in wfjt.admin_role
        assert org_member in wfjt.execute_role
        assert org_member in wfjt.read_role


@pytest.mark.django_db
class TestWorkflowJobTemplateNodeAccess:
    def test_no_jt_access_to_edit(self, wfjt_node, rando):
        # without access to the related job template, admin to the WFJT can
        # not change the prompted parameters
        wfjt_node.workflow_job_template.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        assert not access.can_change(wfjt_node, {'job_type': 'check'})

    def test_node_edit_allowed(self, wfjt_node, org_admin):
        wfjt_node.unified_job_template.admin_role.members.add(org_admin)
        access = WorkflowJobTemplateNodeAccess(org_admin)
        assert access.can_change(wfjt_node, {'job_type': 'check'})

    def test_access_to_edit_non_JT(self, rando, workflow_job_template, organization, project):
        workflow_job_template.admin_role.members.add(rando)
        node = workflow_job_template.workflow_job_template_nodes.create(unified_job_template=project)
        assert not WorkflowJobTemplateNodeAccess(rando).can_change(node, {'limit': ''})

        project.update_role.members.add(rando)
        assert WorkflowJobTemplateNodeAccess(rando).can_change(node, {'limit': ''})

    def test_add_JT_no_start_perm(self, wfjt, job_template, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        job_template.read_role.members.add(rando)
        assert not access.can_add({'workflow_job_template': wfjt, 'unified_job_template': job_template})

    def test_change_JT_no_start_perm(self, wfjt, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        jt1 = JobTemplate.objects.create()
        jt1.execute_role.members.add(rando)
        assert access.can_add({'workflow_job_template': wfjt, 'unified_job_template': jt1})
        node = WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt, unified_job_template=jt1)
        jt2 = JobTemplate.objects.create()
        assert not access.can_change(node, {'unified_job_template': jt2.id})

    def test_add_node_with_minimum_permissions(self, wfjt, job_template, inventory, rando):
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        job_template.execute_role.members.add(rando)
        inventory.use_role.members.add(rando)
        assert access.can_add({'workflow_job_template': wfjt, 'inventory': inventory, 'unified_job_template': job_template})

    def test_remove_unwanted_foreign_node(self, wfjt_node, job_template, rando):
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        wfjt_node.unified_job_template = job_template
        access = WorkflowJobTemplateNodeAccess(rando)
        assert access.can_delete(wfjt_node)

    @pytest.mark.parametrize(
        "add_wfjt_admin, add_jt_admin, permission_type, expected_result, method_type",
        [
            (True, False, 'credentials', False, 'can_attach'),
            (True, True, 'credentials', True, 'can_attach'),
            (True, False, 'labels', False, 'can_attach'),
            (True, True, 'labels', True, 'can_attach'),
            (True, False, 'instance_groups', False, 'can_attach'),
            (True, True, 'instance_groups', True, 'can_attach'),
            (True, False, 'credentials', False, 'can_unattach'),
            (True, True, 'credentials', True, 'can_unattach'),
            (True, False, 'labels', False, 'can_unattach'),
            (True, True, 'labels', True, 'can_unattach'),
            (True, False, 'instance_groups', False, 'can_unattach'),
            (True, True, 'instance_groups', True, 'can_unattach'),
        ],
    )
    def test_attacher_permissions(self, wfjt_node, job_template, rando, add_wfjt_admin, permission_type, add_jt_admin, expected_result, mocker, method_type):
        wfjt = wfjt_node.workflow_job_template
        if add_wfjt_admin:
            wfjt.admin_role.members.add(rando)
            wfjt.unified_job_template = job_template
        if add_jt_admin:
            job_template.execute_role.members.add(rando)

        from awx.main.models import Credential, Label, InstanceGroup, Organization, CredentialType

        if permission_type == 'credentials':
            sub_obj = Credential.objects.create(credential_type=CredentialType.objects.create())
            sub_obj.use_role.members.add(rando)
        elif permission_type == 'labels':
            sub_obj = Label.objects.create(organization=Organization.objects.create())
            sub_obj.organization.member_role.members.add(rando)
        elif permission_type == 'instance_groups':
            sub_obj = InstanceGroup.objects.create()
            org = Organization.objects.create()
            sub_obj.use_role.members.add(rando)  # only admins can see IGs
            org.instance_groups.add(sub_obj)

        access = WorkflowJobTemplateNodeAccess(rando)
        if method_type == 'can_unattach':
            assert getattr(access, method_type)(wfjt_node, sub_obj, permission_type) == expected_result
        else:
            assert getattr(access, method_type)(wfjt_node, sub_obj, permission_type, {}) == expected_result

    # The actual attachment of labels, credentials and instance groups are tested from JobLaunchConfigAccess

    @pytest.mark.parametrize(
        "attachment_type, expect_exception, method_type",
        [
            ("credentials", False, 'can_attach'),
            ("labels", False, 'can_attach'),
            ("instance_groups", False, 'can_attach'),
            ("success_nodes", False, 'can_attach'),
            ("failure_nodes", False, 'can_attach'),
            ("always_nodes", False, 'can_attach'),
            ("junk", True, 'can_attach'),
            ("credentials", False, 'can_unattach'),
            ("labels", False, 'can_unattach'),
            ("instance_groups", False, 'can_unattach'),
            ("success_nodes", False, 'can_unattach'),
            ("failure_nodes", False, 'can_unattach'),
            ("always_nodes", False, 'can_unattach'),
            ("junk", True, 'can_unattach'),
        ],
    )
    def test_attacher_raise_not_implemented(self, wfjt_node, rando, attachment_type, expect_exception, method_type):
        wfjt = wfjt_node.workflow_job_template
        wfjt.admin_role.members.add(rando)
        access = WorkflowJobTemplateNodeAccess(rando)
        if expect_exception:
            with pytest.raises(NotImplementedError):
                access.can_attach(wfjt_node, None, attachment_type, None)
        else:
            try:
                getattr(access, method_type)(wfjt_node, None, attachment_type, None)
            except NotImplementedError:
                # We explicitly catch NotImplemented because the _nodes type will raise a different exception
                assert False, "Exception was raised when it should not have been"
            except Exception:
                #  File "/awx_devel/awx/main/access.py", line 2074, in check_same_WFJT
                #    raise Exception('Attaching workflow nodes only allowed for other nodes')
                pass

    # TODO: Implement additional tests for _nodes attachments here


@pytest.mark.django_db
class TestWorkflowJobAccess:
    @pytest.mark.parametrize("role_name", ["admin_role", "workflow_admin_role"])
    def test_org_admin_can_delete_workflow_job(self, role_name, workflow_job, org_member):
        role = getattr(workflow_job.workflow_job_template.organization, role_name)
        role.members.add(org_member)

        access = WorkflowJobAccess(org_member)
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

    def test_execute_role_relaunch(self, wfjt, workflow_job, rando):
        wfjt.execute_role.members.add(rando)
        JobLaunchConfig.objects.create(job=workflow_job)
        assert WorkflowJobAccess(rando).can_start(workflow_job)

    def test_can_start_with_limits(self, workflow_job, inventory, admin_user):
        inventory.organization.max_hosts = 1
        inventory.organization.save()
        inventory.hosts.create(name="Existing host 1")
        inventory.hosts.create(name="Existing host 2")
        workflow_job.inventory = inventory
        workflow_job.save()

        assert WorkflowJobAccess(admin_user).can_start(workflow_job)

    def test_cannot_relaunch_friends_job(self, wfjt, rando, alice):
        workflow_job = wfjt.workflow_jobs.create(name='foo', created_by=alice)
        JobLaunchConfig.objects.create(job=workflow_job, extra_data={'foo': 'fooforyou'})
        wfjt.execute_role.members.add(alice)
        assert not WorkflowJobAccess(rando).can_start(workflow_job)

    def test_relaunch_inventory_access(self, workflow_job, inventory, rando):
        wfjt = workflow_job.workflow_job_template
        wfjt.execute_role.members.add(rando)
        assert rando in wfjt.execute_role
        workflow_job.created_by = rando
        workflow_job.inventory = inventory
        workflow_job.save()
        wfjt.ask_inventory_on_launch = True
        wfjt.save()
        JobLaunchConfig.objects.create(job=workflow_job, inventory=inventory)
        with pytest.raises(PermissionDenied):
            WorkflowJobAccess(rando).can_start(workflow_job)
        inventory.use_role.members.add(rando)
        assert WorkflowJobAccess(rando).can_start(workflow_job)


@pytest.mark.django_db
class TestWFJTCopyAccess:
    def test_copy_permissions_org_admin(self, wfjt, org_admin, org_member):
        admin_access = WorkflowJobTemplateAccess(org_admin)
        assert admin_access.can_copy(wfjt)

        wfjt.organization.workflow_admin_role.members.add(org_member)
        admin_access = WorkflowJobTemplateAccess(org_member)
        assert admin_access.can_copy(wfjt)

    def test_copy_permissions_user(self, wfjt, org_admin, org_member):
        """
        Only org admins and org workflow admins are able to add WFJTs, only org admins
        are able to copy them
        """
        wfjt.admin_role.members.add(org_member)
        member_access = WorkflowJobTemplateAccess(org_member)
        assert not member_access.can_copy(wfjt)

    def test_workflow_copy_warnings_inv(self, wfjt, rando, inventory):
        """
        The user `rando` does not have access to the prompted inventory in a
        node inside the workflow - test surfacing this information
        """
        wfjt.workflow_job_template_nodes.create(inventory=inventory)
        access = WorkflowJobTemplateAccess(rando, save_messages=True)
        assert not access.can_copy(wfjt)
        warnings = access.messages
        assert 'inventories_unable_to_copy' in warnings

    def test_workflow_copy_no_start(self, wfjt, inventory, admin_user):
        # Test that un-startable resource doesn't block copy
        inv_src = InventorySource.objects.create(inventory=inventory, source='file')
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
