import pytest
import yaml

from awx.api.serializers import JobLaunchSerializer
from awx.main.models.credential import Credential
from awx.main.models.inventory import Inventory
from awx.main.models.jobs import Job, JobTemplate
from awx.main.tests.factories.utils import generate_survey_spec

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
def job_with_links(machine_credential, inventory):
    return Job.objects.create(name='existing-job', credential=machine_credential, inventory=inventory)

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

@pytest.fixture
def bad_scan_JT(job_template_prompts):
    job_template = job_template_prompts(True)
    job_template.job_type = 'scan'
    job_template.save()
    return job_template

# End of setup, tests start here
@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_ignore_unprompted_vars(runtime_data, job_template_prompts, post, admin_user, mocker):
    job_template = job_template_prompts(False)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                            runtime_data, admin_user, expect=201)

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
def test_job_accept_prompted_vars(runtime_data, job_template_prompts, post, admin_user, mocker):
    job_template = job_template_prompts(True)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                            runtime_data, admin_user, expect=201)

    job_id = response.data['job']
    assert job_id == 968

    mock_job.signal_start.assert_called_once_with(**runtime_data)

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_accept_prompted_vars_null(runtime_data, job_template_prompts_null, post, rando, mocker):
    job_template = job_template_prompts_null

    # Give user permission to execute the job template
    job_template.execute_role.members.add(rando)

    # Give user permission to use inventory and credential at runtime
    credential = Credential.objects.get(pk=runtime_data['credential'])
    credential.use_role.members.add(rando)
    inventory = Inventory.objects.get(pk=runtime_data['inventory'])
    inventory.use_role.members.add(rando)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                            runtime_data, rando, expect=201)

    job_id = response.data['job']
    assert job_id == 968
    mock_job.signal_start.assert_called_once_with(**runtime_data)

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_reject_invalid_prompted_vars(runtime_data, job_template_prompts, post, admin_user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        dict(job_type='foobicate',  # foobicate is not a valid job type
             inventory=87865, credential=48474), admin_user, expect=400)

    assert response.data['job_type'] == [u'"foobicate" is not a valid choice.']
    assert response.data['inventory'] == [u'Invalid pk "87865" - object does not exist.']
    assert response.data['credential'] == [u'Invalid pk "48474" - object does not exist.']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_reject_invalid_prompted_extra_vars(runtime_data, job_template_prompts, post, admin_user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', args=[job_template.pk]),
        dict(extra_vars='{"unbalanced brackets":'), admin_user, expect=400)

    assert response.data['extra_vars'] == ['Must be a valid JSON or YAML dictionary.']

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory(deploy_jobtemplate, post, admin_user):
    deploy_jobtemplate.inventory = None
    deploy_jobtemplate.save()

    response = post(reverse('api:job_template_launch',
                    args=[deploy_jobtemplate.pk]), {}, admin_user, expect=400)

    assert response.data['inventory'] == ["Job Template 'inventory' is missing or undefined."]

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory_access(job_template_prompts, runtime_data, post, rando):
    job_template = job_template_prompts(True)
    job_template.execute_role.members.add(rando)

    # Assure that giving an inventory without access to the inventory blocks the launch
    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(inventory=runtime_data['inventory']), rando, expect=403)

    assert response.data['detail'] == u'You do not have permission to perform this action.'

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_credential_access(job_template_prompts, runtime_data, post, rando):
    job_template = job_template_prompts(True)
    job_template.execute_role.members.add(rando)

    # Assure that giving a credential without access blocks the launch
    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(credential=runtime_data['credential']), rando, expect=403)

    assert response.data['detail'] == u'You do not have permission to perform this action.'

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_block_scan_job_type_change(job_template_prompts, post, admin_user):
    job_template = job_template_prompts(True)

    # Assure that changing the type of a scan job blocks the launch
    response = post(reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(job_type='scan'), admin_user, expect=400)

    assert 'job_type' in response.data

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_block_scan_job_inv_change(mocker, bad_scan_JT, runtime_data, post, admin_user):
    # Assure that giving a new inventory for a scan job blocks the launch
    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        response = post(reverse('api:job_template_launch', args=[bad_scan_JT.pk]),
                        dict(inventory=runtime_data['inventory']), admin_user,
                        expect=400)

    assert 'inventory' in response.data

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_relaunch_copy_vars(job_with_links, machine_credential, inventory,
                                deploy_jobtemplate, post, mocker):
    job_with_links.job_template = deploy_jobtemplate
    job_with_links.limit = "my_server"
    with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate._get_unified_job_field_names',
                      return_value=['inventory', 'credential', 'limit']):
        second_job = job_with_links.copy()

    # Check that job data matches the original variables
    assert second_job.credential == job_with_links.credential
    assert second_job.inventory == job_with_links.inventory
    assert second_job.limit == 'my_server'

@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_relaunch_resource_access(job_with_links, user):
    inventory_user = user('user1', False)
    credential_user = user('user2', False)
    both_user = user('user3', False)

    # Confirm that a user with inventory & credential access can launch
    job_with_links.credential.use_role.members.add(both_user)
    job_with_links.inventory.use_role.members.add(both_user)
    assert both_user.can_access(Job, 'start', job_with_links)

    # Confirm that a user with credential access alone can not launch
    job_with_links.credential.use_role.members.add(credential_user)
    assert not credential_user.can_access(Job, 'start', job_with_links)

    # Confirm that a user with inventory access alone can not launch
    job_with_links.inventory.use_role.members.add(inventory_user)
    assert not inventory_user.can_access(Job, 'start', job_with_links)

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
def test_job_launch_unprompted_vars_with_survey(mocker, job_template_prompts, post, admin_user):
    job_template = job_template_prompts(False)
    job_template.survey_enabled = True
    job_template.survey_spec = generate_survey_spec('survey_var')
    job_template.save()

    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        mock_job = mocker.MagicMock(spec=Job, id=968, extra_vars={"job_launch_var": 3, "survey_var": 4})
        with mocker.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation', return_value={}):
                response = post(
                    reverse('api:job_template_launch', args=[job_template.pk]),
                    dict(extra_vars={"job_launch_var": 3, "survey_var": 4}),
                    admin_user, expect=201)

    job_id = response.data['job']
    assert job_id == 968

    # Check that the survey variable is accepted and the job variable isn't
    mock_job.signal_start.assert_called_once_with(extra_vars={"survey_var": 4})
