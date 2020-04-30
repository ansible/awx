from unittest import mock
import pytest

from awx.api.versioning import reverse
from awx.main.access import (
    BaseAccess,
    JobTemplateAccess,
    ScheduleAccess
)
from awx.main.models.jobs import JobTemplate
from awx.main.models import Project, Organization, Inventory, Schedule, User


@mock.patch.object(BaseAccess, 'check_license', return_value=None)
@pytest.mark.django_db
def test_job_template_access_superuser(check_license, user, deploy_jobtemplate):
    # GIVEN a superuser
    u = user('admin', True)
    # WHEN access to a job template is checked
    access = JobTemplateAccess(u)
    # THEN all access checks should pass
    assert access.can_read(deploy_jobtemplate)
    assert access.can_add({})


@pytest.mark.django_db
class TestImplicitAccess:
    def test_org_execute(self, jt_linked, rando):
        assert rando not in jt_linked.execute_role
        jt_linked.organization.execute_role.members.add(rando)
        assert rando in jt_linked.execute_role

    def test_org_admin(self, jt_linked, rando):
        assert rando not in jt_linked.execute_role
        jt_linked.organization.job_template_admin_role.members.add(rando)
        assert rando in jt_linked.execute_role

    def test_org_auditor(self, jt_linked, rando):
        assert rando not in jt_linked.read_role
        jt_linked.organization.auditor_role.members.add(rando)
        assert rando in jt_linked.read_role

    def test_deprecated_inventory_read(self, jt_linked, rando):
        assert rando not in jt_linked.read_role
        jt_linked.inventory.organization.execute_role.members.add(rando)
        assert rando in jt_linked.read_role


@pytest.mark.django_db
def test_job_template_access_read_level(jt_linked, rando):
    ssh_cred = jt_linked.machine_credential
    vault_cred = jt_linked.vault_credentials[0]

    access = JobTemplateAccess(rando)
    jt_linked.project.read_role.members.add(rando)
    jt_linked.inventory.read_role.members.add(rando)
    ssh_cred.read_role.members.add(rando)

    proj_pk = jt_linked.project.pk
    assert not access.can_add(dict(inventory=jt_linked.inventory.pk, project=proj_pk))
    assert not access.can_add(dict(credential=ssh_cred.pk, project=proj_pk))
    assert not access.can_add(dict(vault_credential=vault_cred.pk, project=proj_pk))

    for cred in jt_linked.credentials.all():
        assert not access.can_unattach(jt_linked, cred, 'credentials', {})


@pytest.mark.django_db
def test_project_use_access(project, rando):
    project.use_role.members.add(rando)
    access = JobTemplateAccess(rando)
    assert access.can_add(None)
    assert access.can_add({'project': project.id, 'ask_inventory_on_launch': True})
    project2 = Project.objects.create(
        name='second-project', scm_type=project.scm_type, playbook_files=project.playbook_files,
        organization=project.organization,
    )
    project2.use_role.members.add(rando)
    jt = JobTemplate.objects.create(project=project, ask_inventory_on_launch=True)
    jt.admin_role.members.add(rando)
    assert access.can_change(jt, {'project': project2.pk})


@pytest.mark.django_db
def test_job_template_access_use_level(jt_linked, rando):
    access = JobTemplateAccess(rando)
    jt_linked.project.use_role.members.add(rando)
    jt_linked.inventory.use_role.members.add(rando)
    jt_linked.admin_role.members.add(rando)
    proj_pk = jt_linked.project.pk

    assert access.can_change(jt_linked, {'job_type': 'check', 'project': proj_pk})
    assert access.can_change(jt_linked, {'job_type': 'check', 'inventory': None})

    for cred in jt_linked.credentials.all():
        assert access.can_unattach(jt_linked, cred, 'credentials', {})

    assert access.can_add(dict(inventory=jt_linked.inventory.pk, project=proj_pk))
    assert access.can_add(dict(project=proj_pk))


@pytest.mark.django_db
@pytest.mark.parametrize("role_names", [("admin_role",), ("job_template_admin_role", "inventory_admin_role", "project_admin_role")])
def test_job_template_access_admin(role_names, jt_linked, rando):
    ssh_cred = jt_linked.machine_credential

    access = JobTemplateAccess(rando)

    assert not access.can_read(jt_linked)
    assert not access.can_delete(jt_linked)

    # Appoint this user to the org role
    organization = jt_linked.organization
    for role_name in role_names:
        getattr(organization, role_name).members.add(rando)

    # Assign organization permission in the same way the create view does
    ssh_cred.admin_role.parents.add(organization.admin_role)

    proj_pk = jt_linked.project.pk
    assert access.can_add(dict(inventory=jt_linked.inventory.pk, project=proj_pk))

    for cred in jt_linked.credentials.all():
        assert access.can_unattach(jt_linked, cred, 'credentials', {})

    assert access.can_read(jt_linked)
    assert access.can_delete(jt_linked)


@pytest.mark.django_db
def test_job_template_credentials_prompts_access(
        rando, post, inventory, project, machine_credential, vault_credential):
    jt = JobTemplate.objects.create(
        name = 'test-jt',
        project = project,
        playbook = 'helloworld.yml',
        inventory = inventory,
        ask_credential_on_launch = True
    )
    jt.credentials.add(machine_credential)
    jt.execute_role.members.add(rando)
    post(
        reverse('api:job_template_launch', kwargs={'pk': jt.id}),
        {'credentials': [machine_credential.pk, vault_credential.pk]}, rando,
        expect=403
    )


@pytest.mark.django_db
class TestJobTemplateCredentials:

    def test_job_template_cannot_add_credentials(self, job_template, credential, rando):
        job_template.admin_role.members.add(rando)
        credential.read_role.members.add(rando)
        # without permission to credential, user can not attach it
        assert not JobTemplateAccess(rando).can_attach(
            job_template, credential, 'credentials', {})

    def test_job_template_can_add_credentials(self, job_template, credential, rando):
        job_template.admin_role.members.add(rando)
        credential.use_role.members.add(rando)
        # user has permission to apply credential
        assert JobTemplateAccess(rando).can_attach(
            job_template, credential, 'credentials', {})


@pytest.mark.django_db
class TestOrphanJobTemplate:

    def test_orphan_JT_readable_by_system_auditor(self, job_template, system_auditor):
        assert system_auditor.is_system_auditor
        assert job_template.project is None
        access = JobTemplateAccess(system_auditor)
        assert access.can_read(job_template)

    def test_system_admin_orphan_capabilities(self, job_template, admin_user):
        job_template.capabilities_cache = {'edit': False}
        access = JobTemplateAccess(admin_user)
        capabilities = access.get_user_capabilities(job_template, method_list=['edit'])
        assert capabilities['edit']


@pytest.mark.django_db
@pytest.mark.job_permissions
def test_job_template_creator_access(project, organization, rando, post):
    project.use_role.members.add(rando)
    response = post(url=reverse('api:job_template_list'), data=dict(
        name='newly-created-jt',
        ask_inventory_on_launch=True,
        project=project.pk,
        playbook='helloworld.yml'
    ), user=rando, expect=201)

    jt_pk = response.data['id']
    jt_obj = JobTemplate.objects.get(pk=jt_pk)
    # Creating a JT should place the creator in the admin role
    assert rando in jt_obj.admin_role.members.all()


@pytest.mark.django_db
@pytest.mark.job_permissions
@pytest.mark.parametrize('lacking', ['project', 'inventory'])
def test_job_template_insufficient_creator_permissions(lacking, project, inventory, organization, rando, post):
    if lacking != 'project':
        project.use_role.members.add(rando)
    else:
        project.read_role.members.add(rando)
    if lacking != 'inventory':
        inventory.use_role.members.add(rando)
    else:
        inventory.read_role.members.add(rando)
    post(url=reverse('api:job_template_list'), data=dict(
        name='newly-created-jt',
        inventory=inventory.id,
        project=project.pk,
        playbook='helloworld.yml'
    ), user=rando, expect=403)


@pytest.mark.django_db
def test_associate_label(label, user, job_template):
    access = JobTemplateAccess(user('joe', False))
    job_template.admin_role.members.add(user('joe', False))
    label.organization.read_role.members.add(user('joe', False))
    assert access.can_attach(job_template, label, 'labels', None)


@pytest.mark.django_db
class TestJobTemplateSchedules:

    rrule = 'DTSTART:20151117T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
    rrule2 = 'DTSTART:20151117T050000Z RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=1'

    @pytest.fixture
    def jt2(self):
        return JobTemplate.objects.create(name="other-jt")

    def test_move_schedule_to_JT_no_access(self, job_template, rando, jt2):
        schedule = Schedule.objects.create(unified_job_template=job_template, rrule=self.rrule)
        job_template.admin_role.members.add(rando)
        access = ScheduleAccess(rando)
        assert not access.can_change(schedule, data=dict(unified_job_template=jt2.pk))


    def test_move_schedule_from_JT_no_access(self, job_template, rando, jt2):
        schedule = Schedule.objects.create(unified_job_template=job_template, rrule=self.rrule)
        jt2.admin_role.members.add(rando)
        access = ScheduleAccess(rando)
        assert not access.can_change(schedule, data=dict(unified_job_template=jt2.pk))


    def test_can_create_schedule_with_execute(self, job_template, rando):
        job_template.execute_role.members.add(rando)
        access = ScheduleAccess(rando)
        assert access.can_add({'unified_job_template': job_template})


    def test_can_modify_ones_own_schedule(self, job_template, rando):
        job_template.execute_role.members.add(rando)
        schedule = Schedule.objects.create(unified_job_template=job_template, rrule=self.rrule, created_by=rando)
        access = ScheduleAccess(rando)
        assert access.can_change(schedule, {'rrule': self.rrule2})

    def test_prompts_access_checked(self, job_template, inventory, credential, rando):
        job_template.execute_role.members.add(rando)
        access = ScheduleAccess(rando)
        data = dict(
            unified_job_template=job_template,
            rrule=self.rrule,
            created_by=rando,
            inventory=inventory,
            credentials=[credential]
        )
        with mock.patch('awx.main.access.JobLaunchConfigAccess.can_add') as mock_add:
            mock_add.return_value = True
            assert access.can_add(data)
            mock_add.assert_called_once_with(data)
        data.pop('credentials')
        schedule = Schedule.objects.create(**data)
        with mock.patch('awx.main.access.JobLaunchConfigAccess.can_change') as mock_change:
            mock_change.return_value = True
            assert access.can_change(schedule, {'inventory': 42})
            mock_change.assert_called_once_with(schedule, {'inventory': 42})


@pytest.mark.django_db
class TestProjectOrganization:
    """Tests stories related to management of JT organization via its project
    which have some bearing on RBAC integrity
    """

    def test_new_project_org_change(self, project, patch, admin_user):
        org2 = Organization.objects.create(name='bar')
        patch(
            url=project.get_absolute_url(),
            data={'organization': org2.id},
            user=admin_user,
            expect=200
        )
        assert Project.objects.get(pk=project.id).organization_id == org2.id

    def test_jt_org_cannot_change(self, project, post, patch, admin_user):
        post(
            url=reverse('api:job_template_list'),
            data={
                'name': 'foo_template',
                'project': project.id,
                'playbook': 'helloworld.yml',
                'ask_inventory_on_launch': True
            },
            user=admin_user,
            expect=201
        )
        org2 = Organization.objects.create(name='bar')
        r = patch(
            url=project.get_absolute_url(),
            data={'organization': org2.id},
            user=admin_user,
            expect=400
        )
        assert 'Organization cannot be changed' in str(r.data)

    def test_orphan_JT_adoption(self, project, patch, admin_user, org_admin):
        jt = JobTemplate.objects.create(
            name='bar',
            ask_inventory_on_launch=True,
            playbook='helloworld.yml'
        )
        assert org_admin not in jt.admin_role
        patch(
            url=jt.get_absolute_url(),
            data={'project': project.id},
            user=admin_user,
            expect=200
        )
        assert org_admin in jt.admin_role

    def test_inventory_read_transfer_direct(self, patch):
        orgs = []
        invs = []
        admins = []
        for i in range(2):
            org = Organization.objects.create(name='org{}'.format(i))
            org_admin = User.objects.create(username='user{}'.format(i))
            inv = Inventory.objects.create(
                organization=org,
                name='inv{}'.format(i)
            )
            org.auditor_role.members.add(org_admin)

            orgs.append(org)
            admins.append(org_admin)
            invs.append(inv)

        jt = JobTemplate.objects.create(name='foo', inventory=invs[0])
        assert admins[0] in jt.read_role
        assert admins[1] not in jt.read_role

        jt.inventory = invs[1]
        jt.save(update_fields=['inventory'])
        assert admins[0] not in jt.read_role
        assert admins[1] in jt.read_role

    def test_inventory_read_transfer_indirect(self, patch):
        orgs = []
        admins = []
        for i in range(2):
            org = Organization.objects.create(name='org{}'.format(i))
            org_admin = User.objects.create(username='user{}'.format(i))
            org.auditor_role.members.add(org_admin)

            orgs.append(org)
            admins.append(org_admin)

        inv = Inventory.objects.create(
            organization=orgs[0],
            name='inv{}'.format(i)
        )

        jt = JobTemplate.objects.create(name='foo', inventory=inv)
        assert admins[0] in jt.read_role
        assert admins[1] not in jt.read_role

        inv.organization = orgs[1]
        inv.save(update_fields=['organization'])
        assert admins[0] not in jt.read_role
        assert admins[1] in jt.read_role
