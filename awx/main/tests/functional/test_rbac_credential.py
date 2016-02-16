import pytest

from awx.main.access import CredentialAccess
from awx.main.models.credential import Credential
from awx.main.migrations import _rbac as rbac
from django.apps import apps
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_credential_migration_user(credential, user, permissions):
    u = user('user', False)
    credential.user = u
    credential.save()

    migrated = rbac.migrate_credential(apps, None)

    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_usage_role(credential, user, permissions):
    u = user('user', False)
    credential.usage_role.members.add(u)
    assert credential.accessible_by(u, permissions['usage'])

@pytest.mark.django_db
def test_credential_migration_team_member(credential, team, user, permissions):
    u = user('user', False)
    team.admin_role.members.add(u)
    credential.team = team
    credential.save()

    # No permissions pre-migration
    assert not credential.accessible_by(u, permissions['admin'])

    migrated = rbac.migrate_credential(apps, None)

    # Admin permissions post migration
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['admin'])

@pytest.mark.django_db
def test_credential_migration_team_admin(credential, team, user, permissions):
    u = user('user', False)
    team.member_role.members.add(u)
    credential.team = team
    credential.save()

    # No permissions pre-migration
    assert not credential.accessible_by(u, permissions['usage'])

    # Usage permissions post migration
    migrated = rbac.migrate_credential(apps, None)
    assert len(migrated) == 1
    assert credential.accessible_by(u, permissions['usage'])

def test_credential_access_superuser():
    u = User(username='admin', is_superuser=True)
    access = CredentialAccess(u)
    credential = Credential()

    assert access.can_add(None)
    assert access.can_change(credential, None)
    assert access.can_delete(credential)

@pytest.mark.django_db
def test_credential_access_admin(user, organization, team, credential):
    u = user('org-admin', False)
    organization.admins.add(u)
    team.organization = organization
    team.save()

    access = CredentialAccess(u)

    assert access.can_add({'user': u.pk})
    assert access.can_add({'team': team.pk})

    assert not access.can_change(credential, {'user': u.pk})

    # unowned credential can be deleted
    assert access.can_delete(credential)

    credential.created_by = u
    credential.save()
    assert not access.can_change(credential, {'user': u.pk})

    team.users.add(u)
    assert access.can_change(credential, {'user': u.pk})
