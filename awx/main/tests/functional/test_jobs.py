import redis
import pytest
from unittest import mock
import json

from awx.main.models import (
    Job,
    Instance,
    Host,
    JobHostSummary,
    Inventory,
    InventoryUpdate,
    InventorySource,
    Project,
    ProjectUpdate,
    SystemJob,
    AdHocCommand,
    InstanceGroup,
    Label,
    ExecutionEnvironment,
    Credential,
    CredentialType,
    CredentialInputSource,
    Organization,
    JobTemplate,
)
from awx.main.tasks import jobs
from awx.main.tasks.system import cluster_node_heartbeat
from awx.main.utils.db import bulk_update_sorted_by_id
from ansible_base.lib.testing.util import feature_flag_enabled, feature_flag_disabled

from django.db import OperationalError
from django.test.utils import override_settings


@pytest.fixture
def job_template_with_credentials():
    """
    Factory fixture that creates a job template with specified credentials.

    Usage:
        job = job_template_with_credentials(ssh_cred, vault_cred)
    """

    def _create_job_template(
        *credentials, org_name='test-org', project_name='test-project', inventory_name='test-inventory', jt_name='test-jt', playbook='test.yml'
    ):
        """
        Create a job template with the given credentials.

        Args:
            *credentials: Variable number of Credential objects to attach to the job template
            org_name: Name for the organization
            project_name: Name for the project
            inventory_name: Name for the inventory
            jt_name: Name for the job template
            playbook: Playbook filename

        Returns:
            Job instance created from the job template
        """
        org = Organization.objects.create(name=org_name)
        proj = Project.objects.create(name=project_name, organization=org)
        inv = Inventory.objects.create(name=inventory_name, organization=org)
        jt = JobTemplate.objects.create(name=jt_name, project=proj, inventory=inv, playbook=playbook)

        if credentials:
            jt.credentials.add(*credentials)

        return jt.create_unified_job()

    return _create_job_template


@pytest.mark.django_db
def test_orphan_unified_job_creation(instance, inventory):
    job = Job.objects.create(job_template=None, inventory=inventory, name='hi world')
    job2 = job.copy_unified_job()
    assert job2.job_template is None
    assert job2.inventory == inventory
    assert job2.name == 'hi world'
    assert job.job_type == job2.job_type
    assert job2.launch_type == 'relaunch'


@pytest.mark.django_db
@mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes', lambda *args, **kwargs: None)
@mock.patch('awx.main.models.ha.get_cpu_effective_capacity', lambda cpu, is_control_node: 8)
@mock.patch('awx.main.models.ha.get_mem_effective_capacity', lambda mem, is_control_node: 62)
def test_job_capacity_and_with_inactive_node():
    i = Instance.objects.create(hostname='test-1')
    i.save_health_data('18.0.1', 2, 8000)
    assert i.enabled is True
    assert i.capacity_adjustment == 1.0
    assert i.capacity == 62
    i.enabled = False
    i.save()
    with override_settings(CLUSTER_HOST_ID=i.hostname):
        with mock.patch.object(redis.client.Redis, 'ping', lambda self: True):
            cluster_node_heartbeat(None)
        i = Instance.objects.get(id=i.id)
        assert i.capacity == 0


@pytest.mark.django_db
@mock.patch('awx.main.models.ha.get_cpu_effective_capacity', lambda cpu: 8)
@mock.patch('awx.main.models.ha.get_mem_effective_capacity', lambda mem: 62)
def test_job_capacity_with_redis_disabled():
    i = Instance.objects.create(hostname='test-1')

    def _raise(self):
        raise redis.ConnectionError()

    with mock.patch.object(redis.client.Redis, 'ping', _raise):
        i.local_health_check()
    assert i.capacity == 0


@pytest.mark.django_db
def test_job_type_name():
    job = Job.objects.create()
    assert job.job_type_name == 'job'

    ahc = AdHocCommand.objects.create()
    assert ahc.job_type_name == 'ad_hoc_command'

    source = InventorySource.objects.create(source='ec2')
    source.save()
    iu = InventoryUpdate.objects.create(inventory_source=source, source='ec2')
    assert iu.job_type_name == 'inventory_update'

    proj = Project.objects.create()
    proj.save()
    pu = ProjectUpdate.objects.create(project=proj)
    assert pu.job_type_name == 'project_update'

    sjob = SystemJob.objects.create()
    assert sjob.job_type_name == 'system_job'


@pytest.mark.django_db
def test_job_notification_data(inventory, machine_credential, project):
    encrypted_str = "$encrypted$"
    job = Job.objects.create(
        job_template=None,
        inventory=inventory,
        name='hi world',
        extra_vars=json.dumps({"SSN": "123-45-6789"}),
        survey_passwords={"SSN": encrypted_str},
        project=project,
    )
    job.credentials.set([machine_credential])
    notification_data = job.notification_data(block=0)
    assert json.loads(notification_data['extra_vars'])['SSN'] == encrypted_str


@pytest.mark.django_db
def test_job_notification_host_data(inventory, machine_credential, project, job_template, host):
    job = Job.objects.create(job_template=job_template, inventory=inventory, name='hi world', project=project)
    JobHostSummary.objects.create(job=job, host=host, changed=1, dark=2, failures=3, ok=4, processed=3, skipped=2, rescued=1, ignored=0)
    assert job.notification_data()['hosts'] == {
        'single-host': {'failed': True, 'changed': 1, 'dark': 2, 'failures': 3, 'ok': 4, 'processed': 3, 'skipped': 2, 'rescued': 1, 'ignored': 0}
    }


@pytest.mark.django_db
class TestAnsibleFactsSave:
    current_call = 0

    def test_update_hosts_deleted_host(self, inventory):
        hosts = [Host.objects.create(inventory=inventory, name=f'foo{i}') for i in range(3)]
        for host in hosts:
            host.ansible_facts = {'foo': 'bar'}
        last_pk = hosts[-1].pk
        assert inventory.hosts.count() == 3
        Host.objects.get(pk=last_pk).delete()
        assert inventory.hosts.count() == 2
        bulk_update_sorted_by_id(Host, hosts, fields=['ansible_facts'])
        assert inventory.hosts.count() == 2
        for host in inventory.hosts.all():
            host.refresh_from_db()
            assert host.ansible_facts == {'foo': 'bar'}

    def test_update_hosts_forever_deadlock(self, inventory, mocker):
        hosts = [Host.objects.create(inventory=inventory, name=f'foo{i}') for i in range(3)]
        for host in hosts:
            host.ansible_facts = {'foo': 'bar'}
        db_mock = mocker.patch('awx.main.tasks.facts.Host.objects.bulk_update')
        db_mock.side_effect = OperationalError('deadlock detected')
        with pytest.raises(OperationalError):
            bulk_update_sorted_by_id(Host, hosts, fields=['ansible_facts'])

    def fake_bulk_update(self, host_list):
        if self.current_call > 2:
            return Host.objects.bulk_update(host_list, ['ansible_facts', 'ansible_facts_modified'])
        self.current_call += 1
        raise OperationalError('deadlock detected')


@pytest.mark.django_db
def test_update_hosts_resolved_deadlock(inventory, mocker):

    hosts = [Host.objects.create(inventory=inventory, name=f'foo{i}') for i in range(3)]

    # Set ansible_facts for each host
    for host in hosts:
        host.ansible_facts = {'foo': 'bar'}

    bulk_update_sorted_by_id(Host, hosts, fields=['ansible_facts'])

    # Save changes and refresh from DB to ensure the updated facts are saved
    for host in hosts:
        host.save()  # Ensure changes are persisted in the DB
        host.refresh_from_db()  # Refresh from DB to get latest data

    # Assert that the ansible_facts were updated correctly
    for host in inventory.hosts.all():
        assert host.ansible_facts == {'foo': 'bar'}

    bulk_update_sorted_by_id(Host, hosts, fields=['ansible_facts'])


@pytest.mark.django_db
class TestLaunchConfig:
    def test_null_creation_from_prompts(self):
        job = Job.objects.create()
        data = {
            "credentials": [],
            "extra_vars": {},
            "limit": None,
            "job_type": None,
            "execution_environment": None,
            "instance_groups": None,
            "labels": None,
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)
        assert config is None

    def test_only_limit_defined(self, job_template):
        job = Job.objects.create(job_template=job_template)
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": "",
            "execution_environment": None,
            "instance_groups": None,
            "labels": None,
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)
        assert config.char_prompts == {"limit": ""}
        assert not config.credentials.exists()
        assert config.prompts_dict() == {"limit": ""}

    def test_many_to_many_fields(self, job_template, organization):
        job = Job.objects.create(job_template=job_template)
        ig1 = InstanceGroup.objects.create(name='bar')
        ig2 = InstanceGroup.objects.create(name='foo')
        job_template.instance_groups.add(ig2)
        label1 = Label.objects.create(name='foo', description='bar', organization=organization)
        label2 = Label.objects.create(name='faz', description='baz', organization=organization)
        # Order should matter here which is why we do 2 and then 1
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": None,
            "execution_environment": None,
            "instance_groups": [ig2, ig1],
            "labels": [label2, label1],
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)

        assert config.instance_groups.exists()
        config_instance_group_ids = [item.id for item in config.instance_groups.all()]
        assert config_instance_group_ids == [ig2.id, ig1.id]

        assert config.labels.exists()
        config_label_ids = [item.id for item in config.labels.all()]
        assert config_label_ids == [label2.id, label1.id]

    def test_pk_field(self, job_template, organization):
        job = Job.objects.create(job_template=job_template)
        ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
        # Order should matter here which is why we do 2 and then 1
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": None,
            "execution_environment": ee,
            "instance_groups": [],
            "labels": [],
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)

        assert config.execution_environment
        # We just write the PK instead of trying to assign an item, that happens on the save
        assert config.execution_environment_id == ee.id


@pytest.mark.django_db
def test_base_task_credentials_property(job_template_with_credentials):
    """Test that _credentials property caches credentials and doesn't re-query."""
    task = jobs.RunJob()

    # Create real credentials
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()
    vault_type = CredentialType.defaults['vault']()
    vault_type.save()

    ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')
    vault_cred = Credential.objects.create(credential_type=vault_type, name='vault-cred')

    # Create a job with credentials using fixture
    job = job_template_with_credentials(ssh_cred, vault_cred)
    task.instance = job

    # First access should build credentials
    result1 = task._credentials
    assert len(result1) == 2
    assert isinstance(result1, list)

    # Second access should return cached value (we can verify by checking it's the same list object)
    result2 = task._credentials
    assert result2 is result1  # Same object reference


@pytest.mark.django_db
def test_run_job_machine_credential(job_template_with_credentials):
    """Test _machine_credential returns ssh credential from cache."""
    task = jobs.RunJob()

    # Create credentials
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()
    vault_type = CredentialType.defaults['vault']()
    vault_type.save()

    ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')
    vault_cred = Credential.objects.create(credential_type=vault_type, name='vault-cred')

    # Create a job using fixture
    job = job_template_with_credentials(ssh_cred, vault_cred)
    task.instance = job

    # Set cached credentials
    task._credentials = [ssh_cred, vault_cred]

    # Get machine credential
    result = task._machine_credential
    assert result == ssh_cred
    assert result.credential_type.kind == 'ssh'


@pytest.mark.django_db
def test_run_job_machine_credential_none(job_template_with_credentials):
    """Test _machine_credential returns None when no ssh credential exists."""
    task = jobs.RunJob()

    # Create only vault credential
    vault_type = CredentialType.defaults['vault']()
    vault_type.save()
    vault_cred = Credential.objects.create(credential_type=vault_type, name='vault-cred')

    job = job_template_with_credentials(vault_cred)
    task.instance = job

    # Set cached credentials
    task._credentials = [vault_cred]

    # Get machine credential
    result = task._machine_credential
    assert result is None


@pytest.mark.django_db
def test_run_job_vault_credentials(job_template_with_credentials):
    """Test _vault_credentials returns all vault credentials from cache."""
    task = jobs.RunJob()

    # Create credentials
    vault_type = CredentialType.defaults['vault']()
    vault_type.save()
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()

    vault_cred1 = Credential.objects.create(credential_type=vault_type, name='vault-1')
    vault_cred2 = Credential.objects.create(credential_type=vault_type, name='vault-2')
    ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')

    job = job_template_with_credentials(vault_cred1, ssh_cred, vault_cred2)
    task.instance = job

    # Set cached credentials
    task._credentials = [vault_cred1, ssh_cred, vault_cred2]

    # Get vault credentials
    result = task._vault_credentials
    assert len(result) == 2
    assert vault_cred1 in result
    assert vault_cred2 in result
    assert ssh_cred not in result


@pytest.mark.django_db
def test_run_job_network_credentials(job_template_with_credentials):
    """Test _network_credentials returns all network credentials from cache."""
    task = jobs.RunJob()

    # Create credentials
    net_type = CredentialType.defaults['net']()
    net_type.save()
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()

    net_cred = Credential.objects.create(credential_type=net_type, name='net-cred')
    ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')

    job = job_template_with_credentials(net_cred, ssh_cred)
    task.instance = job

    # Set cached credentials
    task._credentials = [net_cred, ssh_cred]

    # Get network credentials
    result = task._network_credentials
    assert len(result) == 1
    assert result[0] == net_cred


@pytest.mark.django_db
def test_run_job_cloud_credentials(job_template_with_credentials):
    """Test _cloud_credentials returns all cloud credentials from cache."""
    task = jobs.RunJob()

    # Create credentials
    aws_type = CredentialType.defaults['aws']()
    aws_type.save()
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()

    aws_cred = Credential.objects.create(credential_type=aws_type, name='aws-cred')
    ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')

    job = job_template_with_credentials(aws_cred, ssh_cred)
    task.instance = job

    # Set cached credentials
    task._credentials = [aws_cred, ssh_cred]

    # Get cloud credentials
    result = task._cloud_credentials
    assert len(result) == 1
    assert result[0] == aws_cred


@pytest.mark.django_db
@override_settings(RESOURCE_SERVER={'URL': 'https://gateway.example.com', 'SECRET_KEY': 'test-secret-key', 'VALIDATE_HTTPS': False})
def test_populate_workload_identity_tokens_with_flag_enabled(job_template_with_credentials, mocker):
    """Test populate_workload_identity_tokens sets context when flag is enabled."""
    with feature_flag_enabled('FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED'):
        task = jobs.RunJob()

        # Create credential types
        ssh_type = CredentialType.defaults['ssh']()
        ssh_type.save()

        # Create a workload identity credential type
        hashivault_type = CredentialType(
            name='HashiCorp Vault Secret Lookup (OIDC)',
            kind='cloud',
            managed=False,
            inputs={
                'fields': [
                    {'id': 'jwt_aud', 'type': 'string', 'label': 'JWT Audience'},
                    {'id': 'workload_identity_token', 'type': 'string', 'label': 'Workload Identity Token', 'secret': True, 'internal': True},
                ]
            },
        )
        hashivault_type.save()

        # Create credentials
        ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')
        source_cred = Credential.objects.create(credential_type=hashivault_type, name='vault-source', inputs={'jwt_aud': 'https://vault.example.com'})
        target_cred = Credential.objects.create(credential_type=ssh_type, name='target-cred', inputs={'username': 'testuser'})

        # Create input source linking source credential to target credential
        input_source = CredentialInputSource.objects.create(
            target_credential=target_cred, source_credential=source_cred, input_field_name='password', metadata={'path': 'secret/data/password'}
        )

        # Create a job using fixture
        job = job_template_with_credentials(target_cred, ssh_cred)
        task.instance = job

        # Override cached_property so the loop uses these exact Python objects
        task._credentials = [target_cred, ssh_cred]

        # Mock only the HTTP response from the Gateway workload identity endpoint
        mock_response = mocker.Mock(status_code=200)
        mock_response.json.return_value = {'jwt': 'eyJ.test.jwt'}

        mock_request = mocker.patch('requests.request', return_value=mock_response, autospec=True)

        task.populate_workload_identity_tokens()

        # Verify the HTTP call was made to the correct endpoint
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs['method'] == 'POST'
        assert '/api/gateway/v1/workload_identity_tokens' in call_kwargs['url']

        # Verify context was set on the credential, keyed by input source PK
        assert input_source.pk in target_cred.context
        assert target_cred.context[input_source.pk]['workload_identity_token'] == 'eyJ.test.jwt'


@pytest.mark.django_db
def test_populate_workload_identity_tokens_with_flag_disabled(job_template_with_credentials):
    """Test populate_workload_identity_tokens sets error status when flag is disabled."""
    with feature_flag_disabled('FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED'):
        task = jobs.RunJob()

        # Create credential types
        ssh_type = CredentialType.defaults['ssh']()
        ssh_type.save()

        # Create a workload identity credential type
        hashivault_type = CredentialType(
            name='HashiCorp Vault Secret Lookup (OIDC)',
            kind='cloud',
            managed=False,
            inputs={
                'fields': [
                    {'id': 'jwt_aud', 'type': 'string', 'label': 'JWT Audience'},
                    {'id': 'workload_identity_token', 'type': 'string', 'label': 'Workload Identity Token', 'secret': True, 'internal': True},
                ]
            },
        )
        hashivault_type.save()

        # Create credentials
        source_cred = Credential.objects.create(credential_type=hashivault_type, name='vault-source')
        target_cred = Credential.objects.create(credential_type=ssh_type, name='target-cred', inputs={'username': 'testuser'})

        # Create input source linking source credential to target credential
        # Note: Creates the relationship that will trigger the feature flag check
        CredentialInputSource.objects.create(
            target_credential=target_cred, source_credential=source_cred, input_field_name='password', metadata={'path': 'secret/data/password'}
        )

        # Create a job using fixture
        job = job_template_with_credentials(target_cred)
        task.instance = job

        # Set cached credentials
        task._credentials = [target_cred]

        task.populate_workload_identity_tokens()

        # Verify job status was set to error
        job.refresh_from_db()
        assert job.status == 'error'
        assert 'FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED' in job.job_explanation
        assert 'vault-source' in job.job_explanation


@pytest.mark.django_db
@override_settings(RESOURCE_SERVER={'URL': 'https://gateway.example.com', 'SECRET_KEY': 'test-secret-key', 'VALIDATE_HTTPS': False})
def test_populate_workload_identity_tokens_multiple_input_sources_per_credential(job_template_with_credentials, mocker):
    """Test that a single credential with two input sources from different workload identity
    credential types gets a separate JWT token for each input source, keyed by input source PK."""
    with feature_flag_enabled('FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED'):
        task = jobs.RunJob()

        # Create credential types
        ssh_type = CredentialType.defaults['ssh']()
        ssh_type.save()

        # Create two different workload identity credential types
        hashivault_kv_type = CredentialType(
            name='HashiCorp Vault Secret Lookup (OIDC)',
            kind='cloud',
            managed=False,
            inputs={
                'fields': [
                    {'id': 'jwt_aud', 'type': 'string', 'label': 'JWT Audience'},
                    {'id': 'workload_identity_token', 'type': 'string', 'label': 'Workload Identity Token', 'secret': True, 'internal': True},
                ]
            },
        )
        hashivault_kv_type.save()

        hashivault_ssh_type = CredentialType(
            name='HashiCorp Vault Signed SSH (OIDC)',
            kind='cloud',
            managed=False,
            inputs={
                'fields': [
                    {'id': 'jwt_aud', 'type': 'string', 'label': 'JWT Audience'},
                    {'id': 'workload_identity_token', 'type': 'string', 'label': 'Workload Identity Token', 'secret': True, 'internal': True},
                ]
            },
        )
        hashivault_ssh_type.save()

        # Create source credentials with different audiences
        source_cred_kv = Credential.objects.create(
            credential_type=hashivault_kv_type, name='vault-kv-source', inputs={'jwt_aud': 'https://vault-kv.example.com'}
        )
        source_cred_ssh = Credential.objects.create(
            credential_type=hashivault_ssh_type, name='vault-ssh-source', inputs={'jwt_aud': 'https://vault-ssh.example.com'}
        )

        # Create target credential that uses both sources for different fields
        target_cred = Credential.objects.create(credential_type=ssh_type, name='target-cred', inputs={'username': 'testuser'})

        # Create two input sources on the same target credential, each for a different field
        input_source_password = CredentialInputSource.objects.create(
            target_credential=target_cred, source_credential=source_cred_kv, input_field_name='password', metadata={'path': 'secret/data/password'}
        )
        input_source_ssh_key = CredentialInputSource.objects.create(
            target_credential=target_cred, source_credential=source_cred_ssh, input_field_name='ssh_key_data', metadata={'path': 'secret/data/ssh_key'}
        )

        # Create a job using fixture
        job = job_template_with_credentials(target_cred)
        task.instance = job

        # Override cached_property so the loop uses this exact Python object
        task._credentials = [target_cred]

        # Mock HTTP responses - return different JWTs for each call
        response_kv = mocker.Mock(status_code=200)
        response_kv.json.return_value = {'jwt': 'eyJ.kv.jwt'}

        response_ssh = mocker.Mock(status_code=200)
        response_ssh.json.return_value = {'jwt': 'eyJ.ssh.jwt'}

        mock_request = mocker.patch('requests.request', side_effect=[response_kv, response_ssh], autospec=True)

        task.populate_workload_identity_tokens()

        # Verify two separate HTTP calls were made (one per input source)
        assert mock_request.call_count == 2

        # Verify each call used the correct audience from its source credential
        audiences_requested = {call.kwargs.get('json', {}).get('audience', '') for call in mock_request.call_args_list}
        assert 'https://vault-kv.example.com' in audiences_requested
        assert 'https://vault-ssh.example.com' in audiences_requested

        # Verify context on the target credential has both tokens, keyed by input source PK
        assert input_source_password.pk in target_cred.context
        assert input_source_ssh_key.pk in target_cred.context
        assert target_cred.context[input_source_password.pk]['workload_identity_token'] == 'eyJ.kv.jwt'
        assert target_cred.context[input_source_ssh_key.pk]['workload_identity_token'] == 'eyJ.ssh.jwt'


@pytest.mark.django_db
def test_populate_workload_identity_tokens_without_workload_identity_credentials(job_template_with_credentials, mocker):
    """Test populate_workload_identity_tokens does nothing when no workload identity credentials."""
    with feature_flag_enabled('FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED'):
        task = jobs.RunJob()

        # Create only standard credentials (no workload identity)
        ssh_type = CredentialType.defaults['ssh']()
        ssh_type.save()
        vault_type = CredentialType.defaults['vault']()
        vault_type.save()

        ssh_cred = Credential.objects.create(credential_type=ssh_type, name='ssh-cred')
        vault_cred = Credential.objects.create(credential_type=vault_type, name='vault-cred')

        # Create a job using fixture
        job = job_template_with_credentials(ssh_cred, vault_cred)
        task.instance = job

        # Set cached credentials
        task._credentials = [ssh_cred, vault_cred]

        mocker.patch('awx.main.tasks.jobs.populate_claims_for_workload', return_value={'job_id': 123}, autospec=True)

        task.populate_workload_identity_tokens()

        # Verify no context was set
        assert not hasattr(ssh_cred, '_context') or ssh_cred.context == {}
        assert not hasattr(vault_cred, '_context') or vault_cred.context == {}
