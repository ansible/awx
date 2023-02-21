import pytest
import re

from awx.sso.social_pipeline import update_user_orgs, update_user_teams
from awx.main.models import User, Team, Organization


@pytest.fixture
def users():
    u1 = User.objects.create(username='user1@foo.com', last_name='foo', first_name='bar', email='user1@foo.com')
    u2 = User.objects.create(username='user2@foo.com', last_name='foo', first_name='bar', email='user2@foo.com')
    u3 = User.objects.create(username='user3@foo.com', last_name='foo', first_name='bar', email='user3@foo.com')
    return (u1, u2, u3)


@pytest.mark.django_db
class TestSocialPipeline:
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

        # Test organization alias feature
        backend.setting('ORGANIZATION_MAP')['Default']['organization_alias'] = 'Default_Alias'
        update_user_orgs(backend, None, u1)
        assert Organization.objects.get(name="Default_Alias") is not None

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
