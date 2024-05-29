import pytest

from rest_framework.exceptions import PermissionDenied
from awx.api.views import TeamDetail

from awx.api.views import immutablesharedfields
from awx.api.versioning import reverse
from awx.main.models import Organization
from django.test import override_settings


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
        [
            'admin_role',
            'member_role',
        ],
    )
    def test_prevent_assigning_member_to_organization(self, admin_user, post, role):
        orgA = Organization.objects.create(name='orgA')
        role = getattr(orgA, role)
        with override_settings(DIRECT_SHARED_RESOURCE_MANAGEMENT_ENABLED=False):
            resp = post(
                url=reverse('api:user_roles_list', kwargs={'pk': admin_user.id}),
                data={'id': role.id},
                user=admin_user,
                expect=403,
            )
        assert "You cannot assign user to an organization. Must be done via the platform ingress" in resp.data['msg']
