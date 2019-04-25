import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_user_role_view_access(rando, inventory, mocker, post):
    "Assure correct access method is called when assigning users new roles"
    mock_method = mocker.MagicMock(return_value=False)
    with mocker.patch('awx.main.access.UserRoleAttachAccess.can_add', mock_method):
        post(url=reverse('api:user_roles_list', kwargs={'pk': rando.pk}),
             data={"id": inventory.admin_role.pk}, user=rando, expect=403)
    mock_method.assert_called_once_with(obj_A=inventory.admin_role, obj_B=rando)


@pytest.mark.django_db
def test_role_user_view_access(rando, inventory, mocker, post):
    "Assure same call pattern is used when using the reverse URL"
    mock_method = mocker.MagicMock(return_value=False)
    inventory.read_role.members.add(rando)  # so parent read access is satisfied
    with mocker.patch('awx.main.access.UserRoleAttachAccess.can_add', mock_method):
        post(url=reverse('api:role_users_list', kwargs={'pk': inventory.admin_role.pk}),
             data={"id": rando.pk}, user=rando, expect=403)
    mock_method.assert_called_once_with(obj_A=inventory.admin_role, obj_B=rando)


@pytest.mark.django_db
def test_team_role_view_access(rando, team, inventory, mocker, post):
    "Assure correct access method is called when assigning teams new roles"
    team.admin_role.members.add(rando)
    mock_method = mocker.MagicMock(return_value=False)
    with mocker.patch('awx.main.access.RoleRoleAttachAccess.can_add', mock_method):
        post(url=reverse('api:team_roles_list', kwargs={'pk': team.pk}),
             data={"id": inventory.admin_role.pk}, user=rando, expect=403)
    mock_method.assert_called_once_with(obj_A=team.member_role, obj_B=inventory.admin_role)


@pytest.mark.django_db
def test_role_team_view_access(rando, team, inventory, mocker, post):
    """Assure that /role/N/teams/ enforces the same permission restrictions
    that /teams/N/roles/ does when assigning teams new roles"""
    role_pk = inventory.admin_role.pk
    mock_method = mocker.MagicMock(return_value=False)
    with mocker.patch('awx.main.access.RoleRoleAttachAccess.can_add', mock_method):
        post(url=reverse('api:role_teams_list', kwargs={'pk': role_pk}),
             data={"id": team.pk}, user=rando, expect=403)
    mock_method.assert_called_once_with(obj_A=team.member_role, obj_B=inventory.admin_role)


@pytest.mark.django_db
def test_org_associate_with_junk_data(rando, admin_user, organization, post):
    """
    Assure that post-hoc enforcement of auditor role
    will turn off if the action is an association
    """
    user_data = {'is_system_auditor': True, 'id': rando.pk}
    post(url=reverse('api:organization_users_list', kwargs={'pk': organization.pk}),
         data=user_data, expect=204, user=admin_user)
    # assure user is now an org member
    assert rando in organization.member_role
    # assure that this did not also make them a system auditor
    assert not rando.is_system_auditor


@pytest.mark.django_db
def test_sublist_create(org_admin, organization, post):
    post(
        url=reverse('api:organization_teams_list', kwargs={'pk': organization.pk}),
        data={'name': 'new team'},
        expect=201,
        user=org_admin
    )


@pytest.mark.django_db
def test_sublist_create_permission_denied(org_auditor, organization, post):
    post(
        url=reverse('api:organization_teams_list', kwargs={'pk': organization.pk}),
        data={'name': 'new team'},
        expect=403,
        user=org_auditor
    )
