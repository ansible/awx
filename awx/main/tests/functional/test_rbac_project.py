import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import Role
from awx.main.models.organization import Permission
from django.apps import apps
from awx.main.migrations import _old_access as old_access


@pytest.mark.django_db
def test_project_user_project(user_project, project, user):
    u = user('owner')

    assert old_access.check_user_access(u, user_project.__class__, 'read', user_project)
    assert old_access.check_user_access(u, project.__class__, 'read', project) is False

    assert user_project.accessible_by(u, {'read': True}) is False
    assert project.accessible_by(u, {'read': True}) is False
    migrations = rbac.migrate_projects(apps, None)
    assert len(migrations[user_project.name]['users']) == 1
    assert len(migrations[user_project.name]['teams']) == 0
    assert user_project.accessible_by(u, {'read': True}) is True
    assert project.accessible_by(u, {'read': True}) is False

@pytest.mark.django_db
def test_project_accessible_by_sa(user, project):
    u = user('systemadmin', is_superuser=True)
    # This gets setup by a signal, but we want to test the migration which will set this up too, so remove it
    Role.singleton('System Administrator').members.remove(u)

    assert project.accessible_by(u, {'read': True}) is False
    rbac.migrate_organization(apps, None)
    su_migrations = rbac.migrate_users(apps, None)
    migrations = rbac.migrate_projects(apps, None)
    assert len(su_migrations) == 1
    assert len(migrations[project.name]['users']) == 0
    assert len(migrations[project.name]['teams']) == 0
    print(project.admin_role.ancestors.all())
    print(project.admin_role.ancestors.all())
    assert project.accessible_by(u, {'read': True, 'write': True}) is True

@pytest.mark.django_db
def test_project_org_members(user, organization, project):
    admin = user('orgadmin')
    member = user('orgmember')

    assert project.accessible_by(admin, {'read': True}) is False
    assert project.accessible_by(member, {'read': True}) is False

    organization.deprecated_admins.add(admin)
    organization.deprecated_users.add(member)

    rbac.migrate_organization(apps, None)
    migrations = rbac.migrate_projects(apps, None)

    assert len(migrations[project.name]['users']) == 1
    assert len(migrations[project.name]['teams']) == 0
    assert project.accessible_by(admin, {'read': True, 'write': True}) is True
    assert project.accessible_by(member, {'read': True})

@pytest.mark.django_db
def test_project_team(user, team, project):
    nonmember = user('nonmember')
    member = user('member')

    team.deprecated_users.add(member)
    project.teams.add(team)

    assert project.accessible_by(nonmember, {'read': True}) is False
    assert project.accessible_by(member, {'read': True}) is False

    rbac.migrate_team(apps, None)
    rbac.migrate_organization(apps, None)
    migrations = rbac.migrate_projects(apps, None)

    assert len(migrations[project.name]['users']) == 0
    assert len(migrations[project.name]['teams']) == 1
    assert project.accessible_by(member, {'read': True}) is True
    assert project.accessible_by(nonmember, {'read': True}) is False

@pytest.mark.django_db
def test_project_explicit_permission(user, team, project, organization):
    u = user('prjuser')

    assert old_access.check_user_access(u, project.__class__, 'read', project) is False

    organization.deprecated_users.add(u)
    p = Permission(user=u, project=project, permission_type='create', name='Perm name')
    p.save()

    assert project.accessible_by(u, {'read': True}) is False

    rbac.migrate_organization(apps, None)
    migrations = rbac.migrate_projects(apps, None)

    assert len(migrations[project.name]['users']) == 1
    assert project.accessible_by(u, {'read': True}) is True
