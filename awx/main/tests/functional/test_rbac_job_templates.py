import mock
import pytest

from awx.main.access import (
    BaseAccess,
    JobTemplateAccess,
)
from awx.main.migrations import _rbac as rbac
from awx.main.models import Permission
from awx.main.models.jobs import JobTemplate
from django.apps import apps

from django.core.urlresolvers import reverse


@pytest.fixture
def jt_objects(job_template_factory):
    objects = job_template_factory(
        'testJT', organization='org1', project='proj1', inventory='inventory1',
        credential='cred1', cloud_credential='aws1', network_credential='juniper1')
    return objects

@pytest.mark.django_db
def test_job_template_migration_check(credential, deploy_jobtemplate, check_jobtemplate, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')

    credential.deprecated_user = joe
    credential.save()

    check_jobtemplate.project.organization.deprecated_users.add(joe)

    Permission(user=joe, inventory=check_jobtemplate.inventory, permission_type='read').save()
    Permission(user=joe, inventory=check_jobtemplate.inventory,
               project=check_jobtemplate.project, permission_type='check').save()


    rbac.migrate_users(apps, None)
    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)
    rbac.migrate_inventory(apps, None)

    assert joe in check_jobtemplate.project.read_role
    assert admin in check_jobtemplate.execute_role
    assert joe not in check_jobtemplate.execute_role

    rbac.migrate_job_templates(apps, None)

    assert admin in check_jobtemplate.execute_role
    assert joe in check_jobtemplate.execute_role
    assert admin in deploy_jobtemplate.execute_role
    assert joe not in deploy_jobtemplate.execute_role

@pytest.mark.django_db
def test_job_template_migration_deploy(credential, deploy_jobtemplate, check_jobtemplate, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')

    credential.deprecated_user = joe
    credential.save()

    deploy_jobtemplate.project.organization.deprecated_users.add(joe)

    Permission(user=joe, inventory=deploy_jobtemplate.inventory, permission_type='read').save()
    Permission(user=joe, inventory=deploy_jobtemplate.inventory,
               project=deploy_jobtemplate.project, permission_type='run').save()

    rbac.migrate_users(apps, None)
    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)
    rbac.migrate_inventory(apps, None)

    assert joe in deploy_jobtemplate.project.read_role
    assert admin in deploy_jobtemplate.execute_role
    assert joe not in deploy_jobtemplate.execute_role

    rbac.migrate_job_templates(apps, None)

    assert admin in deploy_jobtemplate.execute_role
    assert joe in deploy_jobtemplate.execute_role
    assert admin in check_jobtemplate.execute_role
    assert joe in check_jobtemplate.execute_role


@pytest.mark.django_db
def test_job_template_team_migration_check(credential, deploy_jobtemplate, check_jobtemplate, organization, team, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')
    team.deprecated_users.add(joe)
    team.organization = organization
    team.save()

    credential.deprecated_team = team
    credential.save()

    check_jobtemplate.project.organization.deprecated_users.add(joe)

    Permission(team=team, inventory=check_jobtemplate.inventory, permission_type='read').save()
    Permission(team=team, inventory=check_jobtemplate.inventory,
               project=check_jobtemplate.project, permission_type='check').save()

    rbac.migrate_users(apps, None)
    rbac.migrate_team(apps, None)
    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)
    rbac.migrate_inventory(apps, None)

    assert joe not in check_jobtemplate.read_role
    assert admin in check_jobtemplate.execute_role
    assert joe not in check_jobtemplate.execute_role

    rbac.migrate_job_templates(apps, None)

    assert admin in check_jobtemplate.execute_role
    assert joe in check_jobtemplate.execute_role

    assert admin in deploy_jobtemplate.execute_role
    assert joe not in deploy_jobtemplate.execute_role


@pytest.mark.django_db
def test_job_template_team_deploy_migration(credential, deploy_jobtemplate, check_jobtemplate, organization, team, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')
    team.deprecated_users.add(joe)
    team.organization = organization
    team.save()

    credential.deprecated_team = team
    credential.save()

    deploy_jobtemplate.project.organization.deprecated_users.add(joe)

    Permission(team=team, inventory=deploy_jobtemplate.inventory, permission_type='read').save()
    Permission(team=team, inventory=deploy_jobtemplate.inventory,
               project=deploy_jobtemplate.project, permission_type='run').save()

    rbac.migrate_users(apps, None)
    rbac.migrate_team(apps, None)
    rbac.migrate_organization(apps, None)
    rbac.migrate_projects(apps, None)
    rbac.migrate_inventory(apps, None)

    assert joe not in deploy_jobtemplate.read_role
    assert admin in deploy_jobtemplate.execute_role
    assert joe not in deploy_jobtemplate.execute_role

    rbac.migrate_job_templates(apps, None)

    assert joe in deploy_jobtemplate.read_role
    assert admin in deploy_jobtemplate.execute_role
    assert joe in deploy_jobtemplate.execute_role

    assert admin in check_jobtemplate.execute_role
    assert joe in check_jobtemplate.execute_role


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_job_template_access_superuser(check_license, user, deploy_jobtemplate):
    # GIVEN a superuser
    u = user('admin', True)
    # WHEN access to a job template is checked
    access = JobTemplateAccess(u)
    # THEN all access checks should pass
    assert access.can_read(deploy_jobtemplate)
    assert access.can_add({})

@pytest.mark.django_db
def test_job_template_access_read_level(jt_objects, rando):

    access = JobTemplateAccess(rando)
    jt_objects.project.read_role.members.add(rando)
    jt_objects.inventory.read_role.members.add(rando)
    jt_objects.credential.read_role.members.add(rando)
    jt_objects.cloud_credential.read_role.members.add(rando)
    jt_objects.network_credential.read_role.members.add(rando)

    proj_pk = jt_objects.project.pk
    assert not access.can_add(dict(inventory=jt_objects.inventory.pk, project=proj_pk))
    assert not access.can_add(dict(credential=jt_objects.credential.pk, project=proj_pk))
    assert not access.can_add(dict(cloud_credential=jt_objects.cloud_credential.pk, project=proj_pk))
    assert not access.can_add(dict(network_credential=jt_objects.network_credential.pk, project=proj_pk))

@pytest.mark.django_db
def test_job_template_access_use_level(jt_objects, rando):

    access = JobTemplateAccess(rando)
    jt_objects.project.use_role.members.add(rando)
    jt_objects.inventory.use_role.members.add(rando)
    jt_objects.credential.use_role.members.add(rando)
    jt_objects.cloud_credential.use_role.members.add(rando)
    jt_objects.network_credential.use_role.members.add(rando)

    proj_pk = jt_objects.project.pk
    assert access.can_add(dict(inventory=jt_objects.inventory.pk, project=proj_pk))
    assert access.can_add(dict(credential=jt_objects.credential.pk, project=proj_pk))
    assert access.can_add(dict(cloud_credential=jt_objects.cloud_credential.pk, project=proj_pk))
    assert access.can_add(dict(network_credential=jt_objects.network_credential.pk, project=proj_pk))

@pytest.mark.django_db
def test_job_template_access_org_admin(jt_objects, rando):
    access = JobTemplateAccess(rando)
    # Appoint this user as admin of the organization
    jt_objects.inventory.organization.admin_role.members.add(rando)
    # Assign organization permission in the same way the create view does
    organization = jt_objects.inventory.organization
    jt_objects.credential.admin_role.parents.add(organization.admin_role)
    jt_objects.cloud_credential.admin_role.parents.add(organization.admin_role)
    jt_objects.network_credential.admin_role.parents.add(organization.admin_role)

    proj_pk = jt_objects.project.pk
    assert access.can_add(dict(inventory=jt_objects.inventory.pk, project=proj_pk))
    assert access.can_add(dict(credential=jt_objects.credential.pk, project=proj_pk))
    assert access.can_add(dict(cloud_credential=jt_objects.cloud_credential.pk, project=proj_pk))
    assert access.can_add(dict(network_credential=jt_objects.network_credential.pk, project=proj_pk))

    assert access.can_read(jt_objects.job_template)
    assert access.can_delete(jt_objects.job_template)

@pytest.mark.django_db
@pytest.mark.job_permissions
def test_job_template_creator_access(project, rando, post):

    project.admin_role.members.add(rando)
    with mock.patch(
            'awx.main.models.projects.ProjectOptions.playbooks',
            new_callable=mock.PropertyMock(return_value=['helloworld.yml'])):
        response = post(reverse('api:job_template_list', args=[]), dict(
            name='newly-created-jt',
            job_type='run',
            ask_inventory_on_launch=True,
            ask_credential_on_launch=True,
            project=project.pk,
            playbook='helloworld.yml'
        ), rando)

    assert response.status_code == 201
    jt_pk = response.data['id']
    jt_obj = JobTemplate.objects.get(pk=jt_pk)
    # Creating a JT should place the creator in the admin role
    assert rando in jt_obj.admin_role
