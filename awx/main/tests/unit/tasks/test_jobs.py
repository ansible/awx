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


@mock.patch('awx.main.tasks.facts.update_hosts')
@mock.patch('awx.main.tasks.facts.settings')
@mock.patch('awx.main.tasks.jobs.create_partition', return_value=True)
def test_pre_post_run_hook_facts(mock_create_partition, mock_facts_settings, update_hosts, private_data_dir, execution_environment):
    # creates inventory_object with two hosts
    inventory = Inventory(pk=1)
    mock_inventory = mock.MagicMock(spec=Inventory, wraps=inventory)
    mock_inventory._state = mock.MagicMock()
    qs_hosts = QuerySet()
    hosts = [
        Host(id=1, name='host1', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=mock_inventory),
        Host(id=2, name='host2', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=mock_inventory),
    ]
    qs_hosts._result_cache = hosts
    qs_hosts.only = mock.MagicMock(return_value=hosts)
    mock_inventory.hosts = qs_hosts
    assert mock_inventory.hosts.count() == 2

    # creates job object with fact_cache enabled
    org = Organization(pk=1)
    proj = Project(pk=1, organization=org)
    job = mock.MagicMock(spec=Job, use_fact_cache=True, project=proj, organization=org, job_slice_number=1, job_slice_count=1)
    job.inventory = mock_inventory
    job.execution_environment = execution_environment
    job.get_hosts_for_fact_cache = Job.get_hosts_for_fact_cache.__get__(job)  # to run original method
    job.job_env.get = mock.MagicMock(return_value=private_data_dir)

    # creates the task object with job object as instance
    mock_facts_settings.ANSIBLE_FACT_CACHE_TIMEOUT = False  # defines timeout to false
    task = jobs.RunJob()
    task.instance = job
    task.update_model = mock.Mock(return_value=job)
    task.model.objects.get = mock.Mock(return_value=job)

    # run pre_run_hook
    task.facts_write_time = task.pre_run_hook(job, private_data_dir)

    # updates inventory with one more host
    hosts.append(Host(id=3, name='host3', ansible_facts={"added": True}, ansible_facts_modified=now(), inventory=mock_inventory))
    assert mock_inventory.hosts.count() == 3

    # run post_run_hook
    task.runner_callback.artifacts_processed = mock.MagicMock(return_value=True)

    task.post_run_hook(job, "success")
    assert mock_inventory.hosts[2].ansible_facts == {"added": True}


@mock.patch('awx.main.tasks.facts.update_hosts')
@mock.patch('awx.main.tasks.facts.settings')
@mock.patch('awx.main.tasks.jobs.create_partition', return_value=True)
def test_pre_post_run_hook_facts_deleted_sliced(mock_create_partition, mock_facts_settings, update_hosts, private_data_dir, execution_environment):
    # creates inventory_object with two hosts
    inventory = Inventory(pk=1)
    mock_inventory = mock.MagicMock(spec=Inventory, wraps=inventory)
    mock_inventory._state = mock.MagicMock()
    qs_hosts = QuerySet()
    hosts = [Host(id=num, name=f'host{num}', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=now(), inventory=mock_inventory) for num in range(999)]

    qs_hosts._result_cache = hosts
    qs_hosts.only = mock.MagicMock(return_value=hosts)
    mock_inventory.hosts = qs_hosts
    assert mock_inventory.hosts.count() == 999

    # creates job object with fact_cache enabled
    org = Organization(pk=1)
    proj = Project(pk=1, organization=org)
    job = mock.MagicMock(spec=Job, use_fact_cache=True, project=proj, organization=org, job_slice_number=1, job_slice_count=3)
    job.inventory = mock_inventory
    job.execution_environment = execution_environment
    job.get_hosts_for_fact_cache = Job.get_hosts_for_fact_cache.__get__(job)  # to run original method
    job.job_env.get = mock.MagicMock(return_value=private_data_dir)

    # creates the task object with job object as instance
    mock_facts_settings.ANSIBLE_FACT_CACHE_TIMEOUT = False
    task = jobs.RunJob()
    task.instance = job
    task.update_model = mock.Mock(return_value=job)
    task.model.objects.get = mock.Mock(return_value=job)

    # run pre_run_hook
    task.facts_write_time = task.pre_run_hook(job, private_data_dir)

    hosts.pop(1)
    assert mock_inventory.hosts.count() == 998

    # run post_run_hook
    task.runner_callback.artifacts_processed = mock.MagicMock(return_value=True)
    task.post_run_hook(job, "success")

    for host in hosts:
        assert host.ansible_facts == {"a": 1, "b": 2}

    failures = []
    for host in hosts:
        try:
            assert host.ansible_facts == {"a": 1, "b": 2, "unexpected_key": "bad"}
        except AssertionError:
            failures.append("Host named {} has facts {}".format(host.name, host.ansible_facts))

    assert len(failures) > 0, f"Failures occurred for the following hosts: {failures}"


@mock.patch('awx.main.tasks.facts.update_hosts')
@mock.patch('awx.main.tasks.facts.settings')
def test_invalid_host_facts(mock_facts_settings, update_hosts, private_data_dir, execution_environment):
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
    update_hosts(mock_inventory.hosts)

    with pytest.raises(pytest.fail.Exception):
        if failures:
            pytest.fail(f" {len(failures)} facts cleared failures : {','.join(failures)}")
