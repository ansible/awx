import pytest

from django.test.utils import CaptureQueriesContext
from django.db import connection

from ansible_base.rbac.models import RoleDefinition

from awx.api.versioning import reverse
from awx.main.models import (
    AdHocCommand,
    Credential,
    CredentialType,
    InventorySource,
    InventoryUpdate,
    JobTemplate,
    Organization,
    Project,
    Team,
    UnifiedJob,
)


@pytest.mark.django_db
def test_unified_job_list_uses_or_not_union(user, organization, inventory, setup_managed_roles, get):
    """The unified job list RBAC query uses OR-based filtering, not UNION."""
    org_admin = user('uj-org-admin')
    RoleDefinition.objects.get(name='Organization Admin').give_permission(org_admin, organization)

    project = Project.objects.create(name='uj-test-project', organization=organization)
    jt = JobTemplate.objects.create(name='uj-test-jt', project=project, inventory=inventory, organization=organization)
    jt.create_unified_job()

    inv_src = InventorySource.objects.create(name='uj-test-invsrc', inventory=inventory, source='ec2')
    InventoryUpdate.objects.create(inventory_source=inv_src, source=inv_src.source)

    AdHocCommand.objects.create(name='uj-test-adhoc', inventory=inventory)

    with CaptureQueriesContext(connection) as ctx:
        response = get(reverse('api:unified_job_list'), org_admin)

    assert response.status_code == 200
    assert response.data['count'] >= 3

    uj_rbac_queries = [q['sql'] for q in ctx.captured_queries if 'main_unifiedjob' in q['sql'] and 'dab_rbac_roleevaluation' in q['sql']]
    assert uj_rbac_queries, "Expected a unified-job RBAC query"
    for sql in uj_rbac_queries:
        assert 'UNION' not in sql, "RBAC query should use OR, not UNION"


@pytest.mark.django_db
def test_unified_job_list_org_auditor_sees_jobs(user, setup_managed_roles, get):
    """Org auditors see unified jobs in their org via the audit_organization RBAC branch."""
    org = Organization.objects.create(name='uj-audit-org')
    auditor = user('uj-auditor')
    RoleDefinition.objects.get(name='Organization Audit').give_permission(auditor, org)

    inventory = org.inventories.create(name='uj-audit-inv')
    project = Project.objects.create(name='uj-audit-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-audit-jt', project=project, inventory=inventory, organization=org)
    job = jt.create_unified_job()

    response = get(reverse('api:unified_job_list'), auditor)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert job.pk in result_ids


@pytest.mark.django_db
def test_unified_job_list_inventory_viewer_sees_inventory_updates(user, setup_managed_roles, get):
    """Users with inventory view permission see inventory updates via the inventory RBAC branch."""
    org = Organization.objects.create(name='uj-inv-org')
    inventory = org.inventories.create(name='uj-inv-test')
    inv_viewer = user('uj-inv-viewer')
    RoleDefinition.objects.get(name='Inventory Admin').give_permission(inv_viewer, inventory)

    inv_src = InventorySource.objects.create(name='uj-inv-src', inventory=inventory, source='ec2')
    inv_update = InventoryUpdate.objects.create(inventory_source=inv_src, source=inv_src.source)

    response = get(reverse('api:unified_job_list'), inv_viewer)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert inv_update.pk in result_ids


@pytest.mark.django_db
def test_unified_job_list_singleton_permissions(user, organization, inventory, setup_managed_roles, get):
    """Users with global (singleton) view permissions see jobs via shortcut paths
    that bypass RoleEvaluation queries entirely."""
    singleton_user = user('uj-singleton')
    RoleDefinition.objects.get(name='Organization Admin').give_permission(singleton_user, organization)

    project = Project.objects.create(name='uj-singleton-project', organization=organization)
    jt = JobTemplate.objects.create(name='uj-singleton-jt', project=project, inventory=inventory, organization=organization)
    job = jt.create_unified_job()

    inv_src = InventorySource.objects.create(name='uj-singleton-invsrc', inventory=inventory, source='ec2')
    inv_update = InventoryUpdate.objects.create(inventory_source=inv_src, source=inv_src.source)

    adhoc = AdHocCommand.objects.create(name='uj-singleton-adhoc', inventory=inventory)

    # Inject singleton permissions to exercise the shortcut branches in
    # filtered_queryset() without needing a global RoleDefinition.
    singleton_user._singleton_permissions = {
        'view_jobtemplate',
        'view_project',
        'view_workflowjobtemplate',
        'view_inventory',
        'audit_organization',
    }

    response = get(reverse('api:unified_job_list'), singleton_user)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert job.pk in result_ids
    assert inv_update.pk in result_ids
    assert adhoc.pk in result_ids


@pytest.mark.django_db
def test_unified_job_list_team_member_sees_team_granted_jobs(user, setup_managed_roles, get):
    """A user who can view a JT only through a team assignment must see
    the corresponding unified jobs in the list."""
    org = Organization.objects.create(name='uj-team-org')
    team = Team.objects.create(name='uj-test-team', organization=org)
    team_user = user('uj-team-member')

    RoleDefinition.objects.get(name='Team Member').give_permission(team_user, team)

    inventory = org.inventories.create(name='uj-team-inv')
    project = Project.objects.create(name='uj-team-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-team-jt', project=project, inventory=inventory, organization=org)
    RoleDefinition.objects.get(name='JobTemplate Execute').give_permission(team, jt)
    job = jt.create_unified_job()

    response = get(reverse('api:unified_job_list'), team_user)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert job.pk in result_ids, f"Team member should see job {job.pk} via team-granted JT execute permission, but got result IDs: {result_ids}"


@pytest.mark.django_db
def test_job_list_non_superuser_count_matches_visible_jobs(user, setup_managed_roles, get):
    """The job list count must include only jobs visible to the requesting user."""
    visible_org = Organization.objects.create(name='job-list-visible-org')
    visible_inventory = visible_org.inventories.create(name='job-list-visible-inv')
    visible_project = Project.objects.create(name='job-list-visible-project', organization=visible_org)
    visible_jt = JobTemplate.objects.create(
        name='job-list-visible-jt',
        project=visible_project,
        inventory=visible_inventory,
        organization=visible_org,
    )
    visible_job = visible_jt.create_unified_job()

    hidden_org = Organization.objects.create(name='job-list-hidden-org')
    hidden_inventory = hidden_org.inventories.create(name='job-list-hidden-inv')
    hidden_project = Project.objects.create(name='job-list-hidden-project', organization=hidden_org)
    hidden_jt = JobTemplate.objects.create(
        name='job-list-hidden-jt',
        project=hidden_project,
        inventory=hidden_inventory,
        organization=hidden_org,
    )
    hidden_jt.create_unified_job()

    org_admin = user('job-list-org-admin')
    RoleDefinition.objects.get(name='Organization Admin').give_permission(org_admin, visible_org)

    response = get(reverse('api:job_list'), org_admin)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert [result['id'] for result in response.data['results']] == [visible_job.pk]


@pytest.mark.django_db
def test_unified_job_list_rando_sees_nothing(rando, setup_managed_roles, get):
    """Unprivileged user sees no unified jobs."""
    org = Organization.objects.create(name='uj-rando-org')
    inventory = org.inventories.create(name='uj-rando-inv')
    project = Project.objects.create(name='uj-rando-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-rando-jt', project=project, inventory=inventory, organization=org)
    jt.create_unified_job()
    AdHocCommand.objects.create(name='uj-rando-adhoc', inventory=inventory)

    response = get(reverse('api:unified_job_list'), rando)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_unified_job_list_filtered_count_matches_results(admin, organization, inventory, setup_managed_roles, get):
    """When a filter narrows the result set, the pagination count must
    match the actual number of matching results, not the unfiltered
    table total."""
    project = Project.objects.create(name='uj-filtered-count-project', organization=organization)
    jt = JobTemplate.objects.create(name='uj-filtered-count-jt', project=project, inventory=inventory, organization=organization)

    jt.create_unified_job(_eager_fields={'status': 'running'})
    jt.create_unified_job(_eager_fields={'status': 'canceled'})

    response = get(reverse('api:unified_job_list') + '?status=canceled', admin)
    assert response.status_code == 200
    assert response.data['count'] == len(response.data['results']) == 1


@pytest.mark.django_db
def test_unified_job_list_pagination_count_matches_rbac_filtered_results(rando, setup_managed_roles, get):
    """The pagination count should reflect the RBAC-filtered result set,
    not the unfiltered table total.  A user who cannot see any jobs
    should see count == 0."""
    org = Organization.objects.create(name='uj-count-org')
    inventory = org.inventories.create(name='uj-count-inv')
    project = Project.objects.create(name='uj-count-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-count-jt', project=project, inventory=inventory, organization=org)
    jt.create_unified_job()

    total_jobs = UnifiedJob.objects.count()
    assert total_jobs > 0

    response = get(reverse('api:unified_job_list'), rando)
    assert response.status_code == 200
    assert len(response.data['results']) == 0
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_unified_job_list_count_matches_for_mixed_roles(admin, user, setup_managed_roles, get):
    """A user with a mix of roles should see a count that matches exactly
    the number of results they are permitted to view, not the global total."""
    org = Organization.objects.create(name='uj-mixed-count-org')
    inventory = org.inventories.create(name='uj-mixed-count-inv')
    project = Project.objects.create(name='uj-mixed-count-project', organization=org)

    # Two job templates — user will only get access to jt_visible
    jt_visible = JobTemplate.objects.create(name='uj-mixed-visible-jt', project=project, inventory=inventory, organization=org)
    jt_hidden = JobTemplate.objects.create(name='uj-mixed-hidden-jt', project=project, inventory=inventory, organization=org)

    visible_job_1 = jt_visible.create_unified_job()
    visible_job_2 = jt_visible.create_unified_job()
    jt_hidden.create_unified_job()
    jt_hidden.create_unified_job()

    # Inventory source — user will get access via inventory view
    inv_src = InventorySource.objects.create(name='uj-mixed-count-invsrc', inventory=inventory, source='ec2')
    visible_inv_update = InventoryUpdate.objects.create(inventory_source=inv_src, source=inv_src.source)

    # Ad hoc command — also visible via inventory view
    visible_adhoc = AdHocCommand.objects.create(name='uj-mixed-count-adhoc', inventory=inventory)

    mixed_user = user('uj-mixed-role-user')
    RoleDefinition.objects.get(name='JobTemplate Execute').give_permission(mixed_user, jt_visible)
    RoleDefinition.objects.get(name='Inventory Admin').give_permission(mixed_user, inventory)

    expected_visible_ids = {visible_job_1.pk, visible_job_2.pk, visible_inv_update.pk, visible_adhoc.pk}

    # Admin sees everything
    admin_response = get(reverse('api:unified_job_list'), admin)
    assert admin_response.status_code == 200
    assert admin_response.data['count'] == len(admin_response.data['results'])

    # Mixed-role user sees only their permitted jobs, and count matches
    user_response = get(reverse('api:unified_job_list'), mixed_user)
    assert user_response.status_code == 200
    user_result_ids = {r['id'] for r in user_response.data['results']}
    assert user_result_ids == expected_visible_ids
    assert user_response.data['count'] == len(expected_visible_ids)
    assert user_response.data['count'] < admin_response.data['count']


@pytest.mark.django_db
def test_unified_job_count_deduplicates_multiple_access_routes(user, setup_managed_roles, get):
    """A job reachable through multiple permission paths (direct JT role,
    org auditor role, and team role) must appear exactly once in the
    results and count."""
    org = Organization.objects.create(name="triple-route-org")
    inventory = org.inventories.create(name="triple-route-inventory")
    project = Project.objects.create(name="triple-route-project", organization=org)
    jt = JobTemplate.objects.create(
        name="triple-route-template",
        project=project,
        inventory=inventory,
        organization=org,
    )
    job = jt.create_unified_job()

    viewer = user("triple-route-viewer")

    RoleDefinition.objects.get(name="JobTemplate Execute").give_permission(viewer, jt)
    RoleDefinition.objects.get(name="Organization Audit").give_permission(viewer, org)

    team = Team.objects.create(name="triple-route-team", organization=org)
    team.member_role.members.add(viewer)
    RoleDefinition.objects.get(name="JobTemplate Execute").give_permission(team, jt)

    response = get(reverse("api:unified_job_list"), viewer)

    assert response.status_code == 200
    ids = [result["id"] for result in response.data["results"]]
    assert ids == [job.pk]
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_direct_jt_permission_only_sees_jt_jobs(user, setup_managed_roles, get):
    """A user with a direct JT permission (but no inventory or org permissions)
    sees only jobs from that JT — inventory updates are not visible."""
    org = Organization.objects.create(name='uj-direct-jt-org')
    inventory = org.inventories.create(name='uj-direct-jt-inv')
    project = Project.objects.create(name='uj-direct-jt-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-direct-jt', project=project, inventory=inventory, organization=org)
    job = jt.create_unified_job()

    inv_src = InventorySource.objects.create(name='uj-direct-jt-invsrc', inventory=inventory, source='ec2')
    inv_update = InventoryUpdate.objects.create(inventory_source=inv_src, source=inv_src.source)

    jt_viewer = user('uj-direct-jt-viewer')
    RoleDefinition.objects.get(name='JobTemplate Execute').give_permission(jt_viewer, jt)

    response = get(reverse('api:unified_job_list'), jt_viewer)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert job.pk in result_ids, "JT permission holder should see JT jobs"
    assert inv_update.pk not in result_ids, "JT permission holder should NOT see inventory updates"


@pytest.mark.django_db
def test_global_ujt_view_singleton_sees_all_template_jobs(user, setup_managed_roles, get):
    """A custom global role granting view on all UJT subclasses triggers
    the singleton shortcut and surfaces all template-based jobs."""
    org = Organization.objects.create(name='uj-global-ujt-org')
    inventory = org.inventories.create(name='uj-global-ujt-inv')
    project = Project.objects.create(name='uj-global-ujt-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-global-ujt-jt', project=project, inventory=inventory, organization=org)
    job = jt.create_unified_job()

    global_viewer = user('uj-global-ujt-viewer')
    rd = RoleDefinition.objects.create_from_permissions(
        name='global-ujt-viewer-test',
        permissions=['view_jobtemplate', 'view_project', 'view_workflowjobtemplate'],
        content_type=None,
        managed=True,
    )
    rd.give_global_permission(global_viewer)

    response = get(reverse('api:unified_job_list'), global_viewer)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert job.pk in result_ids, "Global UJT viewer should see JT jobs via singleton shortcut"


@pytest.mark.django_db
def test_global_view_inventory_sees_inventory_updates_and_adhoc(user, setup_managed_roles, get):
    """A custom global role granting only view_inventory lets the user see
    inventory updates and ad hoc commands but not JT-based jobs."""
    org = Organization.objects.create(name='uj-global-inv-org')
    inventory = org.inventories.create(name='uj-global-inv-test')
    project = Project.objects.create(name='uj-global-inv-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-global-inv-jt', project=project, inventory=inventory, organization=org)
    job = jt.create_unified_job()

    inv_src = InventorySource.objects.create(name='uj-global-inv-src', inventory=inventory, source='ec2')
    inv_update = InventoryUpdate.objects.create(inventory_source=inv_src, source=inv_src.source)
    adhoc = AdHocCommand.objects.create(name='uj-global-inv-adhoc', inventory=inventory)

    global_inv_viewer = user('uj-global-inv-viewer')
    rd = RoleDefinition.objects.create_from_permissions(
        name='global-inv-viewer-test',
        permissions=['view_inventory'],
        content_type=None,
        managed=True,
    )
    rd.give_global_permission(global_inv_viewer)

    response = get(reverse('api:unified_job_list'), global_inv_viewer)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert inv_update.pk in result_ids, "Global inventory viewer should see inventory updates"
    assert adhoc.pk in result_ids, "Global inventory viewer should see ad hoc commands"
    assert job.pk not in result_ids, "Global inventory viewer should NOT see JT jobs"


@pytest.mark.django_db
def test_unrelated_credential_role_sees_no_unified_jobs(user, setup_managed_roles, get):
    """A user with only credential permissions should see nothing in the
    unified job list — credential roles are unrelated to UJ visibility."""
    org = Organization.objects.create(name='uj-cred-org')
    inventory = org.inventories.create(name='uj-cred-inv')
    project = Project.objects.create(name='uj-cred-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-cred-jt', project=project, inventory=inventory, organization=org)
    jt.create_unified_job()

    ct = CredentialType.defaults['ssh']()
    ct.save()
    cred = Credential.objects.create(name='uj-test-cred', credential_type=ct, organization=org)

    cred_user = user('uj-cred-only')
    RoleDefinition.objects.get(name='Credential Admin').give_permission(cred_user, cred)

    response = get(reverse('api:unified_job_list'), cred_user)
    assert response.status_code == 200
    assert len(response.data['results']) == 0, "User with only credential perms should see no unified jobs"


@pytest.mark.django_db
def test_jt_role_plus_credential_role_only_shows_jt_jobs(user, setup_managed_roles, get):
    """A user with both a direct JT role and an unrelated credential role
    should only see jobs from the JT — the credential role must not
    pollute or interfere."""
    org = Organization.objects.create(name='uj-mixed-org')
    inventory = org.inventories.create(name='uj-mixed-inv')
    project = Project.objects.create(name='uj-mixed-project', organization=org)
    jt = JobTemplate.objects.create(name='uj-mixed-jt', project=project, inventory=inventory, organization=org)
    job = jt.create_unified_job()

    ct = CredentialType.defaults['ssh']()
    ct.save()
    cred = Credential.objects.create(name='uj-mixed-cred', credential_type=ct, organization=org)

    mixed_user = user('uj-mixed-user')
    RoleDefinition.objects.get(name='JobTemplate Execute').give_permission(mixed_user, jt)
    RoleDefinition.objects.get(name='Credential Admin').give_permission(mixed_user, cred)

    response = get(reverse('api:unified_job_list'), mixed_user)
    assert response.status_code == 200
    result_ids = [r['id'] for r in response.data['results']]
    assert job.pk in result_ids, "User should see JT job via direct JT permission"
    assert len(result_ids) == 1, f"User should only see the one JT job, got: {result_ids}"
