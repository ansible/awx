import pytest

from django.conf import settings
from django.test.utils import override_settings

from awx.main.models import Inventory, InventorySource, InventoryUpdate, ProjectUpdate
from awx.main.models.execution_environments import ExecutionEnvironment
from awx.main.utils.execution_environments import get_default_execution_environment, get_control_plane_execution_environment
from awx.main.management.commands.register_default_execution_environments import Command


@pytest.fixture
def set_up_defaults():
    Command().handle()


@pytest.mark.django_db
def test_default_to_jobs_default(set_up_defaults, organization):
    """Under normal operation, the default EE should be from the list of global job EEs
    which are populated by the installer
    """
    # Fill in some other unrelated EEs
    ExecutionEnvironment.objects.create(name='Steves environment', image='quay.io/ansible/awx-ee')
    ExecutionEnvironment(name=settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['name'], image='quay.io/ansible/awx-ee', organization=organization, pull='missing')
    default_ee = get_default_execution_environment()
    assert default_ee.image == settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['image']
    assert default_ee.name == settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['name']
    assert default_ee.pull == settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['pull']


@pytest.mark.django_db
def test_default_to_control_plane(set_up_defaults):
    """If all of the job execution environments are job execution environments have gone missing
    then it will refuse to use the control plane execution environment as the default
    """
    for ee in ExecutionEnvironment.objects.all():
        if ee.name == 'Control Plane Execution Environment':
            continue
        ee.delete()
    assert get_default_execution_environment() is None


@pytest.mark.django_db
def test_user_default(set_up_defaults):
    """If superuser has configured a default, then their preference should come first, of course"""
    ee = ExecutionEnvironment.objects.create(name='Steves environment', image='quay.io/ansible/awx-ee')
    with override_settings(DEFAULT_EXECUTION_ENVIRONMENT=ee):
        assert get_default_execution_environment() == ee


@pytest.mark.django_db
def test_project_update_uses_control_plane_ee(set_up_defaults, project):
    """ProjectUpdate.resolve_execution_environment() should always return the control plane EE"""
    control_plane_ee = get_control_plane_execution_environment()
    project_update = ProjectUpdate.objects.create(
        project=project,
        scm_type=project.scm_type,
    )
    resolved_ee = project_update.resolve_execution_environment()
    assert resolved_ee == control_plane_ee
    assert resolved_ee.managed is True
    assert resolved_ee.organization is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    'source,expects_control_plane',
    [
        ('constructed', True),
        ('ec2', False),
        ('azure_rm', False),
        ('gce', False),
        ('vmware', False),
        ('openstack', False),
        ('rhv', False),
        ('satellite6', False),
        ('controller', False),
    ],
)
def test_inventory_update_ee_resolution(set_up_defaults, organization, source, expects_control_plane):
    """Constructed inventory updates should resolve to the control plane EE; all others should not"""
    control_plane_ee = get_control_plane_execution_environment()
    inv = Inventory.objects.create(
        name=f'test-inv-{source}',
        kind='constructed' if source == 'constructed' else '',
        organization=organization,
    )
    inv_source = InventorySource.objects.create(
        name=f'{source}-source',
        inventory=inv,
        source=source,
    )
    inv_update = InventoryUpdate.objects.create(
        inventory=inv,
        inventory_source=inv_source,
        source=source,
    )
    resolved_ee = inv_update.resolve_execution_environment()
    if expects_control_plane:
        assert resolved_ee == control_plane_ee
    else:
        assert resolved_ee != control_plane_ee
