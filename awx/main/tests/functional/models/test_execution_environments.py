import pytest

from django.conf import settings
from django.test.utils import override_settings

from awx.main.models.execution_environments import ExecutionEnvironment
from awx.main.utils.execution_environments import get_default_execution_environment
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
    ExecutionEnvironment(name=settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['name'], image='quay.io/ansible/awx-ee', organization=organization)
    default_ee = get_default_execution_environment()
    assert default_ee.image == settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['image']
    assert default_ee.name == settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS[0]['name']


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
