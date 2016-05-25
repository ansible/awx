import pytest
import mock

# AWX
from awx.api.serializers import JobTemplateSerializer
from awx.main.models.jobs import JobTemplate

# Django
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse


@pytest.fixture
def jt_copy_edit(project):
    return JobTemplate.objects.create(
        job_type='run',
        project=project,
        playbook='hello_world.yml',
        ask_inventory_on_launch=True,
        ask_credential_on_launch=True,
        name='copy-edit-job-template'
    )


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
    "If a required resource (inventory here) was deleted, copying not allowed"

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
@pytest.mark.skip(reason="Waiting on issue 1981")
def test_org_admin_foreign_cred_no_copy_edit(jt_copy_edit, org_admin, machine_credential):
    """
    Organization admins SHOULD NOT be able to copy JT without resource access
    but they SHOULD be able to edit that job template
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
    "JT admins wihout access to associated resources SHOULD NOT be able to copy"

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
    assert not response['summary_fields']['can_edit']

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
def test_org_admin_copy_edit_functional(jt_copy_edit, org_admin, get, post):
    get_response = get(reverse('api:job_template_detail', args=[jt_copy_edit.pk]), user=org_admin)

    post_data = get_response.data
    post_data['name'] = '%s @ 12:19:47 pm' % post_data['name']

    assert get_response.status_code == 200
    assert get_response.data['summary_fields']['can_copy']

    with mock.patch(
            'awx.main.models.projects.ProjectOptions.playbooks',
            new_callable=mock.PropertyMock(return_value=['hello_world.yml'])):
        post_response = post(reverse('api:job_template_list', args=[]), user=org_admin, data=post_data)

    print '\n post_response: ' + str(post_response.data)
    assert post_response.status_code == 201
    assert post_response.data['name'] == 'copy-edit-job-template @ 12:19:47 pm'

@pytest.mark.django_db
def test_jt_admin_copy_edit_functional(jt_copy_edit, rando, get, post):

    # Grant random user JT admin access only
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()

    get_response = get(reverse('api:job_template_detail', args=[jt_copy_edit.pk]), user=rando)

    assert get_response.status_code == 200
    assert not get_response.data['summary_fields']['can_copy']

    post_data = get_response.data
    post_data['name'] = '%s @ 12:19:47 pm' % post_data['name']

    with mock.patch(
            'awx.main.models.projects.ProjectOptions.playbooks',
            new_callable=mock.PropertyMock(return_value=['hello_world.yml'])):
        post_response = post(reverse('api:job_template_list', args=[]), user=rando, data=post_data)

    print '\n post_response: ' + str(post_response.data)
    assert post_response.status_code == 403

# Validation function tests
# TODO: replace these JT creations with Wayne's new awesome factories

@pytest.mark.django_db
def test_missing_project_error(inventory, machine_credential):
    obj = JobTemplate.objects.create(
        job_type='run',
        project=None,
        inventory=inventory,
        credential=machine_credential,
        name='missing-project-jt'
    )
    assert 'project' in obj.resources_needed_to_start
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'project' in validation_errors

@pytest.mark.django_db
def test_inventory_credential_contradictions(project):
    obj = JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=None, ask_inventory_on_launch=False,
        credential=None, ask_credential_on_launch=False,
        name='missing-project-jt'
    )
    assert 'inventory' in obj.resources_needed_to_start
    assert 'credential' in obj.resources_needed_to_start
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'inventory' in validation_errors
    assert 'credential' in validation_errors
