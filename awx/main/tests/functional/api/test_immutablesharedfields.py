import pytest

from awx.api.versioning import reverse
from awx.main.models import Organization
from django.test.utils import override_settings


@pytest.mark.django_db
class TestImmutableSharedFields:
    def test_create_raises_permission_denied(self, admin_user, post):
        orgA = Organization.objects.create(name='orgA')
        with override_settings(DIRECT_SHARED_RESOURCE_MANAGEMENT_ENABLED=False):
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
        with override_settings(DIRECT_SHARED_RESOURCE_MANAGEMENT_ENABLED=False):
            resp = delete(
                url=reverse('api:team_detail', kwargs={'pk': team.id}),
                user=admin_user,
                expect=403,
            )
        assert "Deletion of this resource is not allowed" in resp.data['detail']

    def test_perform_update(self, admin_user, patch):
        orgA = Organization.objects.create(name='orgA')
        team = orgA.teams.create(name='teamA')
        # allow patching non-shared fields
        with override_settings(DIRECT_SHARED_RESOURCE_MANAGEMENT_ENABLED=False):
            patch(
                url=reverse('api:team_detail', kwargs={'pk': team.id}),
                data={"description": "can change this field"},
                user=admin_user,
                expect=200,
            )
        orgB = Organization.objects.create(name='orgB')
        # prevent patching shared fields
        with override_settings(DIRECT_SHARED_RESOURCE_MANAGEMENT_ENABLED=False):
            resp = patch(url=reverse('api:team_detail', kwargs={'pk': team.id}), data={"organization": orgB.id}, user=admin_user, expect=403)
        assert "Cannot change shared field" in resp.data['organization']

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
        with override_settings(DIRECT_SHARED_RESOURCE_MANAGEMENT_ENABLED=False):
            resp = post(
                url=reverse('api:user_roles_list', kwargs={'pk': admin_user.id}),
                data={'id': role.id},
                user=admin_user,
                expect=403,
            )
        assert f"Cannot modify user membership to {resource}. Must be done via the platform ingress" in resp.data['msg']
