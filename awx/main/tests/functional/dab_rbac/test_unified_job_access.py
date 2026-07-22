import pytest

from django.test.utils import CaptureQueriesContext
from django.db import connection

from ansible_base.rbac.models import RoleDefinition

from awx.api.versioning import reverse
from awx.main.models import (
    AdHocCommand,
    InventorySource,
    InventoryUpdate,
    JobTemplate,
    Organization,
    Project,
    UnifiedJob,
)


@pytest.mark.django_db
def test_unified_job_list_uses_union(user, organization, inventory, setup_managed_roles, get):
    """The unified job list RBAC query uses UNION instead of OR to allow per-branch query planning."""
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

    uj_rbac_queries = [q['sql'] for q in ctx.captured_queries if 'UNION' in q['sql'] and 'main_unifiedjob' in q['sql']]
    assert uj_rbac_queries, "Expected at least one query using UNION for unified job RBAC filtering"


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
def test_unified_job_list_pagination_uses_unfiltered_count(rando, setup_managed_roles, get):
    """The pagination count should reflect total unified job rows, not
    the RBAC-filtered subset.  The RBAC-filtered COUNT is catastrophically
    slow on large tables with pk__in UNION subqueries."""
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
    assert response.data['count'] == total_jobs
