import pytest

from awx.main.access import JobAccess
from awx.main.models import Job


@pytest.fixture
def normal_job(deploy_jobtemplate):
    return Job.objects.create(
        job_template=deploy_jobtemplate,
        project=deploy_jobtemplate.project,
        inventory=deploy_jobtemplate.inventory
    )

# Read permissions testing
@pytest.mark.django_db
def test_superuser_sees_orphans(normal_job, admin_user):
    normal_job.job_template = None
    access = JobAccess(admin_user)
    assert access.can_read(normal_job)

@pytest.mark.django_db
def test_org_member_does_not_see_orphans(normal_job, org_member, project):
    normal_job.job_template = None
    # Check that privledged access to project still does not grant access
    project.admin_role.members.add(org_member)
    access = JobAccess(org_member)
    assert not access.can_read(normal_job)

@pytest.mark.django_db
def test_org_admin_sees_orphans(normal_job, org_admin):
    normal_job.job_template = None
    access = JobAccess(org_admin)
    assert access.can_read(normal_job)

@pytest.mark.django_db
def test_org_auditor_sees_orphans(normal_job, org_auditor):
    normal_job.job_template = None
    access = JobAccess(org_auditor)
    assert access.can_read(normal_job)

# Delete permissions testing
@pytest.mark.django_db
def test_JT_admin_delete_denied(normal_job, rando):
    normal_job.job_template.admin_role.members.add(rando)
    access = JobAccess(rando)
    assert not access.can_delete(normal_job)

@pytest.mark.django_db
def test_inventory_admin_delete_denied(normal_job, rando):
    normal_job.job_template.inventory.admin_role.members.add(rando)
    access = JobAccess(rando)
    assert not access.can_delete(normal_job)

@pytest.mark.django_db
def test_null_related_delete_denied(normal_job, rando):
    normal_job.project = None
    normal_job.inventory = None
    access = JobAccess(rando)
    assert not access.can_delete(normal_job)

@pytest.mark.django_db
def test_inventory_org_admin_delete_allowed(normal_job, org_admin):
    normal_job.project = None # do this so we test job->inventory->org->admin connection
    access = JobAccess(org_admin)
    assert access.can_delete(normal_job)

@pytest.mark.django_db
def test_project_org_admin_delete_allowed(normal_job, org_admin):
    normal_job.inventory = None # do this so we test job->project->org->admin connection
    access = JobAccess(org_admin)
    assert access.can_delete(normal_job)
