import pytest

from django.contrib.contenttypes.models import ContentType

from awx.main.access import ExecutionEnvironmentAccess
from awx.main.models import ExecutionEnvironment, Organization, Team
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
        permissions=['add_executionenvironment', 'change_executionenvironment', 'delete_executionenvironment', 'view_organization'],
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


@pytest.fixture
def check_user_capabilities(get, setup_managed_roles):
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


# ___ begin tests ___


@pytest.mark.django_db
def test_any_user_can_view_global_ee(control_plane_execution_environment, rando):
    assert ExecutionEnvironmentAccess(rando).can_read(control_plane_execution_environment)


@pytest.mark.django_db
def test_managed_ee_not_assignable(control_plane_execution_environment, ee_rd, rando, admin_user, post):
    url = django_reverse('roleuserassignment-list')
    r = post(url, {'role_definition': ee_rd.pk, 'user': rando.id, 'object_id': control_plane_execution_environment.pk}, user=admin_user, expect=400)
    assert 'Can not assign object roles to managed Execution Environment' in str(r.data)


@pytest.mark.django_db
def test_org_member_required_for_assignment(org_ee, ee_rd, rando, admin_user, post):
    url = django_reverse('roleuserassignment-list')
    r = post(url, {'role_definition': ee_rd.pk, 'user': rando.id, 'object_id': org_ee.pk}, user=admin_user, expect=400)
    assert 'User must have view permission to Execution Environment organization' in str(r.data)


@pytest.mark.django_db
def test_team_can_have_permission(org_ee, ee_rd, rando, admin_user, post):
    org2 = Organization.objects.create(name='a different team')
    team = Team.objects.create(name='a team', organization=org2)
    team.member_role.members.add(rando)
    assert org_ee not in ExecutionEnvironmentAccess(rando).get_queryset()  # user can not view the EE

    url = django_reverse('roleteamassignment-list')

    # can give object roles to the team now
    post(url, {'role_definition': ee_rd.pk, 'team': team.id, 'object_id': org_ee.pk}, user=admin_user, expect=201)
    assert rando.has_obj_perm(org_ee, 'change')
    assert org_ee in ExecutionEnvironmentAccess(rando).get_queryset()  # user can view the EE now


@pytest.mark.django_db
def test_give_object_permission_to_ee(setup_managed_roles, org_ee, ee_rd, org_member, check_user_capabilities):
    access = ExecutionEnvironmentAccess(org_member)
    assert access.can_read(org_ee)  # by virtue of being an org member
    assert not access.can_change(org_ee, {'name': 'new'})
    check_user_capabilities(org_member, org_ee, {'edit': False, 'delete': False, 'copy': False})

    ee_rd.give_permission(org_member, org_ee)
    assert access.can_change(org_ee, {'name': 'new', 'organization': org_ee.organization.id})

    check_user_capabilities(org_member, org_ee, {'edit': True, 'delete': True, 'copy': False})


@pytest.mark.django_db
def test_need_related_organization_access(org_ee, ee_rd, org_member):
    org2 = Organization.objects.create(name='another organization')
    ee_rd.give_permission(org_member, org_ee)
    org2.member_role.members.add(org_member)
    access = ExecutionEnvironmentAccess(org_member)
    assert access.can_change(org_ee, {'name': 'new', 'organization': org_ee.organization})
    assert access.can_change(org_ee, {'name': 'new', 'organization': org_ee.organization.id})
    assert not access.can_change(org_ee, {'name': 'new', 'organization': org2.id})
    assert not access.can_change(org_ee, {'name': 'new', 'organization': org2})

    # User can make the change if they have relevant permission to the new organization
    org_ee.organization.execution_environment_admin_role.members.add(org_member)
    org2.execution_environment_admin_role.members.add(org_member)
    assert access.can_change(org_ee, {'name': 'new', 'organization': org2.id})
    assert access.can_change(org_ee, {'name': 'new', 'organization': org2})


@pytest.mark.django_db
@pytest.mark.parametrize('style', ['new', 'old'])
def test_give_org_permission_to_ee(setup_managed_roles, org_ee, organization, org_member, check_user_capabilities, style, org_ee_rd):
    access = ExecutionEnvironmentAccess(org_member)
    assert not access.can_change(org_ee, {'name': 'new'})
    check_user_capabilities(org_member, org_ee, {'edit': False, 'delete': False, 'copy': False})

    if style == 'new':
        org_ee_rd.give_permission(org_member, organization)
        assert org_member.has_obj_perm(org_ee.organization, 'add_executionenvironment')  # sanity
    else:
        organization.execution_environment_admin_role.members.add(org_member)

    assert access.can_change(org_ee, {'name': 'new', 'organization': organization.id})
    check_user_capabilities(org_member, org_ee, {'edit': True, 'delete': True, 'copy': True})

    # Extra check, user can not remove the EE from the organization
    assert not access.can_change(org_ee, {'name': 'new', 'organization': None})
