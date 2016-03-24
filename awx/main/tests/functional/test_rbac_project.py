import pytest

from awx.main.migrations import _rbac as rbac
from awx.main.models import Role, Permission, Project, Organization, Credential, JobTemplate, Inventory
from django.apps import apps
from awx.main.migrations import _old_access as old_access


@pytest.mark.django_db
def test_project_migration():
    '''

        o1  o2  o3       with   o1 -- i1    o2 -- i2
         \  |  /
          \ | /
   c1 ----  p1
           / | \
          /  |  \
        jt1 jt2 jt3
         |   |   |
        i1  i2  i1


        goes to


            o1
            |
            |
   c1 ----  p1
           / |
          /  |
        jt1 jt3
         |   |
        i1  i1


            o2
            |
            |
   c1 ----  p2
            |
            |
           jt2
            |
           i2

            o3
            |
            |
   c1 ----  p3


    '''


    o1 = Organization.objects.create(name='o1')
    o2 = Organization.objects.create(name='o2')
    o3 = Organization.objects.create(name='o3')

    c1 = Credential.objects.create(name='c1')

    p1 = Project.objects.create(name='p1', credential=c1)
    p1.deprecated_organizations.add(o1, o2, o3)

    i1 = Inventory.objects.create(name='i1', organization=o1)
    i2 = Inventory.objects.create(name='i2', organization=o2)

    jt1 = JobTemplate.objects.create(name='jt1', project=p1, inventory=i1)
    jt2 = JobTemplate.objects.create(name='jt2', project=p1, inventory=i2)
    jt3 = JobTemplate.objects.create(name='jt3', project=p1, inventory=i1)

    assert o1.projects.count() == 0
    assert o2.projects.count() == 0
    assert o3.projects.count() == 0

    rbac.migrate_projects(apps, None)

    jt1 = JobTemplate.objects.get(pk=jt1.pk)
    jt2 = JobTemplate.objects.get(pk=jt2.pk)
    jt3 = JobTemplate.objects.get(pk=jt3.pk)

    assert jt1.project == jt3.project
    assert jt1.project != jt2.project

    assert o1.projects.count() == 1
    assert o2.projects.count() == 1
    assert o3.projects.count() == 1
    assert o1.projects.all()[0].jobtemplates.count() == 2
    assert o2.projects.all()[0].jobtemplates.count() == 1
    assert o3.projects.all()[0].jobtemplates.count() == 0

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
    project.deprecated_teams.add(team)

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
