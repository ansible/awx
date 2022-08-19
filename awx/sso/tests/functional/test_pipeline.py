import pytest
import re
from unittest import mock

from django.utils.timezone import now

from awx.conf.registry import settings_registry
from awx.sso.pipeline import update_user_orgs, update_user_teams, update_user_orgs_by_saml_attr, update_user_teams_by_saml_attr, _check_flag
from awx.main.models import User, Team, Organization, Credential, CredentialType


@pytest.fixture
def galaxy_credential():
    galaxy_type = CredentialType.objects.create(kind='galaxy')
    cred = Credential(
        created=now(), modified=now(), name='Ansible Galaxy', managed=True, credential_type=galaxy_type, inputs={'url': 'https://galaxy.ansible.com/'}
    )
    cred.save()


@pytest.fixture
def users():
    u1 = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com')
    u2 = User.objects.create(username='user2@foo.com', last_name='foo', first_name='bar', email='user2@foo.com')
    u3 = User.objects.create(username='user3@foo.com', last_name='foo', first_name='bar', email='user3@foo.com')
    return (u1, u2, u3)


@pytest.mark.django_db
class TestSAMLMap:
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
                        'organization_alias': '',
                    }
                },
                'TEAM_MAP': {'Blue': {'organization': 'Default', 'remove': True, 'users': ''}, 'Red': {'organization': 'Default', 'remove': True, 'users': ''}},
            }

            def setting(self, key):
                return self.s[key]

        return Backend()

    @pytest.fixture
    def org(self):
        return Organization.objects.create(name="Default")

    def test_update_user_orgs(self, org, backend, users, galaxy_credential):
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

        # Test organization alias feature
        backend.setting('ORGANIZATION_MAP')['Default']['organization_alias'] = 'Default_Alias'
        update_user_orgs(backend, None, u1)
        assert Organization.objects.get(name="Default_Alias") is not None

        for o in Organization.objects.all():
            if o.name == 'Default':
                # The default org was already created and should not have a galaxy credential
                assert o.galaxy_credentials.count() == 0
            else:
                # The Default_Alias was created by SAML and should get the galaxy credential
                assert o.galaxy_credentials.count() == 1
                assert o.galaxy_credentials.first().name == 'Ansible Galaxy'

    def test_update_user_teams(self, backend, users, galaxy_credential):
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

        for o in Organization.objects.all():
            assert o.galaxy_credentials.count() == 1
            assert o.galaxy_credentials.first().name == 'Ansible Galaxy'


@pytest.mark.django_db
class TestSAMLAttr:
    @pytest.fixture
    def kwargs(self):
        return {
            'username': u'cmeyers@redhat.com',
            'uid': 'idp:cmeyers@redhat.com',
            'request': {u'SAMLResponse': [], u'RelayState': [u'idp']},
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
                    'PersonImmutableID': [],
                },
            },
            #'social': <UserSocialAuth: cmeyers@redhat.com>,
            'social': None,
            #'strategy': <awx.sso.strategies.django_strategy.AWXDjangoStrategy object at 0x8523a10>,
            'strategy': None,
            'new_association': False,
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

        class MockSettings:
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
                    {'team': 'Yellow', 'team_alias': 'Yellow_Alias', 'organization': 'Default4', 'organization_alias': 'Default4_Alias'},
                ],
            }

        mock_settings_obj = MockSettings()
        for key in settings_registry.get_registered_settings(category_slug='logging'):
            value = settings_registry.get_setting_field(key).get_default()
            setattr(mock_settings_obj, key, value)
        setattr(mock_settings_obj, 'DEBUG', True)

        return mock_settings_obj

    @pytest.fixture
    def backend(self):
        class Backend:
            s = {
                'ORGANIZATION_MAP': {
                    'Default1': {
                        'remove': True,
                        'admins': 'foobar',
                        'remove_admins': True,
                        'users': 'foo',
                        'remove_users': True,
                        'organization_alias': 'o1_alias',
                    }
                }
            }

            def setting(self, key):
                return self.s[key]

        return Backend()

    def test_update_user_orgs_by_saml_attr(self, orgs, users, galaxy_credential, kwargs, mock_settings, backend):
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

            update_user_orgs_by_saml_attr(backend, None, u1, **kwargs)
            assert Organization.objects.get(name="o1_alias").member_role.members.count() == 1

        for o in Organization.objects.all():
            if o.id in [o1.id, o2.id, o3.id]:
                # o[123] were created without a default galaxy cred
                assert o.galaxy_credentials.count() == 0
            else:
                # anything else created should have a default galaxy cred
                assert o.galaxy_credentials.count() == 1
                assert o.galaxy_credentials.first().name == 'Ansible Galaxy'

    def test_update_user_teams_by_saml_attr(self, orgs, users, galaxy_credential, kwargs, mock_settings):
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

        for o in Organization.objects.all():
            if o.id in [o1.id, o2.id, o3.id]:
                # o[123] were created without a default galaxy cred
                assert o.galaxy_credentials.count() == 0
            else:
                # anything else created should have a default galaxy cred
                assert o.galaxy_credentials.count() == 1
                assert o.galaxy_credentials.first().name == 'Ansible Galaxy'

    def test_update_user_teams_alias_by_saml_attr(self, orgs, users, galaxy_credential, kwargs, mock_settings):
        with mock.patch('django.conf.settings', mock_settings):
            u1 = users[0]

            # Test getting teams from attribute with team->org mapping
            kwargs['response']['attributes']['groups'] = ['Yellow']

            # Ensure team and org will be created
            update_user_teams_by_saml_attr(None, None, u1, **kwargs)

            assert Team.objects.filter(name='Yellow', organization__name='Default4').count() == 0
            assert Team.objects.filter(name='Yellow_Alias', organization__name='Default4').count() == 1
            assert Team.objects.get(name='Yellow_Alias', organization__name='Default4').member_role.members.count() == 1

        # only Org 4 got created/updated
        org = Organization.objects.get(name='Default4')
        assert org.galaxy_credentials.count() == 1
        assert org.galaxy_credentials.first().name == 'Ansible Galaxy'

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

    def test_galaxy_credential_auto_assign(self, users, kwargs, galaxy_credential, mock_settings):
        kwargs['response']['attributes']['memberOf'] = ['Default1', 'Default2', 'Default3']
        kwargs['response']['attributes']['groups'] = ['Blue', 'Red', 'Green']
        with mock.patch('django.conf.settings', mock_settings):
            for u in users:
                update_user_orgs_by_saml_attr(None, None, u, **kwargs)
                update_user_teams_by_saml_attr(None, None, u, **kwargs)

        assert Organization.objects.count() == 4
        for o in Organization.objects.all():
            assert o.galaxy_credentials.count() == 1
            assert o.galaxy_credentials.first().name == 'Ansible Galaxy'

    def test_galaxy_credential_no_auto_assign(self, users, kwargs, galaxy_credential, mock_settings):
        # A Galaxy credential should not be added to an existing org
        o = Organization.objects.create(name='Default1')
        o = Organization.objects.create(name='Default2')
        o = Organization.objects.create(name='Default3')
        o = Organization.objects.create(name='Default4')
        kwargs['response']['attributes']['memberOf'] = ['Default1']
        kwargs['response']['attributes']['groups'] = ['Blue']
        with mock.patch('django.conf.settings', mock_settings):
            for u in users:
                update_user_orgs_by_saml_attr(None, None, u, **kwargs)
                update_user_teams_by_saml_attr(None, None, u, **kwargs)

        assert Organization.objects.count() == 4
        for o in Organization.objects.all():
            assert o.galaxy_credentials.count() == 0


@pytest.mark.django_db
class TestSAMLUserFlags:
    @pytest.mark.parametrize(
        "user_flags_settings, expected, is_superuser",
        [
            # In this case we will pass no user flags so new_flag should be false and changed will def be false
            (
                {},
                (False, False),
                False,
            ),
            # NOTE: The first handful of tests test role/value as string instead of lists.
            #       This was from the initial implementation of these fields but the code should be able to handle this
            #       There are a couple tests at the end of this which will validate arrays in these values.
            #
            # In this case we will give the user a group to make them an admin
            (
                {'is_superuser_role': 'test-role-1'},
                (True, True),
                False,
            ),
            # In this case we will give the user a flag that will make then an admin
            (
                {'is_superuser_attr': 'is_superuser'},
                (True, True),
                False,
            ),
            # In this case we will give the user a flag but the wrong value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'junk'},
                (False, False),
                False,
            ),
            # In this case we will give the user a flag and the right value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'true'},
                (True, True),
                False,
            ),
            # In this case we will give the user a proper role and an is_superuser_attr role that they dont have, this should make them an admin
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'gibberish', 'is_superuser_value': 'true'},
                (True, True),
                False,
            ),
            # In this case we will give the user a proper role and an is_superuser_attr role that they have, this should make them an admin
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'test-role-1'},
                (True, True),
                False,
            ),
            # In this case we will give the user a proper role and an is_superuser_attr role that they have but a bad value, this should make them an admin
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'junk'},
                (False, False),
                False,
            ),
            # In this case we will give the user everything
            (
                {'is_superuser_role': 'test-role-1', 'is_superuser_attr': 'is_superuser', 'is_superuser_value': 'true'},
                (True, True),
                False,
            ),
            # In this test case we will validate that a single attribute (instead of a list) still works
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'test_id'},
                (True, True),
                False,
            ),
            # This will be a negative test for a single atrribute
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'junk'},
                (False, False),
                False,
            ),
            # The user is already a superuser so we should remove them
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'junk', 'remove_superusers': True},
                (False, True),
                True,
            ),
            # The user is already a superuser but we don't have a remove field
            (
                {'is_superuser_attr': 'name_id', 'is_superuser_value': 'junk', 'remove_superusers': False},
                (True, False),
                True,
            ),
            # Positive test for multiple values for is_superuser_value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': ['junk', 'junk2', 'else', 'junk']},
                (True, True),
                False,
            ),
            # Negative test for multiple values for is_superuser_value
            (
                {'is_superuser_attr': 'is_superuser', 'is_superuser_value': ['junk', 'junk2', 'junk']},
                (False, True),
                True,
            ),
            # Positive test for multiple values of is_superuser_role
            (
                {'is_superuser_role': ['junk', 'junk2', 'something', 'junk']},
                (True, True),
                False,
            ),
            # Negative test for multiple values of is_superuser_role
            (
                {'is_superuser_role': ['junk', 'junk2', 'junk']},
                (False, True),
                True,
            ),
        ],
    )
    def test__check_flag(self, user_flags_settings, expected, is_superuser):
        user = User()
        user.username = 'John'
        user.is_superuser = is_superuser

        attributes = {
            'email': ['noone@nowhere.com'],
            'last_name': ['Westcott'],
            'is_superuser': ['something', 'else', 'true'],
            'username': ['test_id'],
            'first_name': ['John'],
            'Role': ['test-role-1', 'something', 'different'],
            'name_id': 'test_id',
        }

        assert expected == _check_flag(user, 'superuser', attributes, user_flags_settings)
