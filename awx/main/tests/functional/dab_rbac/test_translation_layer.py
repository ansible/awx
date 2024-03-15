import pytest

from awx.main.models.rbac import get_role_from_object_role
from awx.main.models import User, Organization, WorkflowJobTemplate, WorkflowJobTemplateNode
from awx.api.versioning import reverse

from ansible_base.rbac.models import RoleUserAssignment


@pytest.mark.django_db
@pytest.mark.parametrize(
    'role_name',
    ['execution_environment_admin_role', 'project_admin_role', 'admin_role', 'auditor_role', 'read_role', 'execute_role', 'notification_admin_role'],
)
def test_round_trip_roles(organization, rando, role_name):
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


@pytest.mark.django_db
def test_organization_level_permissions(organization, inventory):
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
def test_organization_execute_role(organization, rando):
    organization.execute_role.members.add(rando)
    assert rando in organization.execute_role
    assert set(Organization.accessible_objects(rando, 'execute_role')) == set([organization])


@pytest.mark.django_db
def test_workflow_approval_list(get, post, admin_user):
    workflow_job_template = WorkflowJobTemplate.objects.create()
    approval_node = WorkflowJobTemplateNode.objects.create(workflow_job_template=workflow_job_template)
    url = reverse('api:workflow_job_template_node_create_approval', kwargs={'pk': approval_node.pk, 'version': 'v2'})
    post(url, {'name': 'URL Test', 'description': 'An approval', 'timeout': 0}, user=admin_user)
    approval_node.refresh_from_db()
    approval_jt = approval_node.unified_job_template
    approval_jt.create_unified_job()

    r = get(url=reverse('api:workflow_approval_list'), user=admin_user, expect=200)
    assert r.data['count'] >= 1
