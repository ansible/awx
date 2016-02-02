import pytest

from awx.main.access import OrganizationAccess
from django.contrib.auth.models import User

def make_user(name, admin=False):
    try:
        user = User.objects.get(username=name)
    except User.DoesNotExist:
        user = User(username=name, is_superuser=admin, password=name)
        user.save()
    return user

@pytest.mark.django_db
@pytest.mark.parametrize("username,admin", [
    ("admin", True),
    ("user", False),
])
def test_organization_migration(organization, permissions, username, admin):
    user = make_user(username, admin)
    if admin:
        organization.admins.add(user)
    else:
        organization.users.add(user)

    migrated_users = organization.migrate_to_rbac()
    assert len(migrated_users) == 1
    assert migrated_users[0] == user

    if admin:
        assert organization.accessible_by(user, permissions['admin']) == True
    else:
        assert organization.accessible_by(user, permissions['auditor']) == True

@pytest.mark.django_db
@pytest.mark.parametrize("username,admin", [
    ("admin", True),
    ("user-admin", False),
    ("user", False)
])
def test_organization_access(organization, username, admin):
    user = make_user(username, admin)
    access = OrganizationAccess(user)
    if admin:
        assert access.can_change(organization, None) == True
    elif username == "user-admin":
        organization.admins.add(user)
        assert access.can_change(organization, None) == True
    else:
        assert access.can_change(organization, None) == False

