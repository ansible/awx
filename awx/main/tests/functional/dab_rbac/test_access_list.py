import pytest

from awx.main.models import User
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_access_list_superuser(get, admin_user, inventory):
    url = reverse('api:inventory_access_list', kwargs={'pk': inventory.id})

    response = get(url, user=admin_user, expect=200)
    by_username = {}
    for entry in response.data['results']:
        by_username[entry['username']] = entry
    assert 'admin' in by_username

    assert len(by_username['admin']['summary_fields']['indirect_access']) == 1
    assert len(by_username['admin']['summary_fields']['direct_access']) == 0
    access_entry = by_username['admin']['summary_fields']['indirect_access'][0]
    assert sorted(access_entry['descendant_roles']) == sorted(['adhoc_role', 'use_role', 'update_role', 'read_role', 'admin_role'])


@pytest.mark.django_db
def test_access_list_system_auditor(get, admin_user, inventory):
    sys_auditor = User.objects.create(username='sys-aud')
    sys_auditor.is_system_auditor = True
    assert sys_auditor.is_system_auditor
    url = reverse('api:inventory_access_list', kwargs={'pk': inventory.id})

    response = get(url, user=admin_user, expect=200)
    by_username = {}
    for entry in response.data['results']:
        by_username[entry['username']] = entry
    assert 'sys-aud' in by_username

    assert len(by_username['sys-aud']['summary_fields']['indirect_access']) == 1
    assert len(by_username['sys-aud']['summary_fields']['direct_access']) == 0
    access_entry = by_username['sys-aud']['summary_fields']['indirect_access'][0]
    assert access_entry['descendant_roles'] == ['read_role']


@pytest.mark.django_db
def test_access_list_direct_access(get, admin_user, inventory):
    u1 = User.objects.create(username='u1')

    inventory.admin_role.members.add(u1)

    url = reverse('api:inventory_access_list', kwargs={'pk': inventory.id})
    response = get(url, user=admin_user, expect=200)
    by_username = {}
    for entry in response.data['results']:
        by_username[entry['username']] = entry
    assert 'u1' in by_username

    assert len(by_username['u1']['summary_fields']['direct_access']) == 1
    assert len(by_username['u1']['summary_fields']['indirect_access']) == 0
    access_entry = by_username['u1']['summary_fields']['direct_access'][0]
    assert sorted(access_entry['descendant_roles']) == sorted(['adhoc_role', 'use_role', 'update_role', 'read_role', 'admin_role'])


@pytest.mark.django_db
def test_access_list_organization_access(get, admin_user, inventory):
    u2 = User.objects.create(username='u2')

    inventory.organization.inventory_admin_role.members.add(u2)

    # User has indirect access to the inventory
    url = reverse('api:inventory_access_list', kwargs={'pk': inventory.id})
    response = get(url, user=admin_user, expect=200)
    by_username = {}
    for entry in response.data['results']:
        by_username[entry['username']] = entry
    assert 'u2' in by_username

    assert len(by_username['u2']['summary_fields']['indirect_access']) == 1
    assert len(by_username['u2']['summary_fields']['direct_access']) == 0
    access_entry = by_username['u2']['summary_fields']['indirect_access'][0]
    assert sorted(access_entry['descendant_roles']) == sorted(['adhoc_role', 'use_role', 'update_role', 'read_role', 'admin_role'])

    # Test that user shows up in the organization access list with direct access of expected roles
    url = reverse('api:organization_access_list', kwargs={'pk': inventory.organization_id})
    response = get(url, user=admin_user, expect=200)
    by_username = {}
    for entry in response.data['results']:
        by_username[entry['username']] = entry
    assert 'u2' in by_username

    assert len(by_username['u2']['summary_fields']['direct_access']) == 1
    assert len(by_username['u2']['summary_fields']['indirect_access']) == 0
    access_entry = by_username['u2']['summary_fields']['direct_access'][0]
    assert sorted(access_entry['descendant_roles']) == sorted(['inventory_admin_role', 'read_role'])


@pytest.mark.django_db
def test_team_indirect_access(get, team, admin_user, inventory):
    u1 = User.objects.create(username='u1')
    team.member_role.members.add(u1)

    inventory.organization.inventory_admin_role.parents.add(team.member_role)

    url = reverse('api:inventory_access_list', kwargs={'pk': inventory.id})
    response = get(url, user=admin_user, expect=200)
    by_username = {}
    for entry in response.data['results']:
        by_username[entry['username']] = entry
    assert 'u1' in by_username

    assert len(by_username['u1']['summary_fields']['direct_access']) == 1
    assert len(by_username['u1']['summary_fields']['indirect_access']) == 0
    access_entry = by_username['u1']['summary_fields']['direct_access'][0]
    assert sorted(access_entry['descendant_roles']) == sorted(['adhoc_role', 'use_role', 'update_role', 'read_role', 'admin_role'])


@pytest.mark.django_db
def test_workflow_access_list(workflow_job_template, alice, bob, setup_managed_roles, get, admin_user):
    """Basic verification that WFJT access_list is functional"""
    workflow_job_template.admin_role.members.add(alice)
    workflow_job_template.organization.workflow_admin_role.members.add(bob)

    url = reverse('api:workflow_job_template_access_list', kwargs={'pk': workflow_job_template.pk})
    for u in (alice, bob, admin_user):
        response = get(url, user=u, expect=200)
        user_ids = [item['id'] for item in response.data['results']]
        assert alice.pk in user_ids
        assert bob.pk in user_ids
