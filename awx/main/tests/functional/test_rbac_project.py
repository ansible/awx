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

    project_name = unicode("\xc3\xb4", "utf-8")
    p1 = Project.objects.create(name=project_name, credential=c1)
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
def test_single_org_project_migration(organization):
    project = Project.objects.create(name='my project',
                                     description="description",
                                     organization=None)
    organization.deprecated_projects.add(project)
    assert project.organization is None
    rbac.migrate_projects(apps, None)
    project = Project.objects.get(id=project.id)
    assert project.organization.id == organization.id

@pytest.mark.django_db
def test_no_org_project_migration(organization):
    project = Project.objects.create(name='my project',
                                     description="description",
                                     organization=None)
    assert project.organization is None
    rbac.migrate_projects(apps, None)
    assert project.organization is None

@pytest.mark.django_db
def test_multi_org_project_migration():
    org1 = Organization.objects.create(name="org1", description="org1 desc")
    org2 = Organization.objects.create(name="org2", description="org2 desc")
    project = Project.objects.create(name='my project',
                                     description="description",
                                     organization=None)

    assert Project.objects.all().count() == 1
    assert Project.objects.filter(organization=org1).count() == 0
    assert Project.objects.filter(organization=org2).count() == 0

    project.deprecated_organizations.add(org1)
    project.deprecated_organizations.add(org2)
    assert project.organization is None
    rbac.migrate_projects(apps, None)
    assert Project.objects.filter(organization=org1).count() == 1
    assert Project.objects.filter(organization=org2).count() == 1


@pytest.mark.django_db
def test_project_user_project(user_project, project, user):
    u = user('owner')

    assert old_access.check_user_access(u, user_project.__class__, 'read', user_project)
    assert old_access.check_user_access(u, project.__class__, 'read', project) is False

    assert u not in user_project.read_role
    assert u not in project.read_role
    rbac.migrate_projects(apps, None)
    assert u in user_project.read_role
    assert u not in project.read_role

@pytest.mark.django_db
def test_project_accessible_by_sa(user, project):
    u = user('systemadmin', is_superuser=True)
    # This gets setup by a signal, but we want to test the migration which will set this up too, so remove it
    Role.singleton('system_administrator').members.remove(u)

    assert u not in project.read_role
    rbac.migrate_organization(apps, None)
    rbac.migrate_users(apps, None)
    rbac.migrate_projects(apps, None)
    print(project.admin_role.ancestors.all())
    print(project.admin_role.ancestors.all())
    assert u in project.admin_role

@pytest.mark.django_db
def test_project_org_members(user, organization, project):
    admin = user('orgadmin')
    member = user('orgmember')

    assert admin not in project.read_role
    assert member not in project.read_role

    organization.deprecated_admins.add(admin)
    organization.deprecated_users.add(member)

    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)

    assert admin in project.admin_role
    assert member in project.read_role

@pytest.mark.django_db
def test_project_team(user, team, project):
    nonmember = user('nonmember')
    member = user('member')

    team.deprecated_users.add(member)
    project.deprecated_teams.add(team)

    assert nonmember not in project.read_role
    assert member not in project.read_role

    rbac.migrate_team(apps, None)
    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)

    assert member in project.read_role
    assert nonmember not in project.read_role

@pytest.mark.django_db
def test_project_explicit_permission(user, team, project, organization):
    u = user('prjuser')

    assert old_access.check_user_access(u, project.__class__, 'read', project) is False

    organization.deprecated_users.add(u)
    p = Permission(user=u, project=project, permission_type='create', name='Perm name')
    p.save()

    assert u not in project.read_role

    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)

    assert u in project.read_role
