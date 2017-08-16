import pytest

from awx.main.access import (
    JobAccess,
    AdHocCommandAccess,
    InventoryUpdateAccess,
    ProjectUpdateAccess
)
from awx.main.models import (
    Job,
    JobTemplate,
    AdHocCommand,
    InventoryUpdate,
    InventorySource,
    ProjectUpdate,
    User
)


@pytest.fixture
def normal_job(deploy_jobtemplate):
    return Job.objects.create(
        job_template=deploy_jobtemplate,
        project=deploy_jobtemplate.project,
        inventory=deploy_jobtemplate.inventory
    )


@pytest.fixture
def jt_user(deploy_jobtemplate, rando):
    deploy_jobtemplate.execute_role.members.add(rando)
    return rando


@pytest.fixture
def inv_updater(inventory, rando):
    inventory.update_role.members.add(rando)
    return rando


@pytest.fixture
def host_adhoc(host, machine_credential, rando):
    host.inventory.adhoc_role.members.add(rando)
    machine_credential.use_role.members.add(rando)
    return rando


@pytest.fixture
def proj_updater(project, rando):
    project.update_role.members.add(rando)
    return rando


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
def test_delete_job_with_orphan_proj(normal_job, rando):
    normal_job.project.organization = None
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


@pytest.mark.django_db
class TestJobRelaunchAccess:

    def test_job_relaunch_normal_resource_access(self, user, inventory, machine_credential):
        job_with_links = Job.objects.create(name='existing-job', credential=machine_credential, inventory=inventory)
        inventory_user = user('user1', False)
        credential_user = user('user2', False)
        both_user = user('user3', False)

        # Confirm that a user with inventory & credential access can launch
        job_with_links.credential.use_role.members.add(both_user)
        job_with_links.inventory.use_role.members.add(both_user)
        assert both_user.can_access(Job, 'start', job_with_links, validate_license=False)

        # Confirm that a user with credential access alone cannot launch
        job_with_links.credential.use_role.members.add(credential_user)
        assert not credential_user.can_access(Job, 'start', job_with_links, validate_license=False)

        # Confirm that a user with inventory access alone cannot launch
        job_with_links.inventory.use_role.members.add(inventory_user)
        assert not inventory_user.can_access(Job, 'start', job_with_links, validate_license=False)

    def test_job_relaunch_extra_credential_access(
            self, inventory, project, credential, net_credential):
        jt = JobTemplate.objects.create(name='testjt', inventory=inventory, project=project)
        jt.extra_credentials.add(credential)
        job = jt.create_unified_job()

        # Job is unchanged from JT, user has ability to launch
        jt_user = User.objects.create(username='jobtemplateuser')
        jt.execute_role.members.add(jt_user)
        assert jt_user in job.job_template.execute_role
        assert jt_user.can_access(Job, 'start', job, validate_license=False)

        # Job has prompted extra_credential, launch denied w/ message
        job.extra_credentials.add(net_credential)
        assert not jt_user.can_access(Job, 'start', job, validate_license=False)

    def test_prompted_extra_credential_relaunch_denied(
            self, inventory, project, net_credential, rando):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            ask_credential_on_launch=True)
        job = jt.create_unified_job()
        jt.execute_role.members.add(rando)

        # Job has prompted extra_credential, rando lacks permission to use it
        job.extra_credentials.add(net_credential)
        assert not rando.can_access(Job, 'start', job, validate_license=False)

    def test_prompted_extra_credential_relaunch_allowed(
            self, inventory, project, net_credential, rando):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            ask_credential_on_launch=True)
        job = jt.create_unified_job()
        jt.execute_role.members.add(rando)

        # Job has prompted extra_credential, but rando can use it
        net_credential.use_role.members.add(rando)
        job.extra_credentials.add(net_credential)
        assert rando.can_access(Job, 'start', job, validate_license=False)

    def test_extra_credential_relaunch_recreation_permission(
            self, inventory, project, net_credential, credential, rando):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            credential=credential, ask_credential_on_launch=True)
        job = jt.create_unified_job()
        project.admin_role.members.add(rando)
        inventory.admin_role.members.add(rando)
        credential.admin_role.members.add(rando)

        # Relaunch blocked by the extra credential
        job.extra_credentials.add(net_credential)
        assert not rando.can_access(Job, 'start', job, validate_license=False)


@pytest.mark.django_db
class TestJobAndUpdateCancels:

    # used in view: job_template_launch
    def test_jt_self_cancel(self, deploy_jobtemplate, jt_user):
        job = Job(job_template=deploy_jobtemplate, created_by=jt_user)
        access = JobAccess(jt_user)
        assert access.can_cancel(job)

    def test_jt_friend_cancel(self, deploy_jobtemplate, admin_user, jt_user):
        job = Job(job_template=deploy_jobtemplate, created_by=admin_user)
        access = JobAccess(jt_user)
        assert not access.can_cancel(job)

    def test_jt_org_admin_cancel(self, deploy_jobtemplate, org_admin, jt_user):
        job = Job(job_template=deploy_jobtemplate, created_by=jt_user)
        access = JobAccess(org_admin)
        assert access.can_cancel(job)

    # used in view: host_ad_hoc_commands_list
    def test_host_self_cancel(self, host, host_adhoc):
        adhoc_command = AdHocCommand(inventory=host.inventory, created_by=host_adhoc)
        access = AdHocCommandAccess(host_adhoc)
        assert access.can_cancel(adhoc_command)

    def test_host_friend_cancel(self, host, admin_user, host_adhoc):
        adhoc_command = AdHocCommand(inventory=host.inventory, created_by=admin_user)
        access = AdHocCommandAccess(host_adhoc)
        assert not access.can_cancel(adhoc_command)

    # used in view: inventory_source_update_view
    def test_inventory_self_cancel(self, inventory, inv_updater):
        inventory_update = InventoryUpdate(inventory_source=InventorySource(
            name=inventory.name, inventory=inventory, source='gce'
        ), created_by=inv_updater)
        access = InventoryUpdateAccess(inv_updater)
        assert access.can_cancel(inventory_update)

    def test_inventory_friend_cancel(self, inventory, admin_user, inv_updater):
        inventory_update = InventoryUpdate(inventory_source=InventorySource(
            name=inventory.name, inventory=inventory, source='gce'
        ), created_by=admin_user)
        access = InventoryUpdateAccess(inv_updater)
        assert not access.can_cancel(inventory_update)

    # used in view: project_update_view
    def test_project_self_cancel(self, project, proj_updater):
        project_update = ProjectUpdate(project=project, created_by=proj_updater)
        access = ProjectUpdateAccess(proj_updater)
        assert access.can_cancel(project_update)

    def test_project_friend_cancel(self, project, admin_user, proj_updater):
        project_update = ProjectUpdate(project=project, created_by=admin_user)
        access = ProjectUpdateAccess(proj_updater)
        assert not access.can_cancel(project_update)
