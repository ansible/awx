import pytest

from awx.api.versioning import reverse
from awx.main.models import Organization


@pytest.mark.django_db
class TestImmutableSharedFields:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.ALLOW_LOCAL_RESOURCE_MANAGEMENT = False

    def test_create_raises_permission_denied(self, admin_user, post):
        orgA = Organization.objects.create(name='orgA')
        resp = post(
            url=reverse('api:team_list'),
            data={'name': 'teamA', 'organization': orgA.id},
            user=admin_user,
            expect=403,
        )
        assert "Creation of this resource is not allowed" in resp.data['detail']

    def test_perform_delete_raises_permission_denied(self, admin_user, delete):
        orgA = Organization.objects.create(name='orgA')
        team = orgA.teams.create(name='teamA')
        resp = delete(
            url=reverse('api:team_detail', kwargs={'pk': team.id}),
            user=admin_user,
            expect=403,
        )
        assert "Deletion of this resource is not allowed" in resp.data['detail']

    def test_perform_update(self, admin_user, patch):
        orgA = Organization.objects.create(name='orgA')
        # allow patching non-shared fields
        patch(
            url=reverse('api:organization_detail', kwargs={'pk': orgA.id}),
            data={"max_hosts": 76},
            user=admin_user,
            expect=200,
        )
        # prevent patching shared fields
        resp = patch(url=reverse('api:organization_detail', kwargs={'pk': orgA.id}), data={"name": "orgB"}, user=admin_user, expect=403)
        assert "Cannot change shared field" in resp.data['name']

    @pytest.mark.parametrize(
        'role',
        ['admin_role', 'member_role'],
    )
    @pytest.mark.parametrize('resource', ['organization', 'team'])
    def test_prevent_assigning_member_to_organization_or_team(self, admin_user, post, resource, role):
        orgA = Organization.objects.create(name='orgA')
        if resource == 'organization':
            role = getattr(orgA, role)
        elif resource == 'team':
            teamA = orgA.teams.create(name='teamA')
            role = getattr(teamA, role)
        resp = post(
            url=reverse('api:user_roles_list', kwargs={'pk': admin_user.id}),
            data={'id': role.id},
            user=admin_user,
            expect=403,
        )
        assert f"Cannot directly modify user membership to {resource}." in resp.data['msg']
