import pytest

from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
def test_roles_to_not_create(setup_managed_roles):
    assert RoleDefinition.objects.filter(name='Organization Admin').count() == 1

    SHOULD_NOT_EXIST = ('Organization Organization Admin', 'Organization Team Admin', 'Organization InstanceGroup Admin')

    bad_rds = RoleDefinition.objects.filter(name__in=SHOULD_NOT_EXIST)
    if bad_rds.exists():
        raise Exception(f'Found RoleDefinitions that should not exist: {list(bad_rds.values_list('name', flat=True))}')


@pytest.mark.django_db
def test_project_update_role(setup_managed_roles):
    assert RoleDefinition.objects.filter(name='Project Update').count() == 1
