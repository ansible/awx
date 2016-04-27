import pytest
import yaml

from awx.api.serializers import JobLaunchSerializer
from awx.main.models.credential import Credential
from awx.main.models.inventory import Inventory
from awx.main.models.jobs import Job, JobTemplate

from django.core.urlresolvers import reverse

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
def test_job_ignore_unprompted_vars(runtime_data, job_template_prompts, post, user, mocker):
    job_template = job_template_prompts(False)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                            runtime_data, user('admin', True))
            assert response.status_code == 201

    # Check that job is serialized correctly
    job_id = response.data['job']
    assert job_id == 968

    # If job is created with no arguments, it will inherit JT attributes
    mock_job.signal_start.assert_called_once_with(extra_vars={})

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
def test_job_accept_prompted_vars(runtime_data, job_template_prompts, post, user, mocker):
    job_template = job_template_prompts(True)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                            runtime_data, user('admin', True))

    assert response.status_code == 201
    job_id = response.data['job']
    assert job_id == 968

    mock_job.signal_start.assert_called_once_with(**runtime_data)

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_accept_prompted_vars_null(runtime_data, job_template_prompts_null, post, user, mocker):
    job_template = job_template_prompts_null
    common_user = user('not-admin', False)

    # Give user permission to execute the job template
    job_template.execute_role.members.add(common_user)

    # Give user permission to use inventory and credential at runtime
    credential = Credential.objects.get(pk=runtime_data['credential'])
    credential.use_role.members.add(common_user)
    inventory = Inventory.objects.get(pk=runtime_data['inventory'])
    inventory.use_role.members.add(common_user)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                            runtime_data, common_user)

    assert response.status_code == 201
    job_id = response.data['job']
    assert job_id == 968
    mock_job.signal_start.assert_called_once_with(**runtime_data)

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
def test_job_launch_fails_without_inventory_or_cred_access(
        job_template_prompts, runtime_data, machine_credential, post, user, mocker):
    job_template = job_template_prompts(True)
    common_user = user('test-user', False)
    job_template.execute_role.members.add(common_user)

    # Assure that the base job template can be launched to begin with
    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)
    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch',
                            args=[job_template.pk]), {}, common_user)

    assert response.status_code == 201

    # Assure that giving an inventory without access to the inventory blocks the launch
    new_inv = job_template.project.organization.inventories.create(name="user-can-not-use")
    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(inventory=new_inv.pk), common_user)

    assert response.status_code == 403
    assert response.data['detail'] == u'You do not have permission to perform this action.'

    # Assure that giving a credential without access blocks the launch
    new_cred = Credential.objects.create(name='machine-cred-you-cant-use', kind='ssh', username='test_user', password='pas4word')
    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(credential=new_cred.pk), common_user)

    assert response.status_code == 403
    assert response.data['detail'] == u'You do not have permission to perform this action.'

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_relaunch_copy_vars(runtime_data, job_template_prompts, project, post, mocker):
    job_template = job_template_prompts(True)

    # Create a job with the given data that will be relaunched
    job_create_kwargs = runtime_data
    inv_obj = Inventory.objects.get(pk=job_create_kwargs.pop('inventory'))
    cred_obj = Credential.objects.get(pk=job_create_kwargs.pop('credential'))
    original_job = Job.objects.create(inventory=inv_obj, credential=cred_obj, job_template=job_template, **job_create_kwargs)
    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate._get_unified_job_field_names', return_value=runtime_data.keys()):
        second_job = original_job.copy()

    # Check that job data matches the original variables
    assert 'job_launch_var' in yaml.load(second_job.extra_vars)
    assert original_job.limit == second_job.limit
    assert original_job.job_type == second_job.job_type
    assert original_job.inventory.pk == second_job.inventory.pk
    assert original_job.job_tags == second_job.job_tags

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_relaunch_resource_access(runtime_data, project, user):
    the_cred = Credential.objects.get(pk=runtime_data['credential'])
    the_inv = Inventory.objects.get(pk=runtime_data['inventory'])

    original_job = Job.objects.create(
        name='existing-job', credential=the_cred, inventory=the_inv
    )
    inventory_user = user('user1', False)
    credential_user = user('user2', False)
    both_user = user('user3', False)

    # Confirm that a user with inventory & credential access can launch
    the_cred.use_role.members.add(both_user)
    the_inv.use_role.members.add(both_user)
    assert both_user.can_access(Job, 'start', original_job)

    # Confirm that a user with credential access alone can not launch
    the_cred.use_role.members.add(credential_user)
    assert not credential_user.can_access(Job, 'start', original_job)

    # Confirm that a user with inventory access alone can not launch
    the_inv.use_role.members.add(inventory_user)
    assert not inventory_user.can_access(Job, 'start', original_job)

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

    final_job_extra_vars = yaml.load(job_obj.extra_vars)
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

        mock_job = mocker.MagicMock(spec=Job, id=968, extra_vars={"job_launch_var": 3, "survey_var": 4})
        with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
                response = post(
                    reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(extra_vars={"job_launch_var": 3, "survey_var": 4}),
                    user('admin', True))
                assert response.status_code == 201

        job_id = response.data['job']
        assert job_id == 968

        # Check that the survey variable is accepted and the job variable isn't
        mock_job.signal_start.assert_called_once_with(extra_vars={"survey_var": 4})
