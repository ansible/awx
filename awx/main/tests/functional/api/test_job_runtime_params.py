import pytest
import yaml

from awx.api.serializers import JobLaunchSerializer
from awx.main.models.credential import Credential
from awx.main.models.inventory import Inventory
from awx.main.models.jobs import Job, JobTemplate

from django.core.urlresolvers import reverse

@pytest.fixture
def runtime_data():
    cred_obj = Credential.objects.create(name='runtime-cred', kind='ssh', username='test_user2', password='pas4word2')
    return dict(
        limit='test-servers',
        job_type='check',
        inventory=cred_obj.pk,
        job_tags='["provision"]',
        skip_tags='["restart"]',
        extra_vars='{"job_launch_var": 4}'
    )

@pytest.fixture
def job_template_prompts(project, inventory, machine_credential):
    def rf(on_off):
        return JobTemplate.objects.create(
            job_type='run', project=project, inventory=inventory,
            credential=machine_credential, name='deploy-job-template',
            ask_variables_on_launch=on_off,
            ask_tags_on_launch=on_off,
            ask_job_type_on_launch=on_off,
            ask_inventory_on_launch=on_off,
            ask_limit_on_launch=on_off,
        )
    return rf

# Probably remove this test after development is finished
@pytest.mark.django_db
def test_job_launch_prompts_echo(job_template_prompts, get, user):
    job_template = job_template_prompts(True)
    assert job_template.ask_variables_on_launch

    url = reverse('api:job_template_launch', args=[job_template.pk])

    response = get(
        reverse('api:job_template_launch', args=[job_template.pk]), 
        user('admin', True))

    # Just checking that the GET response has what we expect
    assert response.data['ask_variables_on_launch']
    assert response.data['ask_tags_on_launch']
    assert response.data['ask_job_type_on_launch']
    assert response.data['ask_inventory_on_launch']
    assert response.data['ask_limit_on_launch']

@pytest.mark.django_db
def test_job_ignore_unprompted_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(False)

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        runtime_data, user('admin', True))

    job_id = response.data['job']
    job_obj = Job.objects.get(pk=job_id)

    # Check that job data matches job_template data
    assert len(yaml.load(job_obj.extra_vars)) == 0
    assert job_obj.limit == job_template.limit
    assert job_obj.job_type == job_template.job_type
    assert job_obj.inventory.pk == job_template.inventory.pk
    assert job_obj.job_tags == job_template.job_tags

    # Check that response tells us what things were ignored
    assert 'job_launch_var' in response.data['ignored_fields']['extra_vars']
    assert 'job_type' in response.data['ignored_fields']
    assert 'limit' in response.data['ignored_fields']
    assert 'inventory' in response.data['ignored_fields']
    assert 'job_tags' in response.data['ignored_fields']
    assert 'skip_tags' in response.data['ignored_fields']

@pytest.mark.django_db
def test_job_accept_prompted_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        runtime_data, user('admin', True))

    job_id = response.data['job']
    job_obj = Job.objects.get(pk=job_id)

    # Check that job data matches the given runtime variables
    assert 'job_launch_var' in yaml.load(job_obj.extra_vars)
    assert job_obj.limit == runtime_data['limit']
    assert job_obj.job_type == runtime_data['job_type']
    assert job_obj.inventory.pk == runtime_data['inventory']
    assert job_obj.job_tags == runtime_data['job_tags']

@pytest.mark.django_db
def test_job_launch_JT_with_validation(machine_credential, deploy_jobtemplate):
    deploy_jobtemplate.extra_vars = '{"job_template_var": 3}'
    deploy_jobtemplate.save()

    kv = dict(extra_vars={"job_launch_var": 4}, credential=machine_credential.id)
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data=kv,
        context={'obj': deploy_jobtemplate, 'data': kv, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated

    job_obj = deploy_jobtemplate.create_unified_job(**kv)
    result = job_obj.signal_start(**kv)

    final_job_extra_vars = yaml.load(job_obj.extra_vars)
    assert result
    assert 'job_template_var' in final_job_extra_vars
    assert 'job_launch_var' in final_job_extra_vars

@pytest.mark.django_db
def test_job_launch_unprompted_vars_with_survey(job_template_prompts, post, user):
    job_template = job_template_prompts(False)
    job_template.survey_enabled = True
    job_template.survey_spec = {
        "spec": [
            {
                "index": 0,
                "question_name": "survey_var",
                "min": 0,
                "default": "",
                "max": 100,
                "question_description": "A survey question",
                "required": True,
                "variable": "survey_var",
                "choices": "",
                "type": "integer"
            }
        ],
        "description": "",
        "name": ""
    }
    job_template.save()

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        dict(extra_vars={"job_launch_var": 3, "survey_var": 4}), 
        user('admin', True))

    job_id = response.data['job']
    job_obj = Job.objects.get(pk=job_id)

    # Check that the survey variable is accept and the job variable isn't
    job_extra_vars = yaml.load(job_obj.extra_vars)
    assert 'job_launch_var' not in job_extra_vars
    assert 'survey_var' in job_extra_vars

# To add:
#  permissions testing (can't provide inventory you can't run against)
#  credentials/password test if they will be included in response format
