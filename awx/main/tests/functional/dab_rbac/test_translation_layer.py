from unittest import mock
import json

import pytest

from django.contrib.contenttypes.models import ContentType

from crum import impersonate

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import get_role_from_object_role, give_creator_permissions, get_role_codenames, get_role_definition
from awx.main.models import User, Organization, WorkflowJobTemplate, WorkflowJobTemplateNode, Team
from awx.api.versioning import reverse

from ansible_base.rbac.models import RoleUserAssignment, RoleDefinition
from ansible_base.rbac import permission_registry


@pytest.mark.django_db
@pytest.mark.parametrize(
    'role_name',
    [
        'execution_environment_admin_role',
        'workflow_admin_role',
        'project_admin_role',
        'admin_role',
        'auditor_role',
        'read_role',
        'execute_role',
        'approval_role',
        'notification_admin_role',
    ],
)
def test_round_trip_roles(organization, rando, role_name, setup_managed_roles):
    """
    Make an assignment with the old-style role,
    get the equivelent new role
    get the old role again
    """
    getattr(organization, role_name).members.add(rando)
    assignment = RoleUserAssignment.objects.get(user=rando)
    old_role = get_role_from_object_role(assignment.object_role)
    assert old_role.id == getattr(organization, role_name).id


@pytest.mark.django_db
@pytest.mark.parametrize('model', sorted(permission_registry.all_registered_models, key=lambda cls: cls._meta.model_name))
def test_role_migration_matches(request, model, setup_managed_roles):
    fixture_name = model._meta.verbose_name.replace(' ', '_')
    obj = request.getfixturevalue(fixture_name)
    role_ct = 0
    for field in obj._meta.get_fields():
        if isinstance(field, ImplicitRoleField):
            if field.name == 'read_role':
                continue  # intentionally left as "Compat" roles
            role_ct += 1
            old_role = getattr(obj, field.name)
            old_codenames = set(get_role_codenames(old_role))
            rd = get_role_definition(old_role)
            new_codenames = set(rd.permissions.values_list('codename', flat=True))
            # all the old roles should map to a non-Compat role definition
            if 'Compat' not in rd.name:
                model_rds = RoleDefinition.objects.filter(content_type=ContentType.objects.get_for_model(obj))
                rd_data = {}
                for rd in model_rds:
                    rd_data[rd.name] = list(rd.permissions.values_list('codename', flat=True))
            assert (
                'Compat' not in rd.name
            ), f'Permissions for old vs new roles did not match.\nold {field.name}: {old_codenames}\nnew:\n{json.dumps(rd_data, indent=2)}'
            assert new_codenames == set(old_codenames)

    # In the old system these models did not have object-level roles, all others expect some model roles
    if model._meta.model_name not in ('notificationtemplate', 'executionenvironment'):
        assert role_ct > 0


@pytest.mark.django_db
def test_role_naming(setup_managed_roles):
    qs = RoleDefinition.objects.filter(content_type=ContentType.objects.get(model='jobtemplate'), name__endswith='dmin')
    assert qs.count() == 1  # sanity
    rd = qs.first()
    assert rd.name == 'JobTemplate Admin'
    assert rd.description
    assert rd.created_by is None


@pytest.mark.django_db
def test_action_role_naming(setup_managed_roles):
    qs = RoleDefinition.objects.filter(content_type=ContentType.objects.get(model='jobtemplate'), name__endswith='ecute')
    assert qs.count() == 1  # sanity
    rd = qs.first()
    assert rd.name == 'JobTemplate Execute'
    assert rd.description
    assert rd.created_by is None


@pytest.mark.django_db
def test_compat_role_naming(setup_managed_roles, job_template, rando, alice):
    with impersonate(alice):
        job_template.read_role.members.add(rando)
    qs = RoleDefinition.objects.filter(content_type=ContentType.objects.get(model='jobtemplate'), name__endswith='ompat')
    assert qs.count() == 1  # sanity
    rd = qs.first()
    assert rd.name == 'JobTemplate Read Compat'
    assert rd.description
    assert rd.created_by is None


@pytest.mark.django_db
def test_organization_level_permissions(organization, inventory, setup_managed_roles):
    u1 = User.objects.create(username='alice')
    u2 = User.objects.create(username='bob')

    organization.inventory_admin_role.members.add(u1)
    organization.workflow_admin_role.members.add(u2)

    assert u1 in inventory.admin_role
    assert u1 in organization.inventory_admin_role
    assert u2 in organization.workflow_admin_role

    assert u2 not in organization.inventory_admin_role
    assert u1 not in organization.workflow_admin_role
    assert not (set(u1.has_roles.all()) & set(u2.has_roles.all()))  # user have no roles in common

    # Old style
    assert set(Organization.accessible_objects(u1, 'inventory_admin_role')) == set([organization])
    assert set(Organization.accessible_objects(u2, 'inventory_admin_role')) == set()
    assert set(Organization.accessible_objects(u1, 'workflow_admin_role')) == set()
    assert set(Organization.accessible_objects(u2, 'workflow_admin_role')) == set([organization])

    # New style
    assert set(Organization.access_qs(u1, 'add_inventory')) == set([organization])
    assert set(Organization.access_qs(u1, 'change_inventory')) == set([organization])
    assert set(Organization.access_qs(u2, 'add_inventory')) == set()
    assert set(Organization.access_qs(u1, 'add_workflowjobtemplate')) == set()
    assert set(Organization.access_qs(u2, 'add_workflowjobtemplate')) == set([organization])


@pytest.mark.django_db
def test_organization_execute_role(organization, rando, setup_managed_roles):
    organization.execute_role.members.add(rando)
    assert rando in organization.execute_role
    assert set(Organization.accessible_objects(rando, 'execute_role')) == set([organization])


@pytest.mark.django_db
def test_workflow_approval_list(get, post, admin_user, setup_managed_roles):
    workflow_job_template = WorkflowJobTemplate.objects.create()
    approval_node = WorkflowJobTemplateNode.objects.create(workflow_job_template=workflow_job_template)
    url = reverse('api:workflow_job_template_node_create_approval', kwargs={'pk': approval_node.pk, 'version': 'v2'})
    post(url, {'name': 'URL Test', 'description': 'An approval', 'timeout': 0}, user=admin_user)
    approval_node.refresh_from_db()
    approval_jt = approval_node.unified_job_template
    approval_jt.create_unified_job()

    r = get(url=reverse('api:workflow_approval_list'), user=admin_user, expect=200)
    assert r.data['count'] >= 1


@pytest.mark.django_db
def test_creator_permission(rando, admin_user, inventory, setup_managed_roles):
    give_creator_permissions(rando, inventory)
    assert rando in inventory.admin_role
    assert rando in inventory.admin_role.members.all()


@pytest.mark.django_db
def test_team_team_read_role(rando, team, admin_user, post, setup_managed_roles):
    orgs = [Organization.objects.create(name=f'foo-{i}') for i in range(2)]
    teams = [Team.objects.create(name=f'foo-{i}', organization=orgs[i]) for i in range(2)]
    teams[1].member_role.members.add(rando)

    # give second team read permission to first team through the API for regression testing
    url = reverse('api:role_teams_list', kwargs={'pk': teams[0].read_role.pk, 'version': 'v2'})
    post(url, {'id': teams[1].id}, user=admin_user)

    # user should be able to view the first team
    assert rando in teams[0].read_role


@pytest.mark.django_db
def test_implicit_parents_no_assignments(organization):
    """Through the normal course of creating models, we should not be changing DAB RBAC permissions"""
    with mock.patch('awx.main.models.rbac.give_or_remove_permission') as mck:
        Team.objects.create(name='random team', organization=organization)
    mck.assert_not_called()


@pytest.mark.django_db
def test_user_auditor_rel(organization, rando, setup_managed_roles):
    assert rando not in organization.auditor_role
    audit_rd = RoleDefinition.objects.get(name='Organization Audit')
    audit_rd.give_permission(rando, organization)
    assert list(rando.auditor_of_organizations) == [organization]


@pytest.mark.django_db
@pytest.mark.parametrize('resource_name', ['Organization', 'Team'])
@pytest.mark.parametrize('role_name', ['Member', 'Admin'])
def test_mapping_from_controller_role_definitions_to_roles(organization, team, rando, role_name, resource_name, setup_managed_roles):
    """
    ensure mappings for controller roles are correct
    e.g.
    Controller Organization Member > organization.member_role
    Controller Organization Admin > organization.admin_role
    Controller Team Member > team.member_role
    Controller Team Admin > team.admin_role
    """
    resource = organization if resource_name == 'Organization' else team
    old_role_name = f"{role_name.lower()}_role"
    getattr(resource, old_role_name).members.add(rando)
    assignment = RoleUserAssignment.objects.get(user=rando)
    assert assignment.role_definition.name == f'Controller {resource_name} {role_name}'
    old_role = get_role_from_object_role(assignment.object_role)
    assert old_role.id == getattr(resource, old_role_name).id
