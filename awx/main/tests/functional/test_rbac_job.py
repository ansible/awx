import pytest

from rest_framework.exceptions import PermissionDenied

from awx.main.access import (
    JobAccess,
    JobLaunchConfigAccess,
    AdHocCommandAccess,
    InventoryUpdateAccess,
    ProjectUpdateAccess
)
from awx.main.models import (
    Job,
    JobLaunchConfig,
    JobTemplate,
    AdHocCommand,
    InventoryUpdate,
    InventorySource,
    ProjectUpdate,
    User,
    Credential
)

from crum import impersonate


@pytest.fixture
def normal_job(deploy_jobtemplate):
    return Job.objects.create(
        job_template=deploy_jobtemplate,
        project=deploy_jobtemplate.project,
        inventory=deploy_jobtemplate.inventory,
        organization=deploy_jobtemplate.organization
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


# Check that superuser & system auditors can see fully orphaned jobs
@pytest.mark.django_db
@pytest.mark.parametrize("superuser", [True, False])
def test_superuser_superauditor_sees_orphans(normal_job, superuser, admin_user, system_auditor):
    if superuser:
        u = admin_user
    else:
        u = system_auditor
    normal_job.job_template = None
    normal_job.project = None
    normal_job.inventory = None
    access = JobAccess(u)
    assert access.can_read(normal_job), "User sys auditor: {}, sys admin: {}".format(
        u.is_system_auditor, u.is_superuser)


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

    @pytest.mark.parametrize("inv_access,cred_access,can_start", [
        (True, True, True),  # Confirm that a user with inventory & credential access can launch
        (False, True, False),  # Confirm that a user with credential access alone cannot launch
        (True, False, False),  # Confirm that a user with inventory access alone cannot launch
    ])
    def test_job_relaunch_resource_access(self, user, inventory, machine_credential,
                                          inv_access, cred_access, can_start):
        job_template = JobTemplate.objects.create(
            ask_inventory_on_launch=True,
            ask_credential_on_launch=True
        )
        u = user('user1', False)
        job_with_links = Job.objects.create(
            name='existing-job', inventory=inventory, job_template=job_template,
            created_by=u
        )
        job_with_links.credentials.add(machine_credential)
        JobLaunchConfig.objects.create(job=job_with_links, inventory=inventory)
        job_with_links.launch_config.credentials.add(machine_credential)  # credential was prompted
        job_template.execute_role.members.add(u)
        if inv_access:
            job_with_links.inventory.use_role.members.add(u)
        if cred_access:
            machine_credential.use_role.members.add(u)

        access = JobAccess(u)
        if can_start:
            assert access.can_start(job_with_links, validate_license=False)
        else:
            with pytest.raises(PermissionDenied):
                access.can_start(job_with_links, validate_license=False)

    def test_job_relaunch_credential_access(
            self, inventory, project, credential, net_credential):
        jt = JobTemplate.objects.create(name='testjt', inventory=inventory, project=project)
        jt.credentials.add(credential)
        job = jt.create_unified_job()

        # Job is unchanged from JT, user has ability to launch
        jt_user = User.objects.create(username='jobtemplateuser')
        jt.execute_role.members.add(jt_user)
        assert jt_user.can_access(Job, 'start', job, validate_license=False)

        # Job has prompted net credential, launch denied w/ message
        job = jt.create_unified_job(credentials=[net_credential])
        with pytest.raises(PermissionDenied):
            jt_user.can_access(Job, 'start', job, validate_license=False)

    def test_prompted_credential_relaunch_denied(
            self, inventory, project, net_credential, rando):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            ask_credential_on_launch=True)
        job = jt.create_unified_job()
        jt.execute_role.members.add(rando)
        assert rando.can_access(Job, 'start', job, validate_license=False)

        # Job has prompted net credential, rando lacks permission to use it
        job = jt.create_unified_job(credentials=[net_credential])
        with pytest.raises(PermissionDenied):
            rando.can_access(Job, 'start', job, validate_license=False)

    def test_prompted_credential_relaunch_allowed(
            self, inventory, project, net_credential, rando):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            ask_credential_on_launch=True)
        job = jt.create_unified_job()
        jt.execute_role.members.add(rando)

        # Job has prompted net credential, but rando can use it
        net_credential.use_role.members.add(rando)
        job.credentials.add(net_credential)
        assert rando.can_access(Job, 'start', job, validate_license=False)

    def test_credential_relaunch_recreation_permission(
            self, inventory, project, net_credential, credential, rando):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            ask_credential_on_launch=True)
        job = jt.create_unified_job()
        project.admin_role.members.add(rando)
        inventory.admin_role.members.add(rando)
        credential.admin_role.members.add(rando)

        # Relaunch blocked by the net credential
        job.credentials.add(credential)
        job.credentials.add(net_credential)
        assert not rando.can_access(Job, 'start', job, validate_license=False)

    @pytest.mark.job_runtime_vars
    def test_callback_relaunchable_by_user(self, job_template, rando):
        with impersonate(rando):
            job = job_template.create_unified_job(
                _eager_fields={'launch_type': 'callback'},
                limit='host2'
            )
        assert 'limit' in job.launch_config.prompts_dict()  # sanity assertion
        job_template.execute_role.members.add(rando)
        can_access, messages = rando.can_access_with_errors(Job, 'start', job, validate_license=False)
        assert can_access, messages

    def test_other_user_prompts(self, inventory, project, alice, bob):
        jt = JobTemplate.objects.create(
            name='testjt', inventory=inventory, project=project,
            ask_credential_on_launch=True,
            ask_variables_on_launch=True)
        jt.execute_role.members.add(alice, bob)

        with impersonate(bob):
            job = jt.create_unified_job(extra_vars={'job_var': 'foo2', 'my_secret': '$encrypted$foo'})

        assert 'job_var' in job.launch_config.extra_data
        assert bob.can_access(Job, 'start', job, validate_license=False)
        with pytest.raises(PermissionDenied):
            alice.can_access(Job, 'start', job, validate_license=False)


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


@pytest.mark.django_db
class TestLaunchConfigAccess:

    def _make_two_credentials(self, cred_type):
        return (
            Credential.objects.create(
                credential_type=cred_type, name='machine-cred-1',
                inputs={'username': 'test_user', 'password': 'pas4word'}),
            Credential.objects.create(
                credential_type=cred_type, name='machine-cred-2',
                inputs={'username': 'test_user', 'password': 'pas4word'})
        )

    def test_new_credentials_access(self, credentialtype_ssh, rando):
        access = JobLaunchConfigAccess(rando)
        cred1, cred2 = self._make_two_credentials(credentialtype_ssh)

        assert not access.can_add({'credentials': [cred1, cred2]})  # can't add either
        cred1.use_role.members.add(rando)
        assert not access.can_add({'credentials': [cred1, cred2]})  # can't add 1
        cred2.use_role.members.add(rando)
        assert access.can_add({'credentials': [cred1, cred2]})  # can add both

    def test_obj_credentials_access(self, credentialtype_ssh, rando):
        job = Job.objects.create()
        config = JobLaunchConfig.objects.create(job=job)
        access = JobLaunchConfigAccess(rando)
        cred1, cred2 = self._make_two_credentials(credentialtype_ssh)

        assert access.has_credentials_access(config)  # has access if 0 creds
        config.credentials.add(cred1, cred2)
        assert not access.has_credentials_access(config)  # lacks access to both
        cred1.use_role.members.add(rando)
        assert not access.has_credentials_access(config)  # lacks access to 1
        cred2.use_role.members.add(rando)
        assert access.has_credentials_access(config)  # has access to both

    def test_can_use_minor(self, rando):
        # Config object only has flat-field overrides, no RBAC restrictions
        job = Job.objects.create()
        config = JobLaunchConfig.objects.create(job=job)
        access = JobLaunchConfigAccess(rando)

        assert access.can_use(config)
        assert rando.can_access(JobLaunchConfig, 'use', config)
