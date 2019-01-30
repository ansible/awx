import pytest

from awx.main.access import (
    OAuth2ApplicationAccess,
    OAuth2TokenAccess,
    ActivityStreamAccess,
)
from awx.main.models.oauth import (
    OAuth2Application as Application,
    OAuth2AccessToken as AccessToken,
)
from awx.main.models import ActivityStream
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

    def test_admin_only_can_read(self, user, organization):
        user = user('org-admin', False)
        organization.admin_role.members.add(user)
        access = OAuth2ApplicationAccess(user)
        app = Application.objects.create(
            name='test app for {}'.format(user.username), user=user,
            client_type='confidential', authorization_grant_type='password', organization=organization
        )
        assert access.can_read(app) is True

    def test_app_activity_stream(self, org_admin, alice, organization):
        app = Application.objects.create(
            name='test app for {}'.format(org_admin.username), user=org_admin,
            client_type='confidential', authorization_grant_type='password', organization=organization
        )
        access = OAuth2ApplicationAccess(org_admin)
        assert access.can_read(app) is True
        access = ActivityStreamAccess(org_admin)
        activity_stream = ActivityStream.objects.filter(o_auth2_application=app).latest('pk')
        assert access.can_read(activity_stream) is True
        access = ActivityStreamAccess(alice)
        assert access.can_read(app) is False
        assert access.can_read(activity_stream) is False
        

    def test_token_activity_stream(self, org_admin, alice, organization, post):
        app = Application.objects.create(
            name='test app for {}'.format(org_admin.username), user=org_admin,
            client_type='confidential', authorization_grant_type='password', organization=organization
        )
        response = post(
            reverse('api:o_auth2_application_token_list', kwargs={'pk': app.pk}),
            {'scope': 'read'}, org_admin, expect=201
        )
        token = AccessToken.objects.get(token=response.data['token'])
        access = OAuth2ApplicationAccess(org_admin)
        assert access.can_read(app) is True
        access = ActivityStreamAccess(org_admin)
        activity_stream = ActivityStream.objects.filter(o_auth2_access_token=token).latest('pk')
        assert access.can_read(activity_stream) is True
        access = ActivityStreamAccess(alice)
        assert access.can_read(token) is False
        assert access.can_read(activity_stream) is False
        


    def test_can_edit_delete_app_org_admin(
        self, admin, org_admin, org_member, alice, organization
    ):
        user_list = [admin, org_admin, org_member, alice]
        can_access_list = [True, True, False, False]
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=org_admin,
                client_type='confidential', authorization_grant_type='password', organization=organization
            )
            access = OAuth2ApplicationAccess(user)
            assert access.can_change(app, {}) is can_access
            assert access.can_delete(app) is can_access
            
            
    def test_can_edit_delete_app_admin(
        self, admin, org_admin, org_member, alice, organization
    ):
        user_list = [admin, org_admin, org_member, alice]
        can_access_list = [True, True, False, False]
        for user, can_access in zip(user_list, can_access_list):
            app = Application.objects.create(
                name='test app for {}'.format(user.username), user=admin,
                client_type='confidential', authorization_grant_type='password', organization=organization
            )
            access = OAuth2ApplicationAccess(user)
            assert access.can_change(app, {}) is can_access
            assert access.can_delete(app) is can_access


    def test_superuser_can_always_create(self, admin, org_admin, org_member, alice, organization):
        access = OAuth2ApplicationAccess(admin)
        for user in [admin, org_admin, org_member, alice]:
            assert access.can_add({
                'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                'authorization_grant_type': 'password', 'organization': organization.id
            })
    
    def test_normal_user_cannot_create(self, admin, org_admin, org_member, alice, organization):
        for access_user in [org_member, alice]:
            access = OAuth2ApplicationAccess(access_user)
            for user in [admin, org_admin, org_member, alice]:
                assert not access.can_add({
                    'name': 'test app', 'user': user.pk, 'client_type': 'confidential',
                    'authorization_grant_type': 'password', 'organization': organization.id
                })


@pytest.mark.django_db
class TestOAuth2Token:
        
    def test_can_read_change_delete_app_token(
        self, post, admin, org_admin, org_member, alice, organization
    ):
        user_list = [admin, org_admin, org_member, alice]
        can_access_list = [True, True, False, False]
        app = Application.objects.create(
            name='test app for {}'.format(admin.username), user=admin,
            client_type='confidential', authorization_grant_type='password',
            organization=organization
        )
        response = post(
            reverse('api:o_auth2_application_token_list', kwargs={'pk': app.pk}),
            {'scope': 'read'}, admin, expect=201
        )
        for user, can_access in zip(user_list, can_access_list):
            token = AccessToken.objects.get(token=response.data['token'])
            access = OAuth2TokenAccess(user)
            assert access.can_read(token) is can_access
            assert access.can_change(token, {}) is can_access
            assert access.can_delete(token) is can_access


    def test_auditor_can_read(
        self, post, admin, org_admin, org_member, alice, system_auditor, organization
    ):
        user_list = [admin, org_admin, org_member]
        can_access_list = [True, True, True]
        cannot_access_list = [False, False, False]
        app = Application.objects.create(
            name='test app for {}'.format(admin.username), user=admin,
            client_type='confidential', authorization_grant_type='password',
            organization=organization
        )
        for user, can_access, cannot_access in zip(user_list, can_access_list, cannot_access_list):
            response = post(
                reverse('api:o_auth2_application_token_list', kwargs={'pk': app.pk}),
                {'scope': 'read'}, user, expect=201
            )
            token = AccessToken.objects.get(token=response.data['token'])
            access = OAuth2TokenAccess(system_auditor)
            assert access.can_read(token) is can_access
            assert access.can_change(token, {}) is cannot_access
            assert access.can_delete(token) is cannot_access
            
    def test_user_auditor_can_change(
        self, post, org_member, org_admin, system_auditor, organization
    ):    
        app = Application.objects.create(
            name='test app for {}'.format(org_admin.username), user=org_admin,
            client_type='confidential', authorization_grant_type='password',
            organization=organization
        )
        response = post(
            reverse('api:o_auth2_application_token_list', kwargs={'pk': app.pk}),
            {'scope': 'read'}, org_member, expect=201
        )
        token = AccessToken.objects.get(token=response.data['token'])
        access = OAuth2TokenAccess(system_auditor)
        assert access.can_read(token) is True
        assert access.can_change(token, {}) is False
        assert access.can_delete(token) is False
        dual_user = system_auditor
        organization.admin_role.members.add(dual_user)
        access = OAuth2TokenAccess(dual_user)
        assert access.can_read(token) is True
        assert access.can_change(token, {}) is True
        assert access.can_delete(token) is True
        
            
            
    def test_can_read_change_delete_personal_token_org_member(
        self, post, admin, org_admin, org_member, alice
    ):
        # Tests who can read a token created by an org-member
        user_list = [admin, org_admin, org_member, alice]
        can_access_list = [True, False, True, False]
        response = post(
            reverse('api:user_personal_token_list', kwargs={'pk': org_member.pk}),
            {'scope': 'read'}, org_member, expect=201
        )
        token = AccessToken.objects.get(token=response.data['token'])
        for user, can_access in zip(user_list, can_access_list):
            access = OAuth2TokenAccess(user)
            assert access.can_read(token) is can_access
            assert access.can_change(token, {}) is can_access
            assert access.can_delete(token) is can_access
    
            
    def test_can_read_personal_token_creator(
        self, post, admin, org_admin, org_member, alice
    ):
        # Tests the token's creator can read their tokens
        user_list = [admin, org_admin, org_member, alice]
        can_access_list = [True, True, True, True]

        for user, can_access in zip(user_list, can_access_list):
            response = post(
                reverse('api:user_personal_token_list', kwargs={'pk': user.pk}),
                {'scope': 'read', 'application':None}, user, expect=201
            )
            token = AccessToken.objects.get(token=response.data['token'])
            access = OAuth2TokenAccess(user)
            assert access.can_read(token) is can_access
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

