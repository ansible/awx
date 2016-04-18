import pytest
import yaml

from awx.api.serializers import JobLaunchSerializer
from awx.main.models.credential import Credential
from awx.main.models.inventory import Inventory
from awx.main.models.jobs import Job, JobTemplate

from django.core.urlresolvers import reverse

from copy import copy

@pytest.fixture
def runtime_data(organization):
    cred_obj = Credential.objects.create(name='runtime-cred', kind='ssh', username='test_user2', password='pas4word2')
    inv_obj = organization.inventories.create(name="runtime-inv")
    return dict(
        extra_vars='{"job_launch_var": 4}',
        limit='test-servers',
        job_type='check',
        job_tags='provision',
        skip_tags='restart',
        inventory=inv_obj.pk,
        credential=cred_obj.pk,
    )

@pytest.fixture
def job_template_prompts(project, inventory, machine_credential):
    def rf(on_off):
        return JobTemplate.objects.create(
            job_type='run',
            project=project,
            inventory=inventory,
            credential=machine_credential,
            name='deploy-job-template',
            ask_variables_on_launch=on_off,
            ask_tags_on_launch=on_off,
            ask_job_type_on_launch=on_off,
            ask_inventory_on_launch=on_off,
            ask_limit_on_launch=on_off,
            ask_credential_on_launch=on_off,
        )
    return rf

@pytest.fixture
def job_template_prompts_null(project):
    return JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=None,
        credential=None,
        name='deploy-job-template',
        ask_variables_on_launch=True,
        ask_tags_on_launch=True,
        ask_job_type_on_launch=True,
        ask_inventory_on_launch=True,
        ask_limit_on_launch=True,
        ask_credential_on_launch=True,
    )

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_ignore_unprompted_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(False)
    job_template_saved = copy(job_template)

    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    runtime_data, user('admin', True))

    assert response.status_code == 201
    job_id = response.data['job']
    job_obj = Job.objects.get(pk=job_id)

    # Check that job data matches job_template data
    assert len(yaml.load(job_obj.extra_vars)) == 0
    assert job_obj.limit == job_template_saved.limit
    assert job_obj.job_type == job_template_saved.job_type
    assert job_obj.inventory.pk == job_template_saved.inventory.pk
    assert job_obj.job_tags == job_template_saved.job_tags
    assert job_obj.credential.pk == job_template_saved.credential.pk

    # Check that response tells us what things were ignored
    assert 'job_launch_var' in response.data['ignored_fields']['extra_vars']
    assert 'job_type' in response.data['ignored_fields']
    assert 'limit' in response.data['ignored_fields']
    assert 'inventory' in response.data['ignored_fields']
    assert 'credential' in response.data['ignored_fields']
    assert 'job_tags' in response.data['ignored_fields']
    assert 'skip_tags' in response.data['ignored_fields']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_accept_prompted_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(True)
    admin_user = user('admin', True)

    job_template.inventory.execute_role.members.add(admin_user)

    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    runtime_data, admin_user)

    assert response.status_code == 201
    job_id = response.data['job']
    job_obj = Job.objects.get(pk=job_id)

    # Check that job data matches the given runtime variables
    assert 'job_launch_var' in yaml.load(job_obj.extra_vars)
    assert job_obj.limit == runtime_data['limit']
    assert job_obj.job_type == runtime_data['job_type']
    assert job_obj.inventory.pk == runtime_data['inventory']
    assert job_obj.credential.pk == runtime_data['credential']
    assert job_obj.job_tags == runtime_data['job_tags']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_accept_prompted_vars_null(runtime_data, job_template_prompts_null, post, user):
    job_template = job_template_prompts_null
    common_user = user('not-admin', False)

    # Give user permission to execute the job template
    job_template.execute_role.members.add(common_user)

    # Give user permission to use inventory and credential at runtime
    credential = Credential.objects.get(pk=runtime_data['credential'])
    credential.use_role.members.add(common_user)
    inventory = Inventory.objects.get(pk=runtime_data['inventory'])
    inventory.use_role.members.add(common_user)

    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    runtime_data, common_user)

    assert response.status_code == 201
    job_id = response.data['job']
    job_obj = Job.objects.get(pk=job_id)

    # Check that job data matches the given runtime variables
    assert 'job_launch_var' in yaml.load(job_obj.extra_vars)
    assert job_obj.limit == runtime_data['limit']
    assert job_obj.job_type == runtime_data['job_type']
    assert job_obj.inventory.pk == runtime_data['inventory']
    assert job_obj.credential.pk == runtime_data['credential']
    assert job_obj.job_tags == runtime_data['job_tags']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_reject_invalid_prompted_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        dict(job_type='foobicate',  # foobicate is not a valid job type
             inventory=87865, credential=48474), user('admin', True))

    assert response.status_code == 400
    assert response.data['job_type'] == [u'"foobicate" is not a valid choice.']
    assert response.data['inventory'] == [u'Invalid pk "87865" - object does not exist.']
    assert response.data['credential'] == [u'Invalid pk "48474" - object does not exist.']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_reject_invalid_prompted_extra_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        dict(extra_vars='{"unbalanced brackets":'), user('admin', True))

    assert response.status_code == 400
    assert response.data['extra_vars'] == ['Must be valid JSON or YAML']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory(deploy_jobtemplate, post, user):
    deploy_jobtemplate.inventory = None
    deploy_jobtemplate.save()

    response = post(reverse('api:job_template_launch',
                    args=[deploy_jobtemplate.pk]), {}, user('admin', True))

    assert response.status_code == 400
    assert response.data['inventory'] == ['Job Template Inventory is missing or undefined']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory_access(deploy_jobtemplate, machine_credential, post, user):
    deploy_jobtemplate.ask_inventory_on_launch = True
    deploy_jobtemplate.credential = machine_credential
    deploy_jobtemplate.save()
    common_user = user('test-user', False)
    deploy_jobtemplate.execute_role.members.add(common_user)
    deploy_jobtemplate.inventory.use_role.members.add(common_user)
    deploy_jobtemplate.project.member_role.members.add(common_user)
    deploy_jobtemplate.credential.use_role.members.add(common_user)

    # Assure that the base job template can be launched to begin with
    response = post(reverse('api:job_template_launch',
                    args=[deploy_jobtemplate.pk]), {}, common_user)

    assert response.status_code == 201

    # Assure that giving an inventory without access to the inventory blocks the launch
    new_inv = deploy_jobtemplate.project.organization.inventories.create(name="user-can-not-use")
    response = post(reverse('api:job_template_launch', args=[deploy_jobtemplate.pk]),
                    dict(inventory=new_inv.pk), common_user)

    assert response.status_code == 403
    assert response.data['detail'] == u'You do not have permission to perform this action.'

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_relaunch_prompted_vars(runtime_data, job_template_prompts, post, user):
    job_template = job_template_prompts(True)
    admin_user = user('admin', True)

    # Launch job, overwriting several JT fields
    first_response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                          runtime_data, admin_user)

    assert first_response.status_code == 201
    original_job = Job.objects.get(pk=first_response.data['job'])

    # Launch a second job as a relaunch of the first
    second_response = post(reverse('api:job_relaunch', args=[original_job.pk]),
                           {}, admin_user)
    relaunched_job = Job.objects.get(pk=second_response.data['job'])

    # Check that job data matches the original runtime variables
    assert first_response.status_code == 201
    assert 'job_launch_var' in yaml.load(relaunched_job.extra_vars)
    assert relaunched_job.limit == runtime_data['limit']
    assert relaunched_job.job_type == runtime_data['job_type']
    assert relaunched_job.inventory.pk == runtime_data['inventory']
    assert relaunched_job.job_tags == runtime_data['job_tags']

@pytest.mark.django_db
def test_job_launch_JT_with_validation(machine_credential, deploy_jobtemplate):
    deploy_jobtemplate.extra_vars = '{"job_template_var": 3}'
    deploy_jobtemplate.ask_credential_on_launch = True
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
    assert job_obj.credential.id == machine_credential.id

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_unprompted_vars_with_survey(mocker, job_template_prompts, post, user):
    with mocker.patch('awx.main.access.BaseAccess.check_license', return_value=False):
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
        assert response.status_code == 201

        job_id = response.data['job']
        job_obj = Job.objects.get(pk=job_id)

        # Check that the survey variable is accepted and the job variable isn't
        job_extra_vars = yaml.load(job_obj.extra_vars)
        assert 'job_launch_var' not in job_extra_vars
        assert 'survey_var' in job_extra_vars
