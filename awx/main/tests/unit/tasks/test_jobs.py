# -*- coding: utf-8 -*-
import pytest
from unittest import mock

from awx.main.models import (
    Inventory,
    Host,
)

from django.utils.timezone import now
from django.db.models.query import QuerySet

from awx.main.models import (
    Job,
    Organization,
    Project,
    JobTemplate,
    UnifiedJobTemplate,
    InstanceGroup,
    ExecutionEnvironment,
    ProjectUpdate,
    InventoryUpdate,
    InventorySource,
    AdHocCommand,
)
from awx.main.tasks import jobs
from ansible_base.lib.workload_identity.controller import AutomationControllerJobScope


@pytest.fixture
def private_data_dir(tmp_path):
    private_data = tmp_path / 'awx_pdd'
    private_data.mkdir()
    for subfolder in ('inventory', 'env'):
        (private_data / subfolder).mkdir()
    return str(private_data)


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


@mock.patch('awx.main.tasks.facts.settings')
@mock.patch('awx.main.tasks.jobs.create_partition', return_value=True)
def test_pre_post_run_hook_facts(mock_create_partition, mock_facts_settings, private_data_dir, execution_environment):
    # Create mocked inventory and host queryset
    inventory = mock.MagicMock(spec=Inventory, pk=1, kind='')
    host1 = mock.MagicMock(spec=Host, id=1, name='host1', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=inventory)
    host2 = mock.MagicMock(spec=Host, id=2, name='host2', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=inventory)

    # Mock hosts queryset — must support .only().filter().order_by().iterator() chain
    hosts = [host1, host2]
    qs_hosts = mock.MagicMock(spec=QuerySet)
    qs_hosts._result_cache = hosts
    qs_hosts.__iter__ = lambda self: iter(self._result_cache)
    qs_hosts.only.return_value = qs_hosts
    qs_hosts.filter.return_value = qs_hosts
    qs_hosts.order_by.return_value = qs_hosts
    qs_hosts.iterator.side_effect = lambda: iter(qs_hosts._result_cache)
    qs_hosts.count.side_effect = lambda: len(qs_hosts._result_cache)
    inventory.hosts = qs_hosts

    # Create mocked job object
    org = mock.MagicMock(spec=Organization, pk=1)
    proj = mock.MagicMock(spec=Project, pk=1, organization=org)
    job = mock.MagicMock(
        spec=Job,
        pk=1,
        id=1,
        use_fact_cache=True,
        project=proj,
        organization=org,
        job_slice_number=1,
        job_slice_count=1,
        inventory=inventory,
        inventory_id=inventory.pk,
        created=now(),
        execution_environment=execution_environment,
    )
    job.get_hosts_for_fact_cache = Job.get_hosts_for_fact_cache.__get__(job)
    job.job_env.get = mock.MagicMock(return_value=private_data_dir)

    # Mock RunJob task
    mock_facts_settings.ANSIBLE_FACT_CACHE_TIMEOUT = False
    task = jobs.RunJob()
    task.instance = job
    task.update_model = mock.Mock(return_value=job)
    task.model.objects.get = mock.Mock(return_value=job)

    # Run pre_run_hook
    task.facts_write_time = task.pre_run_hook(job, private_data_dir)

    # Add a third mocked host
    host3 = mock.MagicMock(spec=Host, id=3, name='host3', ansible_facts={"added": True}, ansible_facts_modified=now(), inventory=inventory)
    qs_hosts._result_cache.append(host3)
    assert inventory.hosts.count() == 3

    # Run post_run_hook
    task.runner_callback.artifacts_processed = mock.MagicMock(return_value=True)
    task.post_run_hook(job, "success")

    # Verify final host facts
    assert qs_hosts._result_cache[2].ansible_facts == {"added": True}


@mock.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')
@mock.patch('awx.main.tasks.facts.settings')
@mock.patch('awx.main.tasks.jobs.create_partition', return_value=True)
def test_pre_post_run_hook_facts_deleted_sliced(
    mock_create_partition, mock_facts_settings, mock_bulk_update_sorted_by_id, private_data_dir, execution_environment
):
    # Fully mocked inventory
    mock_inventory = mock.MagicMock(spec=Inventory, pk=1, kind='')

    # Create 999 mocked Host instances
    hosts = []
    for i in range(999):
        host = mock.MagicMock(spec=Host)
        host.id = i
        host.name = f'host{i}'
        host.ansible_facts = {"a": 1, "b": 2}
        host.ansible_facts_modified = now()
        host.inventory = mock_inventory
        hosts.append(host)

    # Mock inventory.hosts behavior — must support .only().filter().order_by().iterator() chain
    mock_qs_hosts = mock.MagicMock()
    mock_qs_hosts.only.return_value = mock_qs_hosts
    mock_qs_hosts.filter.return_value = mock_qs_hosts
    mock_qs_hosts.order_by.return_value = mock_qs_hosts
    mock_qs_hosts.iterator.side_effect = lambda: iter(hosts)
    mock_qs_hosts.count.return_value = 999
    mock_inventory.hosts = mock_qs_hosts

    # Mock Organization and Project
    org = mock.MagicMock(spec=Organization)
    proj = mock.MagicMock(spec=Project)
    proj.organization = org

    # Mock job object
    job = mock.MagicMock(spec=Job)
    job.pk = 2
    job.id = 2
    job.use_fact_cache = True
    job.project = proj
    job.organization = org
    job.job_slice_number = 1
    job.job_slice_count = 3
    job.execution_environment = execution_environment
    job.inventory = mock_inventory
    job.inventory_id = mock_inventory.pk
    job.created = now()
    job.job_env.get.return_value = private_data_dir

    # Bind actual method for host filtering
    job.get_hosts_for_fact_cache = Job.get_hosts_for_fact_cache.__get__(job)

    # Mock task instance
    mock_facts_settings.ANSIBLE_FACT_CACHE_TIMEOUT = False
    task = jobs.RunJob()
    task.instance = job
    task.update_model = mock.Mock(return_value=job)
    task.model.objects.get = mock.Mock(return_value=job)

    # Call pre_run_hook
    task.facts_write_time = task.pre_run_hook(job, private_data_dir)

    # Simulate one host deletion
    hosts.pop(1)
    mock_qs_hosts.count.return_value = 998

    # Call post_run_hook
    task.runner_callback.artifacts_processed = mock.MagicMock(return_value=True)
    task.post_run_hook(job, "success")

    # Assert that ansible_facts were preserved
    for host in hosts:
        assert host.ansible_facts == {"a": 1, "b": 2}

    # Add expected failure cases
    failures = []
    for host in hosts:
        try:
            assert host.ansible_facts == {"a": 1, "b": 2, "unexpected_key": "bad"}
        except AssertionError:
            failures.append(f"Host named {host.name} has facts {host.ansible_facts}")

    assert len(failures) > 0, f"Failures occurred for the following hosts: {failures}"


@mock.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')
@mock.patch('awx.main.tasks.facts.settings')
def test_invalid_host_facts(mock_facts_settings, bulk_update_sorted_by_id, private_data_dir, execution_environment):
    inventory = Inventory(pk=1)
    mock_inventory = mock.MagicMock(spec=Inventory, wraps=inventory)
    mock_inventory._state = mock.MagicMock()

    hosts = [
        Host(id=0, name='host0', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=mock_inventory),
        Host(id=1, name='host1', ansible_facts={"a": 1, "b": 2, "unexpected_key": "bad"}, ansible_facts_modified=now(), inventory=mock_inventory),
    ]
    mock_inventory.hosts = hosts

    failures = []
    for host in mock_inventory.hosts:
        assert "a" in host.ansible_facts
        if "unexpected_key" in host.ansible_facts:
            failures.append(host.name)

    mock_facts_settings.SOME_SETTING = True
    bulk_update_sorted_by_id(Host, mock_inventory.hosts, fields=['ansible_facts'])

    with pytest.raises(pytest.fail.Exception):
        if failures:
            pytest.fail(f" {len(failures)} facts cleared failures : {','.join(failures)}")


@pytest.mark.parametrize(
    "job_attrs,expected_claims",
    [
        (
            {
                'id': 100,
                'name': 'Test Job',
                'job_type': 'run',
                'launch_type': 'manual',
                'playbook': 'site.yml',
                'organization': Organization(id=1, name='Test Org'),
                'inventory': Inventory(id=2, name='Test Inventory'),
                'project': Project(id=3, name='Test Project'),
                'execution_environment': ExecutionEnvironment(id=4, name='Test EE'),
                'job_template': JobTemplate(id=5, name='Test Job Template'),
                'unified_job_template': UnifiedJobTemplate(pk=6, id=6, name='Test Unified Job Template'),
                'instance_group': InstanceGroup(id=7, name='Test Instance Group'),
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 100,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Test Job',
                AutomationControllerJobScope.CLAIM_JOB_TYPE: 'run',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'manual',
                AutomationControllerJobScope.CLAIM_PLAYBOOK_NAME: 'site.yml',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_NAME: 'Test Org',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_ID: 1,
                AutomationControllerJobScope.CLAIM_INVENTORY_NAME: 'Test Inventory',
                AutomationControllerJobScope.CLAIM_INVENTORY_ID: 2,
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_NAME: 'Test EE',
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_ID: 4,
                AutomationControllerJobScope.CLAIM_PROJECT_NAME: 'Test Project',
                AutomationControllerJobScope.CLAIM_PROJECT_ID: 3,
                AutomationControllerJobScope.CLAIM_JOB_TEMPLATE_NAME: 'Test Job Template',
                AutomationControllerJobScope.CLAIM_JOB_TEMPLATE_ID: 5,
                AutomationControllerJobScope.CLAIM_UNIFIED_JOB_TEMPLATE_NAME: 'Test Unified Job Template',
                AutomationControllerJobScope.CLAIM_UNIFIED_JOB_TEMPLATE_ID: 6,
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_NAME: 'Test Instance Group',
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_ID: 7,
            },
        ),
        (
            {'id': 100, 'name': 'Test', 'job_type': 'run', 'launch_type': 'manual', 'organization': Organization(id=1, name='')},
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 100,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Test',
                AutomationControllerJobScope.CLAIM_JOB_TYPE: 'run',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'manual',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_ID: 1,
                AutomationControllerJobScope.CLAIM_ORGANIZATION_NAME: '',
                AutomationControllerJobScope.CLAIM_PLAYBOOK_NAME: '',
            },
        ),
    ],
)
def test_populate_claims_for_workload(job_attrs, expected_claims):
    job = Job()

    for attr, value in job_attrs.items():
        setattr(job, attr, value)

    claims = jobs.populate_claims_for_workload(job)
    assert claims == expected_claims


@pytest.mark.parametrize(
    "workload_attrs,expected_claims",
    [
        (
            {
                'id': 200,
                'name': 'Git Sync',
                'job_type': 'check',
                'launch_type': 'sync',
                'organization': Organization(id=1, name='Test Org'),
                'project': Project(pk=3, id=3, name='Test Project'),
                'unified_job_template': Project(pk=3, id=3, name='Test Project'),
                'execution_environment': ExecutionEnvironment(id=4, name='Test EE'),
                'instance_group': InstanceGroup(id=7, name='Test Instance Group'),
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 200,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Git Sync',
                AutomationControllerJobScope.CLAIM_JOB_TYPE: 'check',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'sync',
                AutomationControllerJobScope.CLAIM_LAUNCHED_BY_NAME: 'Test Project',
                AutomationControllerJobScope.CLAIM_LAUNCHED_BY_ID: 3,
                AutomationControllerJobScope.CLAIM_ORGANIZATION_NAME: 'Test Org',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_ID: 1,
                AutomationControllerJobScope.CLAIM_PROJECT_NAME: 'Test Project',
                AutomationControllerJobScope.CLAIM_PROJECT_ID: 3,
                AutomationControllerJobScope.CLAIM_UNIFIED_JOB_TEMPLATE_NAME: 'Test Project',
                AutomationControllerJobScope.CLAIM_UNIFIED_JOB_TEMPLATE_ID: 3,
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_NAME: 'Test EE',
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_ID: 4,
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_NAME: 'Test Instance Group',
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_ID: 7,
            },
        ),
        (
            {
                'id': 201,
                'name': 'Minimal Project Update',
                'job_type': 'run',
                'launch_type': 'manual',
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 201,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Minimal Project Update',
                AutomationControllerJobScope.CLAIM_JOB_TYPE: 'run',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'manual',
            },
        ),
    ],
)
def test_populate_claims_for_project_update(workload_attrs, expected_claims):
    project_update = ProjectUpdate()
    for attr, value in workload_attrs.items():
        setattr(project_update, attr, value)

    claims = jobs.populate_claims_for_workload(project_update)
    assert claims == expected_claims


@pytest.mark.parametrize(
    "workload_attrs,expected_claims",
    [
        (
            {
                'id': 300,
                'name': 'AWS Sync',
                'launch_type': 'scheduled',
                'organization': Organization(id=1, name='Test Org'),
                'inventory': Inventory(id=2, name='AWS Inventory'),
                'unified_job_template': InventorySource(pk=8, id=8, name='AWS Source'),
                'execution_environment': ExecutionEnvironment(id=4, name='Test EE'),
                'instance_group': InstanceGroup(id=7, name='Test Instance Group'),
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 300,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'AWS Sync',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'scheduled',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_NAME: 'Test Org',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_ID: 1,
                AutomationControllerJobScope.CLAIM_INVENTORY_NAME: 'AWS Inventory',
                AutomationControllerJobScope.CLAIM_INVENTORY_ID: 2,
                AutomationControllerJobScope.CLAIM_UNIFIED_JOB_TEMPLATE_NAME: 'AWS Source',
                AutomationControllerJobScope.CLAIM_UNIFIED_JOB_TEMPLATE_ID: 8,
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_NAME: 'Test EE',
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_ID: 4,
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_NAME: 'Test Instance Group',
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_ID: 7,
            },
        ),
        (
            {
                'id': 301,
                'name': 'Minimal Inventory Update',
                'launch_type': 'manual',
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 301,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Minimal Inventory Update',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'manual',
            },
        ),
    ],
)
def test_populate_claims_for_inventory_update(workload_attrs, expected_claims):
    inventory_update = InventoryUpdate()
    for attr, value in workload_attrs.items():
        setattr(inventory_update, attr, value)

    claims = jobs.populate_claims_for_workload(inventory_update)
    assert claims == expected_claims


@pytest.mark.parametrize(
    "workload_attrs,expected_claims",
    [
        (
            {
                'id': 400,
                'name': 'Ping All Hosts',
                'job_type': 'run',
                'launch_type': 'manual',
                'organization': Organization(id=1, name='Test Org'),
                'inventory': Inventory(id=2, name='Test Inventory'),
                'execution_environment': ExecutionEnvironment(id=4, name='Test EE'),
                'instance_group': InstanceGroup(id=7, name='Test Instance Group'),
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 400,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Ping All Hosts',
                AutomationControllerJobScope.CLAIM_JOB_TYPE: 'run',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'manual',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_NAME: 'Test Org',
                AutomationControllerJobScope.CLAIM_ORGANIZATION_ID: 1,
                AutomationControllerJobScope.CLAIM_INVENTORY_NAME: 'Test Inventory',
                AutomationControllerJobScope.CLAIM_INVENTORY_ID: 2,
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_NAME: 'Test EE',
                AutomationControllerJobScope.CLAIM_EXECUTION_ENVIRONMENT_ID: 4,
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_NAME: 'Test Instance Group',
                AutomationControllerJobScope.CLAIM_INSTANCE_GROUP_ID: 7,
            },
        ),
        (
            {
                'id': 401,
                'name': 'Minimal Ad Hoc',
                'job_type': 'run',
                'launch_type': 'manual',
            },
            {
                AutomationControllerJobScope.CLAIM_JOB_ID: 401,
                AutomationControllerJobScope.CLAIM_JOB_NAME: 'Minimal Ad Hoc',
                AutomationControllerJobScope.CLAIM_JOB_TYPE: 'run',
                AutomationControllerJobScope.CLAIM_LAUNCH_TYPE: 'manual',
            },
        ),
    ],
)
def test_populate_claims_for_adhoc_command(workload_attrs, expected_claims):
    adhoc_command = AdHocCommand()
    for attr, value in workload_attrs.items():
        setattr(adhoc_command, attr, value)

    claims = jobs.populate_claims_for_workload(adhoc_command)
    assert claims == expected_claims


@mock.patch('awx.main.utils.workload_identity.get_workload_identity_client')
def test_retrieve_workload_identity_jwt_returns_jwt_from_client(mock_get_client):
    """retrieve_workload_identity_jwt returns the JWT string from the client."""
    mock_client = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_response.jwt = 'eyJ.test.jwt'
    mock_client.request_workload_jwt.return_value = mock_response
    mock_get_client.return_value = mock_client

    unified_job = Job()
    unified_job.id = 42
    unified_job.name = 'Test Job'
    unified_job.launch_type = 'manual'
    unified_job.organization = Organization(id=1, name='Test Org')
    unified_job.unified_job_template = None
    unified_job.instance_group = None

    result = jobs.retrieve_workload_identity_jwt(unified_job, audience='https://api.example.com', scope='aap_controller_automation_job')

    assert result == 'eyJ.test.jwt'
    mock_client.request_workload_jwt.assert_called_once()
    call_kwargs = mock_client.request_workload_jwt.call_args[1]
    assert call_kwargs['audience'] == 'https://api.example.com'
    assert call_kwargs['scope'] == 'aap_controller_automation_job'
    assert 'claims' in call_kwargs
    assert call_kwargs['claims'][AutomationControllerJobScope.CLAIM_JOB_ID] == 42
    assert call_kwargs['claims'][AutomationControllerJobScope.CLAIM_JOB_NAME] == 'Test Job'


@mock.patch('awx.main.utils.workload_identity.get_workload_identity_client')
def test_retrieve_workload_identity_jwt_passes_audience_and_scope(mock_get_client):
    """retrieve_workload_identity_jwt passes audience and scope to the client."""
    mock_client = mock.MagicMock()
    mock_client.request_workload_jwt.return_value = mock.MagicMock(jwt='token')
    mock_get_client.return_value = mock_client

    unified_job = mock.MagicMock()
    audience = 'custom_audience'
    scope = 'custom_scope'
    with mock.patch('awx.main.tasks.jobs.populate_claims_for_workload', return_value={'job_id': 1}):
        jobs.retrieve_workload_identity_jwt(unified_job, audience=audience, scope=scope)

    mock_client.request_workload_jwt.assert_called_once_with(claims={'job_id': 1}, scope=scope, audience=audience)


@mock.patch('awx.main.utils.workload_identity.get_workload_identity_client')
def test_retrieve_workload_identity_jwt_passes_workload_ttl(mock_get_client):
    """retrieve_workload_identity_jwt passes workload_ttl_seconds when provided."""
    mock_client = mock.Mock()
    mock_client.request_workload_jwt.return_value = mock.Mock(jwt='token')
    mock_get_client.return_value = mock_client

    unified_job = mock.MagicMock()
    with mock.patch('awx.main.tasks.jobs.populate_claims_for_workload', return_value={'job_id': 1}):
        jobs.retrieve_workload_identity_jwt(
            unified_job,
            audience='https://vault.example.com',
            scope='aap_controller_automation_job',
            workload_ttl_seconds=3600,
        )

    mock_client.request_workload_jwt.assert_called_once_with(
        claims={'job_id': 1},
        scope='aap_controller_automation_job',
        audience='https://vault.example.com',
        workload_ttl_seconds=3600,
    )


@mock.patch('awx.main.utils.workload_identity.get_workload_identity_client')
def test_retrieve_workload_identity_jwt_raises_when_client_not_configured(mock_get_client):
    """retrieve_workload_identity_jwt raises RuntimeError when client is None."""
    mock_get_client.return_value = None

    unified_job = mock.MagicMock()

    with pytest.raises(RuntimeError, match="Workload identity client is not configured"):
        jobs.retrieve_workload_identity_jwt(unified_job, audience='test_audience', scope='test_scope')


@pytest.mark.parametrize('effective_timeout,expected_ttl', [(3600, 3600), (0, None)])
@mock.patch('awx.main.tasks.jobs.retrieve_workload_identity_jwt')
@mock.patch('awx.main.tasks.jobs.flag_enabled', return_value=True)
def test_populate_workload_identity_tokens_passes_get_instance_timeout_to_client(mock_flag_enabled, mock_retrieve_jwt, effective_timeout, expected_ttl):
    """populate_workload_identity_tokens passes get_instance_timeout() value as workload_ttl_seconds to retrieve_workload_identity_jwt."""
    mock_retrieve_jwt.return_value = 'eyJ.test.jwt'

    task = jobs.RunJob()
    task.instance = mock.MagicMock()

    # Minimal credential with workload identity input source
    credential_ctx = {}
    input_src = mock.MagicMock()
    input_src.pk = 1
    input_src.source_credential = mock.MagicMock()
    input_src.source_credential.get_input.return_value = 'https://vault.example.com'
    input_src.source_credential.name = 'vault-cred'
    input_src.source_credential.credential_type = mock.MagicMock()
    input_src.source_credential.credential_type.inputs = {'fields': [{'id': 'workload_identity_token', 'internal': True}]}

    credential = mock.MagicMock()
    credential.context = credential_ctx
    credential.input_sources = mock.MagicMock()
    credential.input_sources.all.return_value = [input_src]

    task._credentials = [credential]

    with mock.patch.object(task, 'get_instance_timeout', return_value=effective_timeout):
        task.populate_workload_identity_tokens()

    mock_flag_enabled.assert_called_once_with("FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED")
    mock_retrieve_jwt.assert_called_once_with(
        task.instance,
        audience='https://vault.example.com',
        scope=AutomationControllerJobScope.name,
        workload_ttl_seconds=expected_ttl,
    )


class TestRunInventoryUpdatePopulateWorkloadIdentityTokens:
    """Tests for RunInventoryUpdate.populate_workload_identity_tokens."""

    def test_cloud_credential_passed_as_additional_credential(self):
        """The cloud credential is forwarded to super().populate_workload_identity_tokens via additional_credentials."""
        cloud_cred = mock.MagicMock(name='cloud_cred')
        cloud_cred.context = {}

        task = jobs.RunInventoryUpdate()
        task.instance = mock.MagicMock()
        task.instance.get_cloud_credential.return_value = cloud_cred
        task._credentials = []

        with mock.patch.object(jobs.BaseTask, 'populate_workload_identity_tokens') as mock_super:
            task.populate_workload_identity_tokens()

        mock_super.assert_called_once_with(additional_credentials=[cloud_cred])

    def test_no_cloud_credential_calls_super_with_none(self):
        """When there is no cloud credential, super() is called with additional_credentials=None."""
        task = jobs.RunInventoryUpdate()
        task.instance = mock.MagicMock()
        task.instance.get_cloud_credential.return_value = None
        task._credentials = []

        with mock.patch.object(jobs.BaseTask, 'populate_workload_identity_tokens') as mock_super:
            task.populate_workload_identity_tokens()

        mock_super.assert_called_once_with(additional_credentials=None)

    def test_additional_credentials_combined_with_cloud_credential(self):
        """Caller-supplied additional_credentials are combined with the cloud credential."""
        cloud_cred = mock.MagicMock(name='cloud_cred')
        cloud_cred.context = {}
        extra_cred = mock.MagicMock(name='extra_cred')

        task = jobs.RunInventoryUpdate()
        task.instance = mock.MagicMock()
        task.instance.get_cloud_credential.return_value = cloud_cred
        task._credentials = []

        with mock.patch.object(jobs.BaseTask, 'populate_workload_identity_tokens') as mock_super:
            task.populate_workload_identity_tokens(additional_credentials=[extra_cred])

        mock_super.assert_called_once_with(additional_credentials=[extra_cred, cloud_cred])

    def test_cloud_credential_override_after_context_set(self):
        """After OIDC processing, get_cloud_credential is overridden on the instance when context is populated."""
        cloud_cred = mock.MagicMock(name='cloud_cred')
        # Simulate that super().populate_workload_identity_tokens populates context
        cloud_cred.context = {'workload_identity_token': 'eyJ.test.jwt'}

        task = jobs.RunInventoryUpdate()
        task.instance = mock.MagicMock()
        task.instance.get_cloud_credential.return_value = cloud_cred
        task._credentials = []

        with mock.patch.object(jobs.BaseTask, 'populate_workload_identity_tokens'):
            task.populate_workload_identity_tokens()

        # The instance's get_cloud_credential should now return the same object with context
        assert task.instance.get_cloud_credential() is cloud_cred
