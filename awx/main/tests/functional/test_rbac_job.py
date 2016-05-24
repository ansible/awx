import pytest

from awx.main.access import JobAccess
from awx.main.models import Job


@pytest.fixture
def orphan_job(deploy_jobtemplate):
    return Job.objects.create(
        job_template=None,
        project=deploy_jobtemplate.project,
        inventory=deploy_jobtemplate.inventory
    )

@pytest.mark.django_db
def test_superuser_sees_orphans(admin_user, orphan_job):
    access = JobAccess(admin_user)
    assert access.can_read(orphan_job)

@pytest.mark.django_db
def test_org_member_does_not_see_orphans(org_member, orphan_job, project):
    # Check that privledged access to project still does not grant access
    project.admin_role.members.add(org_member)
    access = JobAccess(org_member)
    assert not access.can_read(orphan_job)

@pytest.mark.django_db
def test_org_admin_sees_orphans(org_admin, orphan_job):
    access = JobAccess(org_admin)
    assert access.can_read(orphan_job)

@pytest.mark.django_db
def test_org_auditor_sees_orphans(org_auditor, orphan_job):
    access = JobAccess(org_auditor)
    assert access.can_read(orphan_job)
