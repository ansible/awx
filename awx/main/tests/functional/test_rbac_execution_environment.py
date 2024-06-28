import pytest

from django.contrib.contenttypes.models import ContentType

from awx.main.access import ExecutionEnvironmentAccess
from awx.main.models import ExecutionEnvironment, Organization
from awx.main.models.rbac import get_role_codenames

from awx.api.versioning import reverse
from django.urls import reverse as django_reverse

from ansible_base.rbac.models import RoleDefinition


@pytest.fixture
def ee_rd():
    return RoleDefinition.objects.create_from_permissions(
        name='EE object admin',
        permissions=['change_executionenvironment', 'delete_executionenvironment'],
        content_type=ContentType.objects.get_for_model(ExecutionEnvironment),
    )


@pytest.fixture
def org_ee_rd():
    return RoleDefinition.objects.create_from_permissions(
        name='EE org admin',
        permissions=['change_executionenvironment', 'delete_executionenvironment', 'view_organization'],
        content_type=ContentType.objects.get_for_model(Organization),
    )


@pytest.mark.django_db
def test_old_ee_role_maps_to_correct_permissions(organization):
    assert set(get_role_codenames(organization.execution_environment_admin_role)) == {
        'view_organization',
        'add_executionenvironment',
        'change_executionenvironment',
        'delete_executionenvironment',
    }


@pytest.fixture
def org_ee(organization):
    return ExecutionEnvironment.objects.create(name='some user ee', organization=organization)


@pytest.mark.django_db
def test_managed_ee_not_assignable(control_plane_execution_environment, ee_rd, rando, admin_user, post):
    url = django_reverse('roleuserassignment-list')
    r = post(url, {'role_definition': ee_rd.pk, 'user': rando.id, 'object_id': control_plane_execution_environment.pk}, user=admin_user, expect=400)
    assert 'foo' in str(r.data)


@pytest.mark.django_db
def test_org_member_required_for_assignment(org_ee, ee_rd, rando, admin_user, post):
    url = django_reverse('roleuserassignment-list')
    r = post(url, {'role_definition': ee_rd.pk, 'user': rando.id, 'object_id': org_ee.pk}, user=admin_user, expect=400)
    assert 'foo' in str(r.data)


@pytest.fixture
def check_user_capabilities(get):
    def _rf(user, obj, expected):
        url = reverse('api:execution_environment_list')
        r = get(url, user=user, expect=200)
        for item in r.data['results']:
            if item['id'] == obj.pk:
                assert expected == item['summary_fields']['user_capabilities']
                break
        else:
            raise RuntimeError(f'Could not find expected object ({obj}) in EE list result: {r.data}')

    return _rf


@pytest.mark.django_db
def test_give_object_permission_to_ee(org_ee, ee_rd, org_member, check_user_capabilities):
    access = ExecutionEnvironmentAccess(org_member)
    assert access.can_read(org_ee)  # by virtue of being an org member
    assert not access.can_change(org_ee, {'name': 'new'})
    check_user_capabilities(org_member, org_ee, {'edit': False, 'delete': False, 'copy': False})

    ee_rd.give_permission(org_member, org_ee)
    assert access.can_change(org_ee, {'name': 'new'})

    check_user_capabilities(org_member, org_ee, {'edit': True, 'delete': True, 'copy': False})


@pytest.mark.django_db
def test_give_org_permission_to_ee(org_ee, organization, org_member, check_user_capabilities):
    access = ExecutionEnvironmentAccess(org_member)
    assert not access.can_change(org_ee, {'name': 'new'})
    check_user_capabilities(org_member, org_ee, {'edit': False, 'delete': False, 'copy': False})

    # NOTE: user_capabilities has problem with org_ee_rd.give_permission(org_member, organization)
    organization.execution_environment_admin_role.members.add(org_member)

    assert access.can_change(org_ee, {'name': 'new'})
    check_user_capabilities(org_member, org_ee, {'edit': True, 'delete': True, 'copy': True})
