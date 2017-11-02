import pytest

from awx.main.access import (
    OauthApplicationAccess,
    OauthTokenAccess,
)
from awx.main.models import (
    Application,
    AccessToken,
)
from awx.api.versioning import reverse


@pytest.mark.django_db
class TestOAuthApplication:

    @pytest.mark.parametrize("user_for_access, can_access_list", [
        (0, [True, True, True, True]),
        (1, [False, True, True, False]),
        (2, [False, False, True, False]),
        (3, [False, False, False, True]),
    ])
    def test_can_read_change_delete(
        self, admin, org_admin, org_member, alice, user_for_access, can_access_list
    ):
        user_list = [admin, org_admin, org_member, alice]
        access = OauthApplicationAccess(user_list[user_for_access])
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=user,
                client_type='confidential', authorization_grant_type='password'
            )
            assert access.can_read(app) is can_access
            assert access.can_change(app, {}) is can_access
            assert access.can_delete(app) is can_access

    def test_superuser_can_always_create(self, admin, org_admin, org_member, alice):
        access = OauthApplicationAccess(admin)
        for user in [admin, org_admin, org_member, alice]:
            assert access.can_add({
                'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                'authorization_grant_type': 'password'
            })

    def test_normal_user_cannot_create(self, admin, org_admin, org_member, alice):
        for access_user in [org_member, alice]:
            access = OauthApplicationAccess(access_user)
            for user in [admin, org_admin, org_member, alice]:
                assert not access.can_add({
                    'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                    'authorization_grant_type': 'password'
                })

    def test_org_admin_can_create_in_org(self, admin, org_admin, org_member, alice):
        access = OauthApplicationAccess(org_admin)
        for user in [admin, alice]:
            assert not access.can_add({
                'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                'authorization_grant_type': 'password'
            })
        for user in [org_admin, org_member]:
            assert access.can_add({
                'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                'authorization_grant_type': 'password'
            })


@pytest.mark.django_db
class TestOAuthToken:

    @pytest.mark.parametrize("user_for_access, can_access_list", [
        (0, [True, True, True, True]),
        (1, [False, True, True, False]),
        (2, [False, False, True, False]),
        (3, [False, False, False, True]),
    ])
    def test_can_read_change_delete(
        self, post, admin, org_admin, org_member, alice, user_for_access, can_access_list
    ):
        user_list = [admin, org_admin, org_member, alice]
        access = OauthTokenAccess(user_list[user_for_access])
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=user,
                client_type='confidential', authorization_grant_type='password'
            )
            response = post(
                reverse('api:user_me_oauth_application_token_list', kwargs={'pk': app.pk}),
                {'scope': 'read'}, admin, expect=201
            )
            token = AccessToken.objects.get(token=response.data['token'])
            assert access.can_read(token) is can_access
            assert access.can_change(token, {}) is can_access
            assert access.can_delete(token) is can_access

    @pytest.mark.parametrize("user_for_access, can_access_list", [
        (0, [True, True, True, True]),
        (1, [False, True, True, False]),
        (2, [False, False, True, False]),
        (3, [False, False, False, True]),
    ])
    def test_can_create(
        self, post, admin, org_admin, org_member, alice, user_for_access, can_access_list
    ):
        user_list = [admin, org_admin, org_member, alice]
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=user,
                client_type='confidential', authorization_grant_type='password'
            )
            post(
                reverse('api:user_me_oauth_application_token_list', kwargs={'pk': app.pk}),
                {'scope': 'read'}, user_list[user_for_access], expect=201 if can_access else 403
            )
