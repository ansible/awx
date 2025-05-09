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
)
from awx.main.tasks import jobs


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
