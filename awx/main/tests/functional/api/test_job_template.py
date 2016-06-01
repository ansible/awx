import pytest
import mock

# AWX
from awx.api.serializers import JobTemplateSerializer
from awx.main.models.jobs import JobTemplate
from awx.main.models.projects import ProjectOptions

# Django
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse


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
    SHOULD NOT be able to edit that job template
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
    assert not response['summary_fields']['can_edit']

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
