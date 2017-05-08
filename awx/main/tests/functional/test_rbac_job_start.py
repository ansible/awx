import pytest

from awx.main.models.inventory import Inventory
from awx.main.models.credential import Credential
from awx.main.models.jobs import JobTemplate, Job


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
class TestJobRelaunchAccess:
    @pytest.fixture
    def job_no_prompts(self, machine_credential, inventory):
        jt = JobTemplate.objects.create(name='test-job_template', credential=machine_credential, inventory=inventory)
        return jt.create_unified_job()

    @pytest.fixture
    def job_with_prompts(self, machine_credential, inventory, organization, credentialtype_ssh):
        jt = JobTemplate.objects.create(
            name='test-job-template-prompts', credential=machine_credential, inventory=inventory,
            ask_tags_on_launch=True, ask_variables_on_launch=True, ask_skip_tags_on_launch=True,
            ask_limit_on_launch=True, ask_job_type_on_launch=True, ask_verbosity_on_launch=True,
            ask_inventory_on_launch=True, ask_credential_on_launch=True)
        new_cred = Credential.objects.create(
            name='new-cred',
            credential_type=credentialtype_ssh,
            inputs={
                'username': 'test_user',
                'password': 'pas4word'
            }
        )
        new_inv = Inventory.objects.create(name='new-inv', organization=organization)
        return jt.create_unified_job(credential=new_cred, inventory=new_inv)

    def test_normal_relaunch_via_job_template(self, job_no_prompts, rando):
        "Has JT execute_role, job unchanged relative to JT"
        job_no_prompts.job_template.execute_role.members.add(rando)
        assert rando.can_access(Job, 'start', job_no_prompts)

    def test_no_relaunch_without_prompted_fields_access(self, job_with_prompts, rando):
        "Has JT execute_role but no use_role on inventory & credential - deny relaunch"
        job_with_prompts.job_template.execute_role.members.add(rando)
        assert not rando.can_access(Job, 'start', job_with_prompts)

    def test_can_relaunch_with_prompted_fields_access(self, job_with_prompts, rando):
        "Has use_role on the prompted inventory & credential - allow relaunch"
        job_with_prompts.job_template.execute_role.members.add(rando)
        job_with_prompts.credential.use_role.members.add(rando)
        job_with_prompts.inventory.use_role.members.add(rando)
        assert rando.can_access(Job, 'start', job_with_prompts)

    def test_no_relaunch_after_limit_change(self, job_no_prompts, rando):
        "State of the job contradicts the JT state - deny relaunch"
        job_no_prompts.job_template.execute_role.members.add(rando)
        job_no_prompts.limit = 'webservers'
        job_no_prompts.save()
        assert not rando.can_access(Job, 'start', job_no_prompts)

    def test_can_relaunch_if_limit_was_prompt(self, job_with_prompts, rando):
        "Job state differs from JT, but only on prompted fields - allow relaunch"
        job_with_prompts.job_template.execute_role.members.add(rando)
        job_with_prompts.limit = 'webservers'
        job_with_prompts.save()
        assert not rando.can_access(Job, 'start', job_with_prompts)
