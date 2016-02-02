import pytest

from awx.main.models.organization import Organization
from django.contrib.auth.models import User

def make_user(name, admin=False):
    email = '%s@example.org' % name
    if admin == True:
        return User.objects.create_superuser(name, email, name)
    else:
        return User.objects.create_user(name, email, name)

@pytest.fixture
def organization():
    return Organization.objects.create(name="test-org", description="test-org-desc")

@pytest.mark.django_db
@pytest.mark.parametrize("username,admin", [
    ("admin", True),
    ("user", False),
])
def test_organization_migration(organization, username, admin):
    user = make_user(username, admin)
    organization.admins.add(user)

    migrated_users = organization.migrate_to_rbac()
    assert len(migrated_users) == 1
    assert migrated_users[0] == user

