# -*- coding: utf-8 -*-
import json
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

from datetime import timedelta

from awx.main.models import (
    Instance,
    InventorySource,
    Job,
    AdHocCommand,
    ProjectUpdate,
    InventoryUpdate,
    SystemJob,
    JobEvent,
    ProjectUpdateEvent,
    InventoryUpdateEvent,
    AdHocCommandEvent,
    SystemJobEvent,
    build_safe_env,
    Organization,
    Project,
)
from awx.main.tasks import jobs


@pytest.fixture
def private_data_dir():
    private_data = tempfile.mkdtemp(prefix='awx_')
    for subfolder in ('inventory', 'env'):
        runner_subfolder = os.path.join(private_data, subfolder)
        if not os.path.exists(runner_subfolder):
            os.mkdir(runner_subfolder)
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
    mock_facts_settings.ANSIBLE_FACT_CACHE_TIMEOUT = False  # defines timeout to false
    task = jobs.RunJob()
    task.instance = job
    task.update_model = mock.Mock(return_value=job)
    task.model.objects.get = mock.Mock(return_value=job)

    # run pre_run_hook
    task.facts_write_time = task.pre_run_hook(job, private_data_dir)

    # updates inventory with one more host
    hosts.pop(1)
    assert mock_inventory.hosts.count() == 998

    # run post_run_hook
    task.runner_callback.artifacts_processed = mock.MagicMock(return_value=True)

    task.post_run_hook(job, "success")
    failures = []
    for host in mock_inventory.hosts:
        try:
            assert host.ansible_facts == {"a": 1, "b": 2}
        except AssertionError:
            failures.append("Host named {} has facts {}".format(host.name, host.ansible_facts))
    if failures:
        pytest.fail(f" {len(failures)} facts cleared failures : {','.join(failures)}")
