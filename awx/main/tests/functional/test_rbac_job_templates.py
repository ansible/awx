import mock
import pytest

from awx.api.versioning import reverse
from awx.main.access import (
    BaseAccess,
    JobTemplateAccess,
    ScheduleAccess
)
from awx.main.models.jobs import JobTemplate
from awx.main.models.schedules import Schedule


@pytest.fixture
def jt_objects(job_template_factory):
    objects = job_template_factory(
        'testJT', organization='org1', project='proj1', inventory='inventory1',
        credential='cred1', cloud_credential='aws1', network_credential='juniper1')
    return objects


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
def test_job_template_access_read_level(jt_objects, rando):

    access = JobTemplateAccess(rando)
    jt_objects.project.read_role.members.add(rando)
    jt_objects.inventory.read_role.members.add(rando)
    jt_objects.credential.read_role.members.add(rando)
    jt_objects.cloud_credential.read_role.members.add(rando)
    jt_objects.network_credential.read_role.members.add(rando)

    proj_pk = jt_objects.project.pk
    assert not access.can_add(dict(inventory=jt_objects.inventory.pk, project=proj_pk))
    assert not access.can_add(dict(credential=jt_objects.credential.pk, project=proj_pk))
    assert not access.can_add(dict(cloud_credential=jt_objects.cloud_credential.pk, project=proj_pk))
    assert not access.can_add(dict(network_credential=jt_objects.network_credential.pk, project=proj_pk))


@pytest.mark.django_db
def test_job_template_access_use_level(jt_objects, rando):

    access = JobTemplateAccess(rando)
    jt_objects.project.use_role.members.add(rando)
    jt_objects.inventory.use_role.members.add(rando)
    jt_objects.credential.use_role.members.add(rando)
    jt_objects.cloud_credential.use_role.members.add(rando)
    jt_objects.network_credential.use_role.members.add(rando)

    proj_pk = jt_objects.project.pk
    assert access.can_add(dict(inventory=jt_objects.inventory.pk, project=proj_pk))
    assert access.can_add(dict(credential=jt_objects.credential.pk, project=proj_pk))
    assert access.can_add(dict(cloud_credential=jt_objects.cloud_credential.pk, project=proj_pk))
    assert access.can_add(dict(network_credential=jt_objects.network_credential.pk, project=proj_pk))


@pytest.mark.django_db
def test_job_template_access_org_admin(jt_objects, rando):
    access = JobTemplateAccess(rando)
    # Appoint this user as admin of the organization
    jt_objects.inventory.organization.admin_role.members.add(rando)
    # Assign organization permission in the same way the create view does
    organization = jt_objects.inventory.organization
    jt_objects.credential.admin_role.parents.add(organization.admin_role)
    jt_objects.cloud_credential.admin_role.parents.add(organization.admin_role)
    jt_objects.network_credential.admin_role.parents.add(organization.admin_role)

    proj_pk = jt_objects.project.pk
    assert access.can_add(dict(inventory=jt_objects.inventory.pk, project=proj_pk))
    assert access.can_add(dict(credential=jt_objects.credential.pk, project=proj_pk))
    assert access.can_add(dict(cloud_credential=jt_objects.cloud_credential.pk, project=proj_pk))
    assert access.can_add(dict(network_credential=jt_objects.network_credential.pk, project=proj_pk))

    assert access.can_read(jt_objects.job_template)
    assert access.can_delete(jt_objects.job_template)


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
def test_job_template_creator_access(project, rando, post):

    project.admin_role.members.add(rando)
    with mock.patch(
            'awx.main.models.projects.ProjectOptions.playbooks',
            new_callable=mock.PropertyMock(return_value=['helloworld.yml'])):
        response = post(reverse('api:job_template_list'), dict(
            name='newly-created-jt',
            job_type='run',
            ask_inventory_on_launch=True,
            ask_credential_on_launch=True,
            project=project.pk,
            playbook='helloworld.yml'
        ), rando)

    assert response.status_code == 201
    jt_pk = response.data['id']
    jt_obj = JobTemplate.objects.get(pk=jt_pk)
    # Creating a JT should place the creator in the admin role
    assert rando in jt_obj.admin_role


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
