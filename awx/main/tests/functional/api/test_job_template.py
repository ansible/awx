import pytest
import mock

# AWX
from awx.api.serializers import JobTemplateSerializer, JobLaunchSerializer
from awx.main.models.jobs import JobTemplate, Job
from awx.main.models.projects import ProjectOptions
from awx.main.migrations import _save_password_keys as save_password_keys

# Django
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.apps import apps

@property
def project_playbooks(self):
    return ['mocked', 'mocked.yml', 'alt-mocked.yml']

@pytest.mark.django_db
@mock.patch.object(ProjectOptions, "playbooks", project_playbooks)
@pytest.mark.parametrize(
    "grant_project, grant_credential, grant_inventory, expect", [
        (True, True, True, 201),
        (True, True, False, 403),
        (True, False, True, 403),
        (False, True, True, 403),
    ]
)
def test_create(post, project, machine_credential, inventory, alice, grant_project, grant_credential, grant_inventory, expect):
    if grant_project:
        project.use_role.members.add(alice)
    if grant_credential:
        machine_credential.use_role.members.add(alice)
    if grant_inventory:
        inventory.use_role.members.add(alice)

    post(reverse('api:job_template_list'), {
        'name': 'Some name',
        'project': project.id,
        'credential': machine_credential.id,
        'inventory': inventory.id,
        'playbook': 'mocked.yml',
    }, alice, expect=expect)

@pytest.mark.django_db
@mock.patch.object(ProjectOptions, "playbooks", project_playbooks)
@pytest.mark.parametrize(
    "grant_project, grant_credential, grant_inventory, expect", [
        (True, True, True, 200),
        (True, True, False, 403),
        (True, False, True, 403),
        (False, True, True, 403),
    ]
)
def test_edit_sensitive_fields(patch, job_template_factory, alice, grant_project, grant_credential, grant_inventory, expect):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    objs.job_template.admin_role.members.add(alice)

    if grant_project:
        objs.project.use_role.members.add(alice)
    if grant_credential:
        objs.credential.use_role.members.add(alice)
    if grant_inventory:
        objs.inventory.use_role.members.add(alice)

    patch(reverse('api:job_template_detail', args=(objs.job_template.id,)), {
        'name': 'Some name',
        'project': objs.project.id,
        'credential': objs.credential.id,
        'inventory': objs.inventory.id,
        'playbook': 'alt-mocked.yml',
    }, alice, expect=expect)

@pytest.mark.django_db
@mock.patch.object(ProjectOptions, "playbooks", project_playbooks)
def test_edit_playbook(patch, job_template_factory, alice):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    objs.job_template.admin_role.members.add(alice)
    objs.project.use_role.members.add(alice)
    objs.credential.use_role.members.add(alice)
    objs.inventory.use_role.members.add(alice)

    patch(reverse('api:job_template_detail', args=(objs.job_template.id,)), {
        'playbook': 'alt-mocked.yml',
    }, alice, expect=200)

    objs.inventory.use_role.members.remove(alice)
    patch(reverse('api:job_template_detail', args=(objs.job_template.id,)), {
        'playbook': 'mocked.yml',
    }, alice, expect=403)

@pytest.mark.django_db
@mock.patch.object(ProjectOptions, "playbooks", project_playbooks)
def test_edit_nonsenstive(patch, job_template_factory, alice):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    jt = objs.job_template
    jt.admin_role.members.add(alice)

    res = patch(reverse('api:job_template_detail', args=(jt.id,)), {
        'name': 'updated',
        'description': 'bar',
        'forks': 14,
        'limit': 'something',
        'verbosity': 5,
        'extra_vars': '--',
        'job_tags': 'sometags',
        'force_handlers': True,
        'skip_tags': 'thistag,thattag',
        'ask_variables_on_launch':True,
        'ask_tags_on_launch':True,
        'ask_skip_tags_on_launch':True,
        'ask_job_type_on_launch':True,
        'ask_inventory_on_launch':True,
        'ask_credential_on_launch': True,
    }, alice, expect=200)
    print(res.data)
    assert res.data['name'] == 'updated'
@pytest.fixture
def jt_copy_edit(job_template_factory, project):
    objects = job_template_factory(
        'copy-edit-job-template',
        project=project)
    return objects.job_template

@property
def project_playbooks(self):
    return ['mocked', 'mocked.yml', 'alt-mocked.yml']

@pytest.mark.django_db
def test_job_template_role_user(post, organization_factory, job_template_factory):
    objects = organization_factory("org",
                                   superusers=['admin'],
                                   users=['test'])

    jt_objects = job_template_factory("jt",
                                      organization=objects.organization,
                                      inventory='test_inv',
                                      project='test_proj')

    url = reverse('api:user_roles_list', args=(objects.users.test.pk,))
    response = post(url, dict(id=jt_objects.job_template.execute_role.pk), objects.superusers.admin)
    assert response.status_code == 204

# Test protection against limited set of validation problems

@pytest.mark.django_db
def test_bad_data_copy_edit(admin_user, project):
    """
    If a required resource (inventory here) was deleted, copying not allowed
    because doing so would caues a validation error
    """

    jt_res = JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=None,  ask_inventory_on_launch=False, # not allowed
        credential=None, ask_credential_on_launch=True,
        name='deploy-job-template'
    )
    serializer = JobTemplateSerializer(jt_res)
    request = RequestFactory().get('/api/v1/job_templates/12/')
    request.user = admin_user
    serializer.context['request'] = request
    response = serializer.to_representation(jt_res)
    assert not response['summary_fields']['can_copy']
    assert response['summary_fields']['can_edit']

# Tests for correspondence between view info and actual access

@pytest.mark.django_db
def test_admin_copy_edit(jt_copy_edit, admin_user):
    "Absent a validation error, system admins can do everything"

    # Serializer can_copy/can_edit fields
    serializer = JobTemplateSerializer(jt_copy_edit)
    request = RequestFactory().get('/api/v1/job_templates/12/')
    request.user = admin_user
    serializer.context['request'] = request
    response = serializer.to_representation(jt_copy_edit)
    assert response['summary_fields']['can_copy']
    assert response['summary_fields']['can_edit']

@pytest.mark.django_db
def test_org_admin_copy_edit(jt_copy_edit, org_admin):
    "Organization admins SHOULD be able to copy a JT firmly in their org"

    # Serializer can_copy/can_edit fields
    serializer = JobTemplateSerializer(jt_copy_edit)
    request = RequestFactory().get('/api/v1/job_templates/12/')
    request.user = org_admin
    serializer.context['request'] = request
    response = serializer.to_representation(jt_copy_edit)
    assert response['summary_fields']['can_copy']
    assert response['summary_fields']['can_edit']

@pytest.mark.django_db
def test_org_admin_foreign_cred_no_copy_edit(jt_copy_edit, org_admin, machine_credential):
    """
    Organization admins without access to the 3 related resources:
    SHOULD NOT be able to copy JT
    SHOULD be able to edit that job template, for nonsensitive changes
    """

    # Attach credential to JT that org admin can not use
    jt_copy_edit.credential = machine_credential
    jt_copy_edit.save()

    # Serializer can_copy/can_edit fields
    serializer = JobTemplateSerializer(jt_copy_edit)
    request = RequestFactory().get('/api/v1/job_templates/12/')
    request.user = org_admin
    serializer.context['request'] = request
    response = serializer.to_representation(jt_copy_edit)
    assert not response['summary_fields']['can_copy']
    assert response['summary_fields']['can_edit']

@pytest.mark.django_db
def test_jt_admin_copy_edit(jt_copy_edit, rando):
    """
    JT admins wihout access to associated resources SHOULD NOT be able to copy
    SHOULD be able to make nonsensitive changes"""

    # random user given JT admin access only
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()

    # Serializer can_copy/can_edit fields
    serializer = JobTemplateSerializer(jt_copy_edit)
    request = RequestFactory().get('/api/v1/job_templates/12/')
    request.user = rando
    serializer.context['request'] = request
    response = serializer.to_representation(jt_copy_edit)
    assert not response['summary_fields']['can_copy']
    assert response['summary_fields']['can_edit']

@pytest.mark.django_db
def test_proj_jt_admin_copy_edit(jt_copy_edit, rando):
    "JT admins with access to associated resources SHOULD be able to copy"

    # random user given JT and project admin abilities
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()
    jt_copy_edit.project.admin_role.members.add(rando)
    jt_copy_edit.project.save()

    # Serializer can_copy/can_edit fields
    serializer = JobTemplateSerializer(jt_copy_edit)
    request = RequestFactory().get('/api/v1/job_templates/12/')
    request.user = rando
    serializer.context['request'] = request
    response = serializer.to_representation(jt_copy_edit)
    assert response['summary_fields']['can_copy']
    assert response['summary_fields']['can_edit']

# Functional tests - create new JT with all returned fields, as the UI does

@pytest.mark.django_db
@mock.patch.object(ProjectOptions, "playbooks", project_playbooks)
def test_org_admin_copy_edit_functional(jt_copy_edit, org_admin, get, post):
    get_response = get(reverse('api:job_template_detail', args=[jt_copy_edit.pk]), user=org_admin)
    assert get_response.status_code == 200
    assert get_response.data['summary_fields']['can_copy']

    post_data = get_response.data
    post_data['name'] = '%s @ 12:19:47 pm' % post_data['name']
    post_response = post(reverse('api:job_template_list', args=[]), user=org_admin, data=post_data)
    assert post_response.status_code == 201
    assert post_response.data['name'] == 'copy-edit-job-template @ 12:19:47 pm'

@pytest.mark.django_db
@mock.patch.object(ProjectOptions, "playbooks", project_playbooks)
def test_jt_admin_copy_edit_functional(jt_copy_edit, rando, get, post):

    # Grant random user JT admin access only
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()

    get_response = get(reverse('api:job_template_detail', args=[jt_copy_edit.pk]), user=rando)
    assert get_response.status_code == 200
    assert not get_response.data['summary_fields']['can_copy']

    post_data = get_response.data
    post_data['name'] = '%s @ 12:19:47 pm' % post_data['name']
    post_response = post(reverse('api:job_template_list', args=[]), user=rando, data=post_data)
    assert post_response.status_code == 403

@pytest.mark.django_db
def test_scan_jt_no_inventory(job_template_factory):
    # A user should be able to create a scan job without a project, but an inventory is required
    objects = job_template_factory('jt',
                                   credential='c',
                                   job_type="scan",
                                   project='p',
                                   inventory='i',
                                   organization='o')
    serializer = JobTemplateSerializer(data={"name": "Test", "job_type": "scan",
                                             "project": None, "inventory": objects.inventory.pk})
    assert serializer.is_valid()
    serializer = JobTemplateSerializer(data={"name": "Test", "job_type": "scan",
                                             "project": None, "inventory": None})
    assert not serializer.is_valid()
    assert "inventory" in serializer.errors
    serializer = JobTemplateSerializer(data={"name": "Test", "job_type": "scan",
                                             "project": None, "inventory": None,
                                             "ask_inventory_on_launch": True})
    assert not serializer.is_valid()
    assert "inventory" in serializer.errors

    # A user shouldn't be able to launch a scan job template which is missing an inventory
    obj_jt = objects.job_template
    obj_jt.inventory = None
    serializer = JobLaunchSerializer(instance=obj_jt,
                                     context={'obj': obj_jt,
                                              "data": {}},
                                     data={})
    assert not serializer.is_valid()
    assert 'inventory' in serializer.errors

@pytest.mark.django_db
def test_scan_jt_surveys(inventory):
    serializer = JobTemplateSerializer(data={"name": "Test", "job_type": "scan",
                                             "project": None, "inventory": inventory.pk,
                                             "survey_enabled": True})
    assert not serializer.is_valid()
    assert "survey_enabled" in serializer.errors

@pytest.mark.django_db
def test_jt_without_project(inventory):
    data = dict(name="Test", job_type="run",
                inventory=inventory.pk, project=None)
    serializer = JobTemplateSerializer(data=data)
    assert not serializer.is_valid()
    assert "project" in serializer.errors
    data["job_type"] = "check"
    serializer = JobTemplateSerializer(data=data)
    assert not serializer.is_valid()
    assert "project" in serializer.errors
    data["job_type"] = "scan"
    serializer = JobTemplateSerializer(data=data)
    assert serializer.is_valid()

@pytest.mark.django_db
def test_disallow_template_delete_on_running_job(job_template_factory, delete, admin_user):
    objects = job_template_factory('jt',
                                   credential='c',
                                   job_type="run",
                                   project='p',
                                   inventory='i',
                                   organization='o')
    objects.job_template.create_unified_job()
    delete_response = delete(reverse('api:job_template_detail', args=[objects.job_template.pk]), user=admin_user)
    assert delete_response.status_code == 409

@pytest.mark.django_db
def test_save_survey_passwords_to_job(job_template_with_survey_passwords):
    """Test that when a new job is created, the survey_passwords field is
    given all of the passwords that exist in the JT survey"""
    job = job_template_with_survey_passwords.create_unified_job()
    assert job.survey_passwords == {'SSN': '$encrypted$', 'secret_key': '$encrypted$'}

@pytest.mark.django_db
def test_save_survey_passwords_on_migration(job_template_with_survey_passwords):
    """Test that when upgrading to 3.0.2, the jobs connected to a JT that has
    a survey with passwords in it, the survey passwords get saved to the
    job survey_passwords field."""
    Job.objects.create(job_template=job_template_with_survey_passwords)
    save_password_keys.migrate_survey_passwords(apps, None)
    job = job_template_with_survey_passwords.jobs.all()[0]
    assert job.survey_passwords == {'SSN': '$encrypted$', 'secret_key': '$encrypted$'}
