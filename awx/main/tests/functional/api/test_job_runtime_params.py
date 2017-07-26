import mock
import pytest
import yaml

from awx.api.serializers import JobLaunchSerializer
from awx.main.models.credential import Credential
from awx.main.models.inventory import Inventory, Host
from awx.main.models.jobs import Job, JobTemplate

from awx.api.versioning import reverse


@pytest.fixture
def runtime_data(organization, credentialtype_ssh):
    cred_obj = Credential.objects.create(
        name='runtime-cred',
        credential_type=credentialtype_ssh,
        inputs={
            'username': 'test_user2',
            'password': 'pas4word2'
        }
    )
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
            ask_skip_tags_on_launch=on_off,
            ask_job_type_on_launch=on_off,
            ask_inventory_on_launch=on_off,
            ask_limit_on_launch=on_off,
            ask_credential_on_launch=on_off,
            ask_verbosity_on_launch=on_off,
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
        ask_skip_tags_on_launch=True,
        ask_job_type_on_launch=True,
        ask_inventory_on_launch=True,
        ask_limit_on_launch=True,
        ask_credential_on_launch=True,
        ask_verbosity_on_launch=True,
    )


# End of setup, tests start here
@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_ignore_unprompted_vars(runtime_data, job_template_prompts, post, admin_user, mocker):
    job_template = job_template_prompts(False)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
                            runtime_data, admin_user, expect=201)
            assert JobTemplate.create_unified_job.called
            assert JobTemplate.create_unified_job.call_args == ({'extra_vars':{}},)

    # Check that job is serialized correctly
    job_id = response.data['job']
    assert job_id == 968

    # If job is created with no arguments, it will inherit JT attributes
    mock_job.signal_start.assert_called_once()

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

    with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
                            runtime_data, admin_user, expect=201)
            assert JobTemplate.create_unified_job.called
            assert JobTemplate.create_unified_job.call_args == (runtime_data,)

    job_id = response.data['job']
    assert job_id == 968

    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_accept_null_tags(job_template_prompts, post, admin_user, mocker):
    job_template = job_template_prompts(True)

    mock_job = mocker.MagicMock(spec=Job, id=968)

    with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                 {'job_tags': '', 'skip_tags': ''}, admin_user, expect=201)
            assert JobTemplate.create_unified_job.called
            assert JobTemplate.create_unified_job.call_args == ({'job_tags':'', 'skip_tags':''},)

    mock_job.signal_start.assert_called_once()


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

    with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                            runtime_data, rando, expect=201)
            assert JobTemplate.create_unified_job.called
            assert JobTemplate.create_unified_job.call_args == (runtime_data,)

    job_id = response.data['job']
    assert job_id == 968
    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_reject_invalid_prompted_vars(runtime_data, job_template_prompts, post, admin_user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
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
        reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
        dict(extra_vars='{"unbalanced brackets":'), admin_user, expect=400)

    assert 'extra_vars' in response.data
    assert 'valid JSON or YAML' in str(response.data['extra_vars'][0])


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory(deploy_jobtemplate, post, admin_user):
    deploy_jobtemplate.inventory = None
    deploy_jobtemplate.save()

    response = post(reverse('api:job_template_launch',
                    kwargs={'pk': deploy_jobtemplate.pk}), {}, admin_user, expect=400)

    assert response.data['inventory'] == ["Job Template 'inventory' is missing or undefined."]


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory_access(job_template_prompts, runtime_data, post, rando):
    job_template = job_template_prompts(True)
    job_template.execute_role.members.add(rando)

    # Assure that giving an inventory without access to the inventory blocks the launch
    response = post(reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
                    dict(inventory=runtime_data['inventory']), rando, expect=403)

    assert response.data['detail'] == u'You do not have permission to perform this action.'


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_credential_access(job_template_prompts, runtime_data, post, rando):
    job_template = job_template_prompts(True)
    job_template.execute_role.members.add(rando)

    # Assure that giving a credential without access blocks the launch
    response = post(reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
                    dict(credential=runtime_data['credential']), rando, expect=403)

    assert response.data['detail'] == u'You do not have permission to perform this action.'


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_block_scan_job_type_change(job_template_prompts, post, admin_user):
    job_template = job_template_prompts(True)

    # Assure that changing the type of a scan job blocks the launch
    response = post(reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
                    dict(job_type='scan'), admin_user, expect=400)

    assert 'job_type' in response.data


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
@pytest.mark.parametrize('pks, error_msg', [
    ([1], 'must be network or cloud'),
    ([999], 'object does not exist'),
])
def test_job_launch_JT_with_invalid_extra_credentials(machine_credential, deploy_jobtemplate, pks, error_msg):
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.save()

    kv = dict(extra_credentials=pks, credential=machine_credential.id)
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data=kv,
        context={'obj': deploy_jobtemplate, 'data': kv, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated is False


@pytest.mark.django_db
def test_job_launch_JT_enforces_unique_extra_credential_kinds(machine_credential, credentialtype_aws, deploy_jobtemplate):
    """
    JT launching should require that extra_credentials have distinct CredentialTypes
    """
    pks = []
    for i in range(2):
        aws = Credential.objects.create(
            name='cred-%d' % i,
            credential_type=credentialtype_aws,
            inputs={
                'username': 'test_user',
                'password': 'pas4word'
            }
        )
        aws.save()
        pks.append(aws.pk)

    kv = dict(extra_credentials=pks, credential=machine_credential.id)
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data=kv,
        context={'obj': deploy_jobtemplate, 'data': kv, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated is False


@pytest.mark.django_db
@pytest.mark.parametrize('ask_credential_on_launch', [True, False])
def test_job_launch_with_no_credentials(deploy_jobtemplate, ask_credential_on_launch):
    deploy_jobtemplate.credential = None
    deploy_jobtemplate.vault_credential = None
    deploy_jobtemplate.ask_credential_on_launch = ask_credential_on_launch
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data={},
        context={'obj': deploy_jobtemplate, 'data': {}, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated is False
    assert serializer.errors['credential'] == ["Job Template 'credential' is missing or undefined."]


@pytest.mark.django_db
def test_job_launch_with_only_vault_credential(vault_credential, deploy_jobtemplate):
    deploy_jobtemplate.credential = None
    deploy_jobtemplate.vault_credential = vault_credential
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data={},
        context={'obj': deploy_jobtemplate, 'data': {}, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated

    prompted_fields, ignored_fields = deploy_jobtemplate._accept_or_ignore_job_kwargs(**{})
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)

    assert job_obj.vault_credential.pk == vault_credential.pk


@pytest.mark.django_db
def test_job_launch_with_vault_credential_ask_for_machine(vault_credential, deploy_jobtemplate):
    deploy_jobtemplate.credential = None
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.vault_credential = vault_credential
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data={},
        context={'obj': deploy_jobtemplate, 'data': {}, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated

    prompted_fields, ignored_fields = deploy_jobtemplate._accept_or_ignore_job_kwargs(**{})
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)
    assert job_obj.credential is None
    assert job_obj.vault_credential.pk == vault_credential.pk


@pytest.mark.django_db
def test_job_launch_with_vault_credential_and_prompted_machine_cred(machine_credential, vault_credential,
                                                                    deploy_jobtemplate):
    deploy_jobtemplate.credential = None
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.vault_credential = vault_credential
    kv = dict(credential=machine_credential.id)
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data=kv,
        context={'obj': deploy_jobtemplate, 'data': kv, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated

    prompted_fields, ignored_fields = deploy_jobtemplate._accept_or_ignore_job_kwargs(**kv)
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)
    assert job_obj.credential.pk == machine_credential.pk
    assert job_obj.vault_credential.pk == vault_credential.pk


@pytest.mark.django_db
def test_job_launch_JT_with_default_vault_credential(machine_credential, vault_credential, deploy_jobtemplate):
    deploy_jobtemplate.credential = machine_credential
    deploy_jobtemplate.vault_credential = vault_credential
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data={},
        context={'obj': deploy_jobtemplate, 'data': {}, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated

    prompted_fields, ignored_fields = deploy_jobtemplate._accept_or_ignore_job_kwargs(**{})
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)

    assert job_obj.vault_credential.pk == vault_credential.pk


@pytest.mark.django_db
def test_job_launch_fails_with_missing_vault_password(machine_credential, vault_credential,
                                                      deploy_jobtemplate, post, rando):
    vault_credential.vault_password = 'ASK'
    vault_credential.save()
    deploy_jobtemplate.credential = machine_credential
    deploy_jobtemplate.vault_credential = vault_credential
    deploy_jobtemplate.execute_role.members.add(rando)
    deploy_jobtemplate.save()

    response = post(
        reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
        rando,
        expect=400
    )
    assert response.data['passwords_needed_to_start'] == ['vault_password']


@pytest.mark.django_db
def test_job_launch_fails_with_missing_ssh_password(machine_credential, deploy_jobtemplate, post,
                                                    rando):
    machine_credential.password = 'ASK'
    machine_credential.save()
    deploy_jobtemplate.credential = machine_credential
    deploy_jobtemplate.execute_role.members.add(rando)
    deploy_jobtemplate.save()

    response = post(
        reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
        rando,
        expect=400
    )
    assert response.data['passwords_needed_to_start'] == ['ssh_password']


@pytest.mark.django_db
def test_job_launch_fails_with_missing_vault_and_ssh_password(machine_credential, vault_credential,
                                                              deploy_jobtemplate, post, rando):
    vault_credential.vault_password = 'ASK'
    vault_credential.save()
    machine_credential.password = 'ASK'
    machine_credential.save()
    deploy_jobtemplate.credential = machine_credential
    deploy_jobtemplate.vault_credential = vault_credential
    deploy_jobtemplate.execute_role.members.add(rando)
    deploy_jobtemplate.save()

    response = post(
        reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
        rando,
        expect=400
    )
    assert sorted(response.data['passwords_needed_to_start']) == ['ssh_password', 'vault_password']


@pytest.mark.django_db
def test_job_launch_pass_with_prompted_vault_password(machine_credential, vault_credential,
                                                      deploy_jobtemplate, post, rando):
    vault_credential.vault_password = 'ASK'
    vault_credential.save()
    deploy_jobtemplate.credential = machine_credential
    deploy_jobtemplate.vault_credential = vault_credential
    deploy_jobtemplate.execute_role.members.add(rando)
    deploy_jobtemplate.save()

    with mock.patch.object(Job, 'signal_start') as signal_start:
        post(
            reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
            {'vault_password': 'vault-me'},
            rando,
            expect=201
        )
        signal_start.assert_called_with(vault_password='vault-me')


@pytest.mark.django_db
def test_job_launch_JT_with_extra_credentials(machine_credential, credential, net_credential, deploy_jobtemplate):
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.save()

    kv = dict(extra_credentials=[credential.pk, net_credential.pk], credential=machine_credential.id)
    serializer = JobLaunchSerializer(
        instance=deploy_jobtemplate, data=kv,
        context={'obj': deploy_jobtemplate, 'data': kv, 'passwords': {}})
    validated = serializer.is_valid()
    assert validated

    prompted_fields, ignored_fields = deploy_jobtemplate._accept_or_ignore_job_kwargs(**kv)
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)

    extra_creds = job_obj.extra_credentials.all()
    assert len(extra_creds) == 2
    assert credential in extra_creds
    assert net_credential in extra_creds


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_unprompted_vars_with_survey(mocker, survey_spec_factory, job_template_prompts, post, admin_user):
    job_template = job_template_prompts(False)
    job_template.survey_enabled = True
    job_template.survey_spec = survey_spec_factory('survey_var')
    job_template.save()

    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        mock_job = mocker.MagicMock(spec=Job, id=968, extra_vars={"job_launch_var": 3, "survey_var": 4})
        with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation', return_value={}):
                response = post(
                    reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
                    dict(extra_vars={"job_launch_var": 3, "survey_var": 4}),
                    admin_user, expect=201)
                assert JobTemplate.create_unified_job.called
                assert JobTemplate.create_unified_job.call_args == ({'extra_vars':{'survey_var': 4}},)


    job_id = response.data['job']
    assert job_id == 968

    # Check that the survey variable is accepted and the job variable isn't
    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_callback_accept_prompted_extra_var(mocker, survey_spec_factory, job_template_prompts, post, admin_user, host):
    job_template = job_template_prompts(True)
    job_template.host_config_key = "foo"
    job_template.survey_enabled = True
    job_template.survey_spec = survey_spec_factory('survey_var')
    job_template.save()

    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        mock_job = mocker.MagicMock(spec=Job, id=968, extra_vars={"job_launch_var": 3, "survey_var": 4})
        with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation', return_value={}):
                with mocker.patch('awx.api.views.JobTemplateCallback.find_matching_hosts', return_value=[host]):
                    post(
                        reverse('api:job_template_callback', kwargs={'pk': job_template.pk}),
                        dict(extra_vars={"job_launch_var": 3, "survey_var": 4}, host_config_key="foo"),
                        admin_user, expect=201, format='json')
                    assert JobTemplate.create_unified_job.called
                    assert JobTemplate.create_unified_job.call_args == ({'extra_vars': {'survey_var': 4,
                                                                                        'job_launch_var': 3},
                                                                         'launch_type': 'callback',
                                                                         'limit': 'single-host'},)

    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_callback_ignore_unprompted_extra_var(mocker, survey_spec_factory, job_template_prompts, post, admin_user, host):
    job_template = job_template_prompts(False)
    job_template.host_config_key = "foo"
    job_template.save()

    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        mock_job = mocker.MagicMock(spec=Job, id=968, extra_vars={"job_launch_var": 3, "survey_var": 4})
        with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation', return_value={}):
                with mocker.patch('awx.api.views.JobTemplateCallback.find_matching_hosts', return_value=[host]):
                    post(
                        reverse('api:job_template_callback', kwargs={'pk':job_template.pk}),
                        dict(extra_vars={"job_launch_var": 3, "survey_var": 4}, host_config_key="foo"),
                        admin_user, expect=201, format='json')
                    assert JobTemplate.create_unified_job.called
                    assert JobTemplate.create_unified_job.call_args == ({'launch_type': 'callback',
                                                                         'limit': 'single-host'},)

    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_callback_find_matching_hosts(mocker, get, job_template_prompts, admin_user):
    job_template = job_template_prompts(False)
    job_template.host_config_key = "foo"
    job_template.save()
    host_with_alias = Host(name='localhost', inventory=job_template.inventory)
    host_with_alias.save()
    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        r = get(reverse('api:job_template_callback', kwargs={'pk': job_template.pk}),
                user=admin_user, expect=200)
        assert tuple(r.data['matching_hosts']) == ('localhost',)


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_callback_extra_var_takes_priority_over_host_name(mocker, get, job_template_prompts, admin_user):
    job_template = job_template_prompts(False)
    job_template.host_config_key = "foo"
    job_template.save()
    host_with_alias = Host(name='localhost', variables={'ansible_host': 'foobar'}, inventory=job_template.inventory)
    host_with_alias.save()
    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        r = get(reverse('api:job_template_callback', kwargs={'pk': job_template.pk}),
                user=admin_user, expect=200)
        assert not r.data['matching_hosts']
