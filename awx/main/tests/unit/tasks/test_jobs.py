# -*- coding: utf-8 -*-
import os
import tempfile
import shutil

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
def private_data_dir():
    private_data = tempfile.mkdtemp(prefix='awx_')
    for subfolder in ('inventory', 'env'):
        runner_subfolder = os.path.join(private_data, subfolder)
        os.makedirs(runner_subfolder, exist_ok=True)
    yield private_data
    shutil.rmtree(private_data, True)


@mock.patch('awx.main.tasks.facts.settings')
@mock.patch('awx.main.tasks.jobs.create_partition', return_value=True)
def test_pre_post_run_hook_facts(mock_create_partition, mock_facts_settings, private_data_dir, execution_environment):
    # Create mocked inventory and host queryset
    inventory = mock.MagicMock(spec=Inventory, pk=1)
    host1 = mock.MagicMock(spec=Host, id=1, name='host1', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=inventory)
    host2 = mock.MagicMock(spec=Host, id=2, name='host2', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=inventory)

    # Mock hosts queryset
    hosts = [host1, host2]
    qs_hosts = mock.MagicMock(spec=QuerySet)
    qs_hosts._result_cache = hosts
    qs_hosts.only.return_value = hosts
    qs_hosts.count.side_effect = lambda: len(qs_hosts._result_cache)
    inventory.hosts = qs_hosts

    # Create mocked job object
    org = mock.MagicMock(spec=Organization, pk=1)
    proj = mock.MagicMock(spec=Project, pk=1, organization=org)
    job = mock.MagicMock(
        spec=Job,
        use_fact_cache=True,
        project=proj,
        organization=org,
        job_slice_number=1,
        job_slice_count=1,
        inventory=inventory,
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
def test_pre_post_run_hook_facts_deleted_sliced(mock_create_partition, mock_facts_settings, private_data_dir, execution_environment):
    # Fully mocked inventory
    mock_inventory = mock.MagicMock(spec=Inventory)

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

    # Mock inventory.hosts behavior
    mock_qs_hosts = mock.MagicMock()
    mock_qs_hosts.only.return_value = hosts
    mock_qs_hosts.count.return_value = 999
    mock_inventory.hosts = mock_qs_hosts

    # Mock Organization and Project
    org = mock.MagicMock(spec=Organization)
    proj = mock.MagicMock(spec=Project)
    proj.organization = org

    # Mock job object
    job = mock.MagicMock(spec=Job)
    job.use_fact_cache = True
    job.project = proj
    job.organization = org
    job.job_slice_number = 1
    job.job_slice_count = 3
    job.execution_environment = execution_environment
    job.inventory = mock_inventory
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
