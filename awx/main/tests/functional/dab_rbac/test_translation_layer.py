from unittest import mock

import pytest

from django.contrib.contenttypes.models import ContentType
from django.apps import apps

from crum import impersonate

from awx.main.models.rbac import get_role_from_object_role, give_creator_permissions
from awx.main.models import User, Organization, WorkflowJobTemplate, WorkflowJobTemplateNode, Team
from awx.main.migrations._dab_rbac import setup_managed_role_definitions
from awx.api.versioning import reverse

from ansible_base.rbac.models import RoleUserAssignment, RoleDefinition


@pytest.mark.django_db
@pytest.mark.parametrize(
    'role_name',
    ['execution_environment_admin_role', 'project_admin_role', 'admin_role', 'auditor_role', 'read_role', 'execute_role', 'notification_admin_role'],
)
def test_round_trip_roles(organization, rando, role_name, managed_roles):
    """
    Make an assignment with the old-style role,
    get the equivelent new role
    get the old role again
    """
    getattr(organization, role_name).members.add(rando)
    assignment = RoleUserAssignment.objects.get(user=rando)
    print(assignment.role_definition.name)
    old_role = get_role_from_object_role(assignment.object_role)
    assert old_role.id == getattr(organization, role_name).id


@pytest.fixture
def setup_managed():
    setup_managed_role_definitions(apps, None)


@pytest.mark.django_db
def test_role_naming(setup_managed):
    qs = RoleDefinition.objects.filter(content_type=ContentType.objects.get(model='jobtemplate'), name__endswith='dmin')
    assert qs.count() == 1  # sanity
    rd = qs.first()
    assert rd.name == 'JobTemplate Admin'
    assert rd.description
    assert rd.created_by is None


@pytest.mark.django_db
def test_action_role_naming(setup_managed):
    qs = RoleDefinition.objects.filter(content_type=ContentType.objects.get(model='jobtemplate'), name__endswith='ecute')
    assert qs.count() == 1  # sanity
    rd = qs.first()
    assert rd.name == 'JobTemplate Execute'
    assert rd.description
    assert rd.created_by is None


@pytest.mark.django_db
def test_compat_role_naming(setup_managed, job_template, rando, alice):
    with impersonate(alice):
        job_template.read_role.members.add(rando)
    qs = RoleDefinition.objects.filter(content_type=ContentType.objects.get(model='jobtemplate'), name__endswith='ompat')
    assert qs.count() == 1  # sanity
    rd = qs.first()
    assert rd.name == 'JobTemplate Read Compat'
    assert rd.description
    assert rd.created_by is None


@pytest.mark.django_db
def test_organization_level_permissions(organization, inventory, managed_roles):
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
def test_organization_execute_role(organization, rando, managed_roles):
    organization.execute_role.members.add(rando)
    assert rando in organization.execute_role
    assert set(Organization.accessible_objects(rando, 'execute_role')) == set([organization])


@pytest.mark.django_db
def test_workflow_approval_list(get, post, admin_user, managed_roles):
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
def test_creator_permission(rando, admin_user, inventory, managed_roles):
    give_creator_permissions(rando, inventory)
    assert rando in inventory.admin_role
    assert rando in inventory.admin_role.members.all()


@pytest.mark.django_db
def test_team_team_read_role(rando, team, admin_user, post, managed_roles):
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
