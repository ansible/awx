import pytest

from awx.main.models import (ExecutionEnvironment)


@pytest.mark.django_db
def test_execution_environment_creation(execution_environment, organization):
    execution_env = ExecutionEnvironment.objects.create(
        name='Hello Environment', 
        image='', 
        organization=organization, 
        managed_by_tower=False, 
        credential=None,
        pull='missing'
    )
    assert type(execution_env) is type(execution_environment)
    assert execution_env.organization == organization
    assert execution_env.name == 'Hello Environment'
    assert execution_env.pull == 'missing'
