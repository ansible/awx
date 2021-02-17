from unittest import mock
import pytest
import yaml
import json

from awx.api.serializers import JobLaunchSerializer
from awx.main.models.credential import Credential
from awx.main.models.inventory import Inventory, Host
from awx.main.models.jobs import Job, JobTemplate, UnifiedJobTemplate

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
        credentials=[cred_obj.pk],
        diff_mode=True,
        verbosity=2
    )


@pytest.fixture
def job_with_links(machine_credential, inventory):
    return Job.objects.create(name='existing-job', credential=machine_credential, inventory=inventory)


@pytest.fixture
def job_template_prompts(project, inventory, machine_credential):
    def rf(on_off):
        jt = JobTemplate.objects.create(
            job_type='run',
            project=project,
            inventory=inventory,
            name='deploy-job-template',
            # JT values must differ from prompted vals in order to register
            limit='webservers',
            job_tags = 'foobar',
            skip_tags = 'barfoo',
            ask_variables_on_launch=on_off,
            ask_tags_on_launch=on_off,
            ask_skip_tags_on_launch=on_off,
            ask_job_type_on_launch=on_off,
            ask_inventory_on_launch=on_off,
            ask_limit_on_launch=on_off,
            ask_credential_on_launch=on_off,
            ask_diff_mode_on_launch=on_off,
            ask_verbosity_on_launch=on_off,
        )
        jt.credentials.add(machine_credential)
        return jt
    return rf


@pytest.fixture
def job_template_prompts_null(project):
    return JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=None,
        name='deploy-job-template',
        ask_variables_on_launch=True,
        ask_tags_on_launch=True,
        ask_skip_tags_on_launch=True,
        ask_job_type_on_launch=True,
        ask_inventory_on_launch=True,
        ask_limit_on_launch=True,
        ask_credential_on_launch=True,
        ask_diff_mode_on_launch=True,
        ask_verbosity_on_launch=True,
    )


def data_to_internal(data):
    '''
    returns internal representation, model objects, dictionaries, etc
    as opposed to integer primary keys and JSON strings
    '''
    internal = data.copy()
    if 'extra_vars' in data:
        internal['extra_vars'] = json.loads(data['extra_vars'])
    if 'credentials' in data:
        internal['credentials'] = set(Credential.objects.get(pk=_id) for _id in data['credentials'])
    if 'inventory' in data:
        internal['inventory'] = Inventory.objects.get(pk=data['inventory'])
    return internal


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
            assert JobTemplate.create_unified_job.call_args == ()

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
    assert 'credentials' in response.data['ignored_fields']
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
            called_with = data_to_internal(runtime_data)
            JobTemplate.create_unified_job.assert_called_with(**called_with)

    job_id = response.data['job']
    assert job_id == 968

    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_accept_empty_tags(job_template_prompts, post, admin_user, mocker):
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
    credential = Credential.objects.get(pk=runtime_data['credentials'][0])
    credential.use_role.members.add(rando)
    inventory = Inventory.objects.get(pk=runtime_data['inventory'])
    inventory.use_role.members.add(rando)

    mock_job = mocker.MagicMock(spec=Job, id=968, **runtime_data)

    with mocker.patch.object(JobTemplate, 'create_unified_job', return_value=mock_job):
        with mocker.patch('awx.api.serializers.JobSerializer.to_representation'):
            response = post(reverse('api:job_template_launch', kwargs={'pk': job_template.pk}),
                            runtime_data, rando, expect=201)
            assert JobTemplate.create_unified_job.called
            expected_call = data_to_internal(runtime_data)
            assert JobTemplate.create_unified_job.call_args == (expected_call,)

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
             inventory=87865, credentials=[48474]), admin_user, expect=400)

    assert response.data['job_type'] == [u'"foobicate" is not a valid choice.']
    assert response.data['inventory'] == [u'Invalid pk "87865" - object does not exist.']
    assert response.data['credentials'] == [u'Invalid pk "48474" - object does not exist.']


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_reject_invalid_prompted_extra_vars(runtime_data, job_template_prompts, post, admin_user):
    job_template = job_template_prompts(True)

    response = post(
        reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
        dict(extra_vars='{"unbalanced brackets":'), admin_user, expect=400)

    assert 'extra_vars' in response.data
    assert 'Cannot parse as' in str(response.data['extra_vars'][0])


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_job_launch_fails_without_inventory(deploy_jobtemplate, post, admin_user):
    deploy_jobtemplate.inventory = None
    deploy_jobtemplate.save()

    response = post(reverse('api:job_template_launch',
                    kwargs={'pk': deploy_jobtemplate.pk}), {}, admin_user, expect=400)

    assert 'inventory' in response.data['resources_needed_to_start'][0]


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
    post(reverse('api:job_template_launch', kwargs={'pk':job_template.pk}),
         dict(credentials=runtime_data['credentials']), rando, expect=403)


@pytest.mark.django_db
def test_job_launch_JT_with_validation(machine_credential, credential, deploy_jobtemplate):
    deploy_jobtemplate.extra_vars = '{"job_template_var": 3}'
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.ask_variables_on_launch = True
    deploy_jobtemplate.save()

    kv = dict(extra_vars={"job_launch_var": 4}, credentials=[machine_credential.pk, credential.pk])
    serializer = JobLaunchSerializer(data=kv, context={'template': deploy_jobtemplate})
    validated = serializer.is_valid()
    assert validated, serializer.errors

    kv['credentials'] = [machine_credential]  # conversion to internal value
    job_obj = deploy_jobtemplate.create_unified_job(**kv)

    final_job_extra_vars = yaml.safe_load(job_obj.extra_vars)
    assert 'job_launch_var' in final_job_extra_vars
    assert 'job_template_var' in final_job_extra_vars
    assert set([cred.pk for cred in job_obj.credentials.all()]) == set([machine_credential.id, credential.id])


@pytest.mark.django_db
def test_job_launch_with_default_creds(machine_credential, vault_credential, deploy_jobtemplate):
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.credentials.add(machine_credential)
    deploy_jobtemplate.credentials.add(vault_credential)
    kv = dict()
    serializer = JobLaunchSerializer(data=kv, context={'template': deploy_jobtemplate})
    validated = serializer.is_valid()
    assert validated

    prompted_fields, ignored_fields, errors = deploy_jobtemplate._accept_or_ignore_job_kwargs(**kv)
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)
    assert job_obj.machine_credential.pk == machine_credential.pk
    assert job_obj.vault_credentials[0].pk == vault_credential.pk


@pytest.mark.django_db
def test_job_launch_JT_enforces_unique_credentials_kinds(machine_credential, credentialtype_aws, deploy_jobtemplate):
    """
    JT launching should require that credentials have distinct CredentialTypes
    """
    creds = []
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
        creds.append(aws)

    kv = dict(credentials=creds, credential=machine_credential.id)
    serializer = JobLaunchSerializer(data=kv, context={'template': deploy_jobtemplate})
    validated = serializer.is_valid()
    assert not validated


@pytest.mark.django_db
def test_job_launch_with_empty_creds(machine_credential, vault_credential, deploy_jobtemplate, credential):
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.credentials.add(machine_credential)
    deploy_jobtemplate.credentials.add(vault_credential)
    # `credentials` list is strictly those already present on deploy_jobtemplate
    kv = dict(credentials=[credential.pk, machine_credential.pk, vault_credential.pk])
    serializer = JobLaunchSerializer(data=kv, context={'template': deploy_jobtemplate})
    validated = serializer.is_valid()
    assert validated, serializer.errors

    prompted_fields, ignored_fields, errors = deploy_jobtemplate._accept_or_ignore_job_kwargs(**serializer.validated_data)
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)
    assert job_obj.machine_credential.pk == deploy_jobtemplate.machine_credential.pk
    assert job_obj.vault_credentials[0].pk == deploy_jobtemplate.vault_credentials[0].pk


@pytest.mark.django_db
def test_job_launch_fails_with_missing_vault_password(machine_credential, vault_credential,
                                                      deploy_jobtemplate, post, rando):
    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    deploy_jobtemplate.credentials.add(vault_credential)
    deploy_jobtemplate.execute_role.members.add(rando)
    deploy_jobtemplate.save()

    response = post(
        reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
        rando,
        expect=400
    )
    assert response.data['passwords_needed_to_start'] == ['vault_password']


@pytest.mark.django_db
def test_job_launch_with_added_cred_and_vault_password(credential, machine_credential, vault_credential,
                                                       deploy_jobtemplate, post, admin):
    # see: https://github.com/ansible/awx/issues/8202
    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    payload = {
        'credentials': [vault_credential.id, machine_credential.id],
        'credential_passwords': {'vault_password': 'vault-me'},
    }

    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.credentials.remove(credential)
    deploy_jobtemplate.credentials.add(vault_credential)
    deploy_jobtemplate.save()

    with mock.patch.object(Job, 'signal_start') as signal_start:
        post(
            reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
            payload,
            admin,
            expect=201,
        )
        signal_start.assert_called_with(**{
            'vault_password': 'vault-me'
        })


@pytest.mark.django_db
def test_job_launch_with_multiple_launch_time_passwords(credential, machine_credential, vault_credential,
                                                        deploy_jobtemplate, post, admin):
    # see: https://github.com/ansible/awx/issues/8202
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.credentials.remove(credential)
    deploy_jobtemplate.credentials.add(machine_credential)
    deploy_jobtemplate.credentials.add(vault_credential)
    deploy_jobtemplate.save()

    second_machine_credential = Credential(
        name='SSH #2',
        credential_type=machine_credential.credential_type,
        inputs={'password': 'ASK'}
    )
    second_machine_credential.save()

    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    payload = {
        'credentials': [vault_credential.id, second_machine_credential.id],
        'credential_passwords': {'ssh_password': 'ssh-me', 'vault_password': 'vault-me'},
    }

    with mock.patch.object(Job, 'signal_start') as signal_start:
        post(
            reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk}),
            payload,
            admin,
            expect=201,
        )
        signal_start.assert_called_with(**{
            'ssh_password': 'ssh-me',
            'vault_password': 'vault-me',
        })


@pytest.mark.django_db
@pytest.mark.parametrize('launch_kwargs', [
    {'vault_password.abc': 'vault-me-1', 'vault_password.xyz': 'vault-me-2'},
    {'credential_passwords': {'vault_password.abc': 'vault-me-1', 'vault_password.xyz': 'vault-me-2'}}
])
def test_job_launch_fails_with_missing_multivault_password(machine_credential, vault_credential,
                                                           deploy_jobtemplate, launch_kwargs,
                                                           get, post, rando):
    vault_cred_first = Credential(
        name='Vault #1',
        credential_type=vault_credential.credential_type,
        inputs={
            'vault_password': 'ASK',
            'vault_id': 'abc'
        }
    )
    vault_cred_first.save()
    vault_cred_second = Credential(
        name='Vault #2',
        credential_type=vault_credential.credential_type,
        inputs={
            'vault_password': 'ASK',
            'vault_id': 'xyz'
        }
    )
    vault_cred_second.save()
    deploy_jobtemplate.credentials.add(vault_cred_first)
    deploy_jobtemplate.credentials.add(vault_cred_second)
    deploy_jobtemplate.execute_role.members.add(rando)
    deploy_jobtemplate.save()

    url = reverse('api:job_template_launch', kwargs={'pk': deploy_jobtemplate.pk})
    resp = get(url, rando, expect=200)

    assert {
        'credential_type': vault_cred_first.credential_type_id,
        'passwords_needed': ['vault_password.abc'],
        'vault_id': u'abc',
        'name': u'Vault #1',
        'id': vault_cred_first.id
    } in resp.data['defaults']['credentials']
    assert {
        'credential_type': vault_cred_second.credential_type_id,
        'passwords_needed': ['vault_password.xyz'],
        'vault_id': u'xyz',
        'name': u'Vault #2',
        'id': vault_cred_second.id
    } in resp.data['defaults']['credentials']

    assert resp.data['passwords_needed_to_start'] == ['vault_password.abc', 'vault_password.xyz']
    assert sum([
        cred['passwords_needed'] for cred in resp.data['defaults']['credentials']
        if cred['credential_type'] == vault_credential.credential_type_id
    ], []) == ['vault_password.abc', 'vault_password.xyz']

    resp = post(url, rando, expect=400)
    assert resp.data['passwords_needed_to_start'] == ['vault_password.abc', 'vault_password.xyz']

    with mock.patch.object(Job, 'signal_start') as signal_start:
        post(url, launch_kwargs, rando, expect=201)
        signal_start.assert_called_with(**{
            'vault_password.abc': 'vault-me-1',
            'vault_password.xyz': 'vault-me-2'
        })


@pytest.mark.django_db
def test_job_launch_fails_with_missing_ssh_password(machine_credential, deploy_jobtemplate, post,
                                                    rando):
    machine_credential.inputs['password'] = 'ASK'
    machine_credential.save()
    deploy_jobtemplate.credentials.add(machine_credential)
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
    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    machine_credential.inputs['password'] = 'ASK'
    machine_credential.save()
    deploy_jobtemplate.credentials.add(machine_credential)
    deploy_jobtemplate.credentials.add(vault_credential)
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
    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    deploy_jobtemplate.credentials.add(machine_credential)
    deploy_jobtemplate.credentials.add(vault_credential)
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
def test_job_launch_JT_with_credentials(machine_credential, credential, net_credential, kube_credential, deploy_jobtemplate):
    deploy_jobtemplate.ask_credential_on_launch = True
    deploy_jobtemplate.save()

    kv = dict(credentials=[credential.pk, net_credential.pk, machine_credential.pk, kube_credential.pk])
    serializer = JobLaunchSerializer(data=kv, context={'template': deploy_jobtemplate})
    validated = serializer.is_valid()
    assert validated, serializer.errors

    kv['credentials'] = [credential, net_credential, machine_credential, kube_credential]  # convert to internal value
    prompted_fields, ignored_fields, errors = deploy_jobtemplate._accept_or_ignore_job_kwargs(
        _exclude_errors=['required', 'prompts'], **kv)
    job_obj = deploy_jobtemplate.create_unified_job(**prompted_fields)

    creds = job_obj.credentials.all()
    assert len(creds) == 4
    assert credential in creds
    assert net_credential in creds
    assert machine_credential in creds
    assert kube_credential in creds


@pytest.mark.django_db
def test_job_branch_rejected_and_accepted(deploy_jobtemplate):
    deploy_jobtemplate.ask_scm_branch_on_launch = True
    deploy_jobtemplate.save()
    prompted_fields, ignored_fields, errors = deploy_jobtemplate._accept_or_ignore_job_kwargs(
        scm_branch='foobar'
    )
    assert 'scm_branch' in ignored_fields
    assert 'does not allow override of branch' in errors['scm_branch']

    deploy_jobtemplate.project.allow_override = True
    deploy_jobtemplate.project.save()
    prompted_fields, ignored_fields, errors = deploy_jobtemplate._accept_or_ignore_job_kwargs(
        scm_branch='foobar'
    )
    assert not ignored_fields
    assert prompted_fields['scm_branch'] == 'foobar'


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
        with mocker.patch.object(UnifiedJobTemplate, 'create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation', return_value={}):
                with mocker.patch('awx.api.views.JobTemplateCallback.find_matching_hosts', return_value=[host]):
                    post(
                        reverse('api:job_template_callback', kwargs={'pk': job_template.pk}),
                        dict(extra_vars={"job_launch_var": 3, "survey_var": 4}, host_config_key="foo"),
                        admin_user, expect=201, format='json')
                    assert UnifiedJobTemplate.create_unified_job.called
                    call_args = UnifiedJobTemplate.create_unified_job.call_args[1]
                    call_args.pop('_eager_fields', None)  # internal purposes
                    assert call_args == {
                        'extra_vars': {'survey_var': 4, 'job_launch_var': 3},
                        'limit': 'single-host'
                    }

    mock_job.signal_start.assert_called_once()


@pytest.mark.django_db
@pytest.mark.job_runtime_vars
def test_callback_ignore_unprompted_extra_var(mocker, survey_spec_factory, job_template_prompts, post, admin_user, host):
    job_template = job_template_prompts(False)
    job_template.host_config_key = "foo"
    job_template.save()

    with mocker.patch('awx.main.access.BaseAccess.check_license'):
        mock_job = mocker.MagicMock(spec=Job, id=968, extra_vars={"job_launch_var": 3, "survey_var": 4})
        with mocker.patch.object(UnifiedJobTemplate, 'create_unified_job', return_value=mock_job):
            with mocker.patch('awx.api.serializers.JobSerializer.to_representation', return_value={}):
                with mocker.patch('awx.api.views.JobTemplateCallback.find_matching_hosts', return_value=[host]):
                    post(
                        reverse('api:job_template_callback', kwargs={'pk':job_template.pk}),
                        dict(extra_vars={"job_launch_var": 3, "survey_var": 4}, host_config_key="foo"),
                        admin_user, expect=201, format='json')
                    assert UnifiedJobTemplate.create_unified_job.called
                    call_args = UnifiedJobTemplate.create_unified_job.call_args[1]
                    call_args.pop('_eager_fields', None)  # internal purposes
                    assert call_args == {
                        'limit': 'single-host'
                    }

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
