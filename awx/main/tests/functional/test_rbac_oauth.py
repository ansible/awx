import pytest

from awx.main.access import (
    OAuth2ApplicationAccess,
    OAuth2TokenAccess,
)
from awx.main.models.oauth import (
    OAuth2Application as Application,
    OAuth2AccessToken as AccessToken,
)
from awx.api.versioning import reverse


@pytest.mark.django_db
class TestOAuth2Application:
        
        @pytest.mark.parametrize("user_for_access, can_access_list", [
            (0, [True, True]),
            (1, [True, True]),
            (2, [True, True]),
            (3, [False, False]),
        ])
        def test_can_read(
            self, admin, org_admin, org_member, alice, user_for_access, can_access_list, organization
        ):
            user_list = [admin, org_admin, org_member, alice]
            access = OAuth2ApplicationAccess(user_list[user_for_access])
            app_creation_user_list = [admin, org_admin]
            for user, can_access in zip(app_creation_user_list, can_access_list):
                app = Application.objects.create(
                    name='test app for {}'.format(user.username), user=user,
                    client_type='confidential', authorization_grant_type='password', organization=organization
                )
                assert access.can_read(app) is can_access    
    
    
        @pytest.mark.parametrize("user_for_access, can_access_list", [
            (0, [True, True]),
            (1, [True, True]),
            (2, [False, False]),
            (3, [False, False]),
        ])
        def test_can_edit_delete(
            self, admin, org_admin, org_member, alice, user_for_access, can_access_list, organization
        ):
            organization.admin_role.members.add(org_admin)
            organization.member_role.members.add(org_member)
            user_list = [admin, org_admin, org_member, alice]
            access = OAuth2ApplicationAccess(user_list[user_for_access])
            app_creation_user_list = [admin, org_admin]
            for user, can_access in zip(app_creation_user_list, can_access_list):
                app = Application.objects.create(
                    name='test app for {}'.format(user.username), user=user,
                    client_type='confidential', authorization_grant_type='password', organization=organization
                )
                assert access.can_change(app, {}) is can_access
                assert access.can_delete(app) is can_access
    
    
    
    

        def test_superuser_can_always_create(self, admin, org_admin, org_member, alice):
            access = OAuth2ApplicationAccess(admin)
            for user in [admin, org_admin, org_member, alice]:
                assert access.can_add({
                    'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                    'authorization_grant_type': 'password', 'organization': 1
                })
        
        def test_normal_user_cannot_create(self, admin, org_admin, org_member, alice):
            for access_user in [org_member, alice]:
                access = OAuth2ApplicationAccess(access_user)
                for user in [admin, org_admin, org_member, alice]:
                    assert not access.can_add({
                        'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                        'authorization_grant_type': 'password', 'organization': 1
                    })


@pytest.mark.django_db
class TestOAuth2Token:

    @pytest.mark.skip(reason="Needs Update - CA")
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
        access = OAuth2TokenAccess(user_list[user_for_access])
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=user,
                client_type='confidential', authorization_grant_type='password'
            )
            response = post(
                reverse('api:o_auth2_application_token_list', kwargs={'pk': app.pk}),
                {'scope': 'read'}, admin, expect=201
            )
            token = AccessToken.objects.get(token=response.data['token'])
            
            assert access.can_read(token) is can_access                       # TODO: fix this test
            assert access.can_change(token, {}) is can_access
            assert access.can_delete(token) is can_access

    @pytest.mark.parametrize("user_for_access, can_access_list", [
        (0, [True, True]),
        (1, [True, True]),
        (2, [True, True]),
        (3, [False, False]),
    ])
    def test_can_create(
        self, post, admin, org_admin, org_member, alice, user_for_access, can_access_list, organization
    ):
        user_list = [admin, org_admin, org_member, alice]
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=user,
                client_type='confidential', authorization_grant_type='password', organization=organization
            )
            post(
                reverse('api:o_auth2_application_token_list', kwargs={'pk': app.pk}),
                {'scope': 'read'}, user_list[user_for_access], expect=201 if can_access else 403
            )
