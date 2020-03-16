import pytest

from rest_framework.exceptions import PermissionDenied

from awx.main.models.inventory import Inventory
from awx.main.models.credential import Credential
from awx.main.models.jobs import JobTemplate, Job
from awx.main.access import (
    UnifiedJobAccess,
    WorkflowJobAccess, WorkflowJobNodeAccess,
    JobAccess
)


@pytest.mark.django_db
@pytest.mark.job_permissions
def test_admin_executing_permissions(deploy_jobtemplate, inventory, machine_credential, user):
    admin_user = user('admin-user', True)

    assert admin_user.can_access(Inventory, 'use', inventory)
    assert admin_user.can_access(Inventory, 'run_ad_hoc_commands', inventory)  # for ad_hoc
    assert admin_user.can_access(JobTemplate, 'start', deploy_jobtemplate)
    assert admin_user.can_access(Credential, 'use', machine_credential)


@pytest.mark.django_db
@pytest.mark.job_permissions
def test_admin_executing_permissions_with_limits(deploy_jobtemplate, inventory, user):
    admin_user = user('admin-user', True)

    inventory.organization.max_hosts = 1
    inventory.organization.save()
    inventory.hosts.create(name="Existing host 1")
    inventory.hosts.create(name="Existing host 2")

    assert admin_user.can_access(JobTemplate, 'start', deploy_jobtemplate)


@pytest.mark.django_db
@pytest.mark.job_permissions
def test_job_template_start_access(deploy_jobtemplate, user):
    common_user = user('test-user', False)
    deploy_jobtemplate.execute_role.members.add(common_user)

    assert common_user.can_access(JobTemplate, 'start', deploy_jobtemplate)


@pytest.mark.django_db
@pytest.mark.job_permissions
def test_credential_use_access(machine_credential, user):
    common_user = user('test-user', False)
    machine_credential.use_role.members.add(common_user)

    assert common_user.can_access(Credential, 'use', machine_credential)


@pytest.mark.django_db
@pytest.mark.job_permissions
def test_inventory_use_access(inventory, user):
    common_user = user('test-user', False)
    inventory.use_role.members.add(common_user)

    assert common_user.can_access(Inventory, 'use', inventory)


@pytest.mark.django_db
def test_slice_job(slice_job_factory, rando):
    workflow_job = slice_job_factory(2, jt_kwargs={'created_by': rando}, spawn=True)
    workflow_job.job_template.execute_role.members.add(rando)

    # Abilities of user with execute_role for slice workflow job container
    assert WorkflowJobAccess(rando).can_start(workflow_job)  # relaunch allowed
    for access_cls in (UnifiedJobAccess, WorkflowJobAccess):
        access = access_cls(rando)
        assert access.can_read(workflow_job)
        assert workflow_job in access.get_queryset()

    # Abilities of user with execute_role for all the slice of the job
    for node in workflow_job.workflow_nodes.all():
        access = WorkflowJobNodeAccess(rando)
        assert access.can_read(node)
        assert node in access.get_queryset()
        job = node.job
        assert JobAccess(rando).can_start(job)  # relaunch allowed
        for access_cls in (UnifiedJobAccess, JobAccess):
            access = access_cls(rando)
            assert access.can_read(job)
            assert job in access.get_queryset()


@pytest.mark.django_db
class TestJobRelaunchAccess:
    @pytest.fixture
    def job_no_prompts(self, machine_credential, inventory, organization):
        jt = JobTemplate.objects.create(name='test-job_template', inventory=inventory, organization=organization)
        jt.credentials.add(machine_credential)
        return jt.create_unified_job()

    @pytest.fixture
    def job_with_prompts(self, machine_credential, inventory, organization, credentialtype_ssh):
        jt = JobTemplate.objects.create(
            name='test-job-template-prompts', inventory=inventory,
            ask_tags_on_launch=True, ask_variables_on_launch=True, ask_skip_tags_on_launch=True,
            ask_limit_on_launch=True, ask_job_type_on_launch=True, ask_verbosity_on_launch=True,
            ask_inventory_on_launch=True, ask_credential_on_launch=True)
        jt.credentials.add(machine_credential)
        new_cred = Credential.objects.create(
            name='new-cred',
            credential_type=credentialtype_ssh,
            inputs={
                'username': 'test_user',
                'password': 'pas4word'
            }
        )
        new_cred.save()
        new_inv = Inventory.objects.create(name='new-inv', organization=organization)
        return jt.create_unified_job(credentials=[new_cred], inventory=new_inv)

    def test_normal_relaunch_via_job_template(self, job_no_prompts, rando):
        "Has JT execute_role, job unchanged relative to JT"
        job_no_prompts.job_template.execute_role.members.add(rando)
        assert rando.can_access(Job, 'start', job_no_prompts)

    def test_orphan_relaunch_via_organization(self, job_no_prompts, rando, organization):
        "JT for job has been deleted, relevant organization roles will allow management"
        assert job_no_prompts.organization == organization
        organization.execute_role.members.add(rando)
        job_no_prompts.job_template.delete()
        job_no_prompts.job_template = None  # Django should do this for us, but it does not
        assert rando.can_access(Job, 'start', job_no_prompts)

    def test_no_relaunch_without_prompted_fields_access(self, job_with_prompts, rando):
        "Has JT execute_role but no use_role on inventory & credential - deny relaunch"
        job_with_prompts.job_template.execute_role.members.add(rando)
        with pytest.raises(PermissionDenied) as exc:
            rando.can_access(Job, 'start', job_with_prompts)
        assert 'Job was launched with prompted fields you do not have access to' in str(exc)

    def test_can_relaunch_with_prompted_fields_access(self, job_with_prompts, rando):
        "Has use_role on the prompted inventory & credential - allow relaunch"
        job_with_prompts.job_template.execute_role.members.add(rando)
        for cred in job_with_prompts.credentials.all():
            cred.use_role.members.add(rando)
        job_with_prompts.inventory.use_role.members.add(rando)
        job_with_prompts.created_by = rando
        assert rando.can_access(Job, 'start', job_with_prompts)

    def test_no_relaunch_after_limit_change(self, inventory, machine_credential, rando):
        "State of the job contradicts the JT state - deny relaunch based on JT execute"
        jt = JobTemplate.objects.create(name='test-job_template', inventory=inventory, ask_limit_on_launch=True)
        jt.credentials.add(machine_credential)
        job_with_prompts = jt.create_unified_job(limit='webservers')
        jt.ask_limit_on_launch = False
        jt.save()
        jt.execute_role.members.add(rando)
        with pytest.raises(PermissionDenied):
            rando.can_access(Job, 'start', job_with_prompts)

    def test_can_relaunch_if_limit_was_prompt(self, job_with_prompts, rando):
        "Job state differs from JT, but only on prompted fields - allow relaunch"
        job_with_prompts.job_template.execute_role.members.add(rando)
        job_with_prompts.limit = 'webservers'
        job_with_prompts.save()
        job_with_prompts.inventory.use_role.members.add(rando)
        for cred in job_with_prompts.credentials.all():
            cred.use_role.members.add(rando)
        assert rando.can_access(Job, 'start', job_with_prompts)
