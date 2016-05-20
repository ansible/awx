import pytest
import mock

# AWX
from awx.api.serializers import JobTemplateSerializer
from awx.main.access import JobTemplateAccess
from awx.main.models.jobs import JobTemplate

# Django
from django.test.client import RequestFactory
from django.forms.models import model_to_dict
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

    # Access
    jt_access = JobTemplateAccess(admin_user)
    jt_dict = model_to_dict(jt_copy_edit)
    assert jt_access.can_add(jt_dict)
    assert jt_access.can_change(jt_copy_edit, jt_dict)

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

    # Access
    jt_access = JobTemplateAccess(org_admin)
    jt_dict = model_to_dict(jt_copy_edit)
    assert jt_access.can_add(jt_dict)
    assert jt_access.can_change(jt_copy_edit, jt_dict)

@pytest.mark.django_db
@pytest.mark.skip(reason="Waiting on issue 1981")
def test_org_admin_foreign_cred_no_copy_edit(jt_copy_edit, org_admin, machine_credential):
    "Organization admins SHOULD NOT be able to copy JT without resource access"

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

    # Access
    jt_access = JobTemplateAccess(org_admin)
    jt_dict = model_to_dict(jt_copy_edit)
    assert not jt_access.can_add(jt_dict)
    assert jt_access.can_change(jt_copy_edit, jt_dict)

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

    # Access
    jt_access = JobTemplateAccess(rando)
    jt_dict = model_to_dict(jt_copy_edit)
    print ' jt_dict: ' + str(jt_dict)
    assert not jt_access.can_add(jt_dict)
    assert not jt_access.can_change(jt_copy_edit, jt_dict)

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

    # Access
    jt_access = JobTemplateAccess(rando)
    jt_dict = model_to_dict(jt_copy_edit)
    assert jt_access.can_add(jt_dict)
    assert jt_access.can_change(jt_copy_edit, jt_dict)

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
