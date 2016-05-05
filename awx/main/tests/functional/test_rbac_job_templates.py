import mock
import pytest

from awx.main.access import (
    BaseAccess,
    JobTemplateAccess,
)
from awx.main.migrations import _rbac as rbac
from awx.main.models import Permission
from django.apps import apps


@pytest.mark.django_db
def test_job_template_migration_check(deploy_jobtemplate, check_jobtemplate, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')


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
def test_job_template_migration_deploy(deploy_jobtemplate, check_jobtemplate, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')


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
def test_job_template_team_migration_check(deploy_jobtemplate, check_jobtemplate, organization, team, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')
    team.deprecated_users.add(joe)
    team.organization = organization
    team.save()

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
def test_job_template_team_deploy_migration(deploy_jobtemplate, check_jobtemplate, organization, team, user):
    admin = user('admin', is_superuser=True)
    joe = user('joe')
    team.deprecated_users.add(joe)
    team.organization = organization
    team.save()

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
