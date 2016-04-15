import pytest

from awx.main.models.inventory import Inventory
from awx.main.models.credential import Credential
from awx.main.models.jobs import JobTemplate

@pytest.fixture
def machine_credential():
    return Credential.objects.create(name='machine-cred', kind='ssh', username='test_user', password='pas4word')

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
    machine_credential.usage_role.members.add(common_user)

    assert common_user.can_access(Credential, 'use', machine_credential)

@pytest.mark.django_db
@pytest.mark.job_permissions
def test_inventory_use_access(inventory, user):

    common_user = user('test-user', False)
    inventory.usage_role.members.add(common_user)

    assert common_user.can_access(Inventory, 'use', inventory)
