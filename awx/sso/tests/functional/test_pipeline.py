
import pytest
import re
from unittest import mock

from awx.sso.pipeline import (
    update_user_orgs,
    update_user_teams,
    update_user_orgs_by_saml_attr,
    update_user_teams_by_saml_attr,
)

from awx.main.models import (
    User,
    Team,
    Organization
)


@pytest.fixture
def users():
    u1 = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com')
    u2 = User.objects.create(username='user2@foo.com', last_name='foo', first_name='bar', email='user2@foo.com')
    u3 = User.objects.create(username='user3@foo.com', last_name='foo', first_name='bar', email='user3@foo.com')
    return (u1, u2, u3)


@pytest.mark.django_db
class TestSAMLMap():

    @pytest.fixture
    def backend(self):
        class Backend:
            s = {
                'ORGANIZATION_MAP': {
                    'Default': {
                        'remove': True,
                        'admins': 'foobar',
                        'remove_admins': True,
                        'users': 'foo',
                        'remove_users': True,
                    }
                },
                'TEAM_MAP': {
                    'Blue': {
                        'organization': 'Default',
                        'remove': True,
                        'users': '',
                    },
                    'Red': {
                        'organization': 'Default',
                        'remove': True,
                        'users': '',
                    }
                }
            }

            def setting(self, key):
                return self.s[key]

        return Backend()

    @pytest.fixture
    def org(self):
        return Organization.objects.create(name="Default")

    def test_update_user_orgs(self, org, backend, users):
        u1, u2, u3 = users

        # Test user membership logic with regular expressions
        backend.setting('ORGANIZATION_MAP')['Default']['admins'] = re.compile('.*')
        backend.setting('ORGANIZATION_MAP')['Default']['users'] = re.compile('.*')

        update_user_orgs(backend, None, u1)
        update_user_orgs(backend, None, u2)
        update_user_orgs(backend, None, u3)

        assert org.admin_role.members.count() == 3
        assert org.member_role.members.count() == 3

        # Test remove feature enabled
        backend.setting('ORGANIZATION_MAP')['Default']['admins'] = ''
        backend.setting('ORGANIZATION_MAP')['Default']['users'] = ''
        backend.setting('ORGANIZATION_MAP')['Default']['remove_admins'] = True
        backend.setting('ORGANIZATION_MAP')['Default']['remove_users'] = True
        update_user_orgs(backend, None, u1)

        assert org.admin_role.members.count() == 2
        assert org.member_role.members.count() == 2

        # Test remove feature disabled
        backend.setting('ORGANIZATION_MAP')['Default']['remove_admins'] = False
        backend.setting('ORGANIZATION_MAP')['Default']['remove_users'] = False
        update_user_orgs(backend, None, u2)

        assert org.admin_role.members.count() == 2
        assert org.member_role.members.count() == 2

    def test_update_user_teams(self, backend, users):
        u1, u2, u3 = users

        # Test user membership logic with regular expressions
        backend.setting('TEAM_MAP')['Blue']['users'] = re.compile('.*')
        backend.setting('TEAM_MAP')['Red']['users'] = re.compile('.*')

        update_user_teams(backend, None, u1)
        update_user_teams(backend, None, u2)
        update_user_teams(backend, None, u3)

        assert Team.objects.get(name="Red").member_role.members.count() == 3
        assert Team.objects.get(name="Blue").member_role.members.count() == 3

        # Test remove feature enabled
        backend.setting('TEAM_MAP')['Blue']['remove'] = True
        backend.setting('TEAM_MAP')['Red']['remove'] = True
        backend.setting('TEAM_MAP')['Blue']['users'] = ''
        backend.setting('TEAM_MAP')['Red']['users'] = ''

        update_user_teams(backend, None, u1)

        assert Team.objects.get(name="Red").member_role.members.count() == 2
        assert Team.objects.get(name="Blue").member_role.members.count() == 2

        # Test remove feature disabled
        backend.setting('TEAM_MAP')['Blue']['remove'] = False
        backend.setting('TEAM_MAP')['Red']['remove'] = False

        update_user_teams(backend, None, u2)

        assert Team.objects.get(name="Red").member_role.members.count() == 2
        assert Team.objects.get(name="Blue").member_role.members.count() == 2


@pytest.mark.django_db
class TestSAMLAttr():

    @pytest.fixture
    def kwargs(self):
        return {
            'username': u'cmeyers@redhat.com',
            'uid': 'idp:cmeyers@redhat.com',
            'request': {
                u'SAMLResponse': [],
                u'RelayState': [u'idp']
            },
            'is_new': False,
            'response': {
                'session_index': '_0728f0e0-b766-0135-75fa-02842b07c044',
                'idp_name': u'idp',
                'attributes': {
                    'memberOf': ['Default1', 'Default2'],
                    'admins': ['Default3'],
                    'auditors': ['Default4'],
                    'groups': ['Blue', 'Red'],
                    'User.email': ['cmeyers@redhat.com'],
                    'User.LastName': ['Meyers'],
                    'name_id': 'cmeyers@redhat.com',
                    'User.FirstName': ['Chris'],
                    'PersonImmutableID': []
                }
            },
            #'social': <UserSocialAuth: cmeyers@redhat.com>,
            'social': None,
            #'strategy': <awx.sso.strategies.django_strategy.AWXDjangoStrategy object at 0x8523a10>,
            'strategy': None,
            'new_association': False
        }

    @pytest.fixture
    def orgs(self):
        o1 = Organization.objects.create(name='Default1')
        o2 = Organization.objects.create(name='Default2')
        o3 = Organization.objects.create(name='Default3')
        return (o1, o2, o3)

    @pytest.fixture
    def mock_settings(self, request):
        fixture_args = request.node.get_closest_marker('fixture_args')
        if fixture_args and 'autocreate' in fixture_args.kwargs:
            autocreate = fixture_args.kwargs['autocreate']
        else:
            autocreate = True

        class MockSettings():
            SAML_AUTO_CREATE_OBJECTS = autocreate
            SOCIAL_AUTH_SAML_ORGANIZATION_ATTR = {
                'saml_attr': 'memberOf',
                'saml_admin_attr': 'admins',
                'saml_auditor_attr': 'auditors',
                'remove': True,
                'remove_admins': True,
            }
            SOCIAL_AUTH_SAML_TEAM_ATTR = {
                'saml_attr': 'groups',
                'remove': True,
                'team_org_map': [
                    {'team': 'Blue', 'organization': 'Default1'},
                    {'team': 'Blue', 'organization': 'Default2'},
                    {'team': 'Blue', 'organization': 'Default3'},
                    {'team': 'Red', 'organization': 'Default1'},
                    {'team': 'Green', 'organization': 'Default1'},
                    {'team': 'Green', 'organization': 'Default3'},
                    {
                        'team': 'Yellow', 'team_alias': 'Yellow_Alias',
                        'organization': 'Default4', 'organization_alias': 'Default4_Alias'
                    },
                ]
            }
        return MockSettings()

    def test_update_user_orgs_by_saml_attr(self, orgs, users, kwargs, mock_settings):
        with mock.patch('django.conf.settings', mock_settings):
            o1, o2, o3 = orgs
            u1, u2, u3 = users

            # Test getting orgs from attribute
            update_user_orgs_by_saml_attr(None, None, u1, **kwargs)
            update_user_orgs_by_saml_attr(None, None, u2, **kwargs)
            update_user_orgs_by_saml_attr(None, None, u3, **kwargs)

            assert o1.member_role.members.count() == 3
            assert o2.member_role.members.count() == 3
            assert o3.member_role.members.count() == 0

            # Test remove logic enabled
            kwargs['response']['attributes']['memberOf'] = ['Default3']

            update_user_orgs_by_saml_attr(None, None, u1, **kwargs)

            assert o1.member_role.members.count() == 2
            assert o2.member_role.members.count() == 2
            assert o3.member_role.members.count() == 1

            # Test remove logic disabled
            mock_settings.SOCIAL_AUTH_SAML_ORGANIZATION_ATTR['remove'] = False
            kwargs['response']['attributes']['memberOf'] = ['Default1', 'Default2']

            update_user_orgs_by_saml_attr(None, None, u1, **kwargs)

            assert o1.member_role.members.count() == 3
            assert o2.member_role.members.count() == 3
            assert o3.member_role.members.count() == 1

    def test_update_user_teams_by_saml_attr(self, orgs, users, kwargs, mock_settings):
        with mock.patch('django.conf.settings', mock_settings):
            o1, o2, o3 = orgs
            u1, u2, u3 = users

            # Test getting teams from attribute with team->org mapping

            kwargs['response']['attributes']['groups'] = ['Blue', 'Red', 'Green']

            # Ensure basic functionality
            update_user_teams_by_saml_attr(None, None, u1, **kwargs)
            update_user_teams_by_saml_attr(None, None, u2, **kwargs)
            update_user_teams_by_saml_attr(None, None, u3, **kwargs)

            assert Team.objects.get(name='Blue', organization__name='Default1').member_role.members.count() == 3
            assert Team.objects.get(name='Blue', organization__name='Default2').member_role.members.count() == 3
            assert Team.objects.get(name='Blue', organization__name='Default3').member_role.members.count() == 3

            assert Team.objects.get(name='Red', organization__name='Default1').member_role.members.count() == 3

            assert Team.objects.get(name='Green', organization__name='Default1').member_role.members.count() == 3
            assert Team.objects.get(name='Green', organization__name='Default3').member_role.members.count() == 3

            # Test remove logic
            kwargs['response']['attributes']['groups'] = ['Green']
            update_user_teams_by_saml_attr(None, None, u1, **kwargs)
            update_user_teams_by_saml_attr(None, None, u2, **kwargs)
            update_user_teams_by_saml_attr(None, None, u3, **kwargs)

            assert Team.objects.get(name='Blue', organization__name='Default1').member_role.members.count() == 0
            assert Team.objects.get(name='Blue', organization__name='Default2').member_role.members.count() == 0
            assert Team.objects.get(name='Blue', organization__name='Default3').member_role.members.count() == 0

            assert Team.objects.get(name='Red', organization__name='Default1').member_role.members.count() == 0

            assert Team.objects.get(name='Green', organization__name='Default1').member_role.members.count() == 3
            assert Team.objects.get(name='Green', organization__name='Default3').member_role.members.count() == 3

            # Test remove logic disabled
            mock_settings.SOCIAL_AUTH_SAML_TEAM_ATTR['remove'] = False
            kwargs['response']['attributes']['groups'] = ['Blue']

            update_user_teams_by_saml_attr(None, None, u1, **kwargs)
            update_user_teams_by_saml_attr(None, None, u2, **kwargs)
            update_user_teams_by_saml_attr(None, None, u3, **kwargs)

            assert Team.objects.get(name='Blue', organization__name='Default1').member_role.members.count() == 3
            assert Team.objects.get(name='Blue', organization__name='Default2').member_role.members.count() == 3
            assert Team.objects.get(name='Blue', organization__name='Default3').member_role.members.count() == 3

            assert Team.objects.get(name='Red', organization__name='Default1').member_role.members.count() == 0

            assert Team.objects.get(name='Green', organization__name='Default1').member_role.members.count() == 3
            assert Team.objects.get(name='Green', organization__name='Default3').member_role.members.count() == 3

    def test_update_user_teams_alias_by_saml_attr(self, orgs, users, kwargs, mock_settings):
        with mock.patch('django.conf.settings', mock_settings):
            u1 = users[0]

            # Test getting teams from attribute with team->org mapping
            kwargs['response']['attributes']['groups'] = ['Yellow']

            # Ensure team and org will be created
            update_user_teams_by_saml_attr(None, None, u1, **kwargs)

            assert Team.objects.filter(name='Yellow', organization__name='Default4').count() == 0
            assert Team.objects.filter(name='Yellow_Alias', organization__name='Default4_Alias').count() == 1
            assert Team.objects.get(
                name='Yellow_Alias', organization__name='Default4_Alias').member_role.members.count() == 1

    @pytest.mark.fixture_args(autocreate=False)
    def test_autocreate_disabled(self, users, kwargs, mock_settings):
        kwargs['response']['attributes']['memberOf'] = ['Default1', 'Default2', 'Default3']
        kwargs['response']['attributes']['groups'] = ['Blue', 'Red', 'Green']
        with mock.patch('django.conf.settings', mock_settings):
            for u in users:
                update_user_orgs_by_saml_attr(None, None, u, **kwargs)
                update_user_teams_by_saml_attr(None, None, u, **kwargs)
                assert Organization.objects.count() == 0
                assert Team.objects.count() == 0

            # precreate everything
            o1 = Organization.objects.create(name='Default1')
            o2 = Organization.objects.create(name='Default2')
            o3 = Organization.objects.create(name='Default3')
            Team.objects.create(name='Blue', organization_id=o1.id)
            Team.objects.create(name='Blue', organization_id=o2.id)
            Team.objects.create(name='Blue', organization_id=o3.id)
            Team.objects.create(name='Red', organization_id=o1.id)
            Team.objects.create(name='Green', organization_id=o1.id)
            Team.objects.create(name='Green', organization_id=o3.id)

            for u in users:
                update_user_orgs_by_saml_attr(None, None, u, **kwargs)
                update_user_teams_by_saml_attr(None, None, u, **kwargs)

        assert o1.member_role.members.count() == 3
        assert o2.member_role.members.count() == 3
        assert o3.member_role.members.count() == 3

        assert Team.objects.get(name='Blue', organization__name='Default1').member_role.members.count() == 3
        assert Team.objects.get(name='Blue', organization__name='Default2').member_role.members.count() == 3
        assert Team.objects.get(name='Blue', organization__name='Default3').member_role.members.count() == 3

        assert Team.objects.get(name='Red', organization__name='Default1').member_role.members.count() == 3

        assert Team.objects.get(name='Green', organization__name='Default1').member_role.members.count() == 3
        assert Team.objects.get(name='Green', organization__name='Default3').member_role.members.count() == 3
