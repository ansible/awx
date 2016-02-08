import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.access import OrganizationAccess
from django.apps import apps


@pytest.mark.django_db
def test_organization_migration_admin(organization, permissions, user):
    u = user('admin', True)
    organization.admins.add(u)

    assert not organization.accessible_by(u, permissions['admin'])

    migrations = rbac.migrate_organization(apps, None)

    assert len(migrations) == 1
    assert organization.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_organization_migration_user(organization, permissions, user):
    u = user('user', False)
    organization.users.add(u)

    assert not organization.accessible_by(u, permissions['auditor'])

    migrations = rbac.migrate_organization(apps, None)

    assert len(migrations) == 1
    assert organization.accessible_by(u, permissions['auditor'])

@pytest.mark.django_db
def test_organization_access_superuser(organization, user):
    access = OrganizationAccess(user('admin', True))
    assert access.can_change(organization, None)

@pytest.mark.django_db
def test_organization_access_admin(organization, user):
    u = user('admin', False)
    organization.admins.add(u)

    access = OrganizationAccess(u)
    assert access.can_change(organization, None)

@pytest.mark.django_db
def test_organization_access_user(organization, user):
    access = OrganizationAccess(user('user', False))
    assert not access.can_change(organization, None)
