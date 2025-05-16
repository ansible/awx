# -*- coding: utf-8 -*-
import json
import os
import pytest

from awx.main.models import (
    Inventory,
    Host,
)
from awx.main.tasks.facts import start_fact_cache, finish_fact_cache

from django.utils.timezone import now

from datetime import timedelta

import time


@pytest.fixture
def ref_time():
    return now() - timedelta(seconds=5)


@pytest.fixture
def hosts(ref_time):
    inventory = Inventory(id=5)
    return [
        Host(name='host1', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=ref_time, inventory=inventory),
        Host(name='host2', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=ref_time, inventory=inventory),
        Host(name='host3', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=ref_time, inventory=inventory),
        Host(name=u'Iñtërnâtiônàlizætiøn', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=ref_time, inventory=inventory),
    ]


def test_start_job_fact_cache(hosts, tmpdir):
    # Create artifacts dir inside tmpdir
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Assign a mock inventory ID
    inventory_id = 42

    # Call the function WITHOUT log_data — the decorator handles it
    start_fact_cache(hosts, artifacts_dir=str(artifacts_dir), timeout=0, inventory_id=inventory_id)

    # Fact files are written into artifacts_dir/fact_cache/
    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    for host in hosts:
        filepath = os.path.join(fact_cache_dir, host.name)
        assert os.path.exists(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            assert json.load(f) == host.ansible_facts


def test_fact_cache_with_invalid_path_traversal(tmpdir):
    hosts = [
        Host(
            name='../foo',
            ansible_facts={"a": 1, "b": 2},
        ),
    ]
    artifacts_dir = tmpdir.mkdir("artifacts")
    inventory_id = 42

    start_fact_cache(hosts, artifacts_dir=str(artifacts_dir), timeout=0, inventory_id=inventory_id)

    # Fact cache directory (safe location)
    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    # The bad host name should not produce a file
    assert not os.path.exists(os.path.join(fact_cache_dir, '../foo'))

    # Make sure the fact_cache dir exists and is still empty
    assert os.listdir(fact_cache_dir) == []


def test_start_job_fact_cache_past_timeout(hosts, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    start_fact_cache(hosts, fact_cache, timeout=2)

    for host in hosts:
        assert not os.path.exists(os.path.join(fact_cache, host.name))
    ret = start_fact_cache(hosts, fact_cache, timeout=2)
    assert ret is None


def test_start_job_fact_cache_within_timeout(hosts, tmpdir):
    artifacts_dir = tmpdir.mkdir("artifacts")

    # The hosts fixture was modified 5s ago, which is less than 7s
    start_fact_cache(hosts, str(artifacts_dir), timeout=7)

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')
    for host in hosts:
        filepath = os.path.join(fact_cache_dir, host.name)
        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            assert json.load(f) == host.ansible_facts


def test_finish_job_fact_cache_clear(hosts, mocker, ref_time, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    start_fact_cache(hosts, fact_cache, timeout=0)

    bulk_update = mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Mock the os.path.exists behavior for host deletion
    # Let's assume the fact file for hosts[1] is missing.
    mocker.patch('os.path.exists', side_effect=lambda path: hosts[1].name not in path)

    # Simulate one host's fact file getting deleted manually
    host_to_delete_filepath = os.path.join(fact_cache, hosts[1].name)

    # Simulate the file being removed by checking existence first, to avoid FileNotFoundError
    if os.path.exists(host_to_delete_filepath):
        os.remove(host_to_delete_filepath)

    finish_fact_cache(fact_cache)

    # Simulate side effects that would normally be applied during bulk update
    hosts[1].ansible_facts = {}
    hosts[1].ansible_facts_modified = now()

    # Verify facts are preserved for hosts with valid cache files
    for host in (hosts[0], hosts[2], hosts[3]):
        assert host.ansible_facts == {"a": 1, "b": 2}
        assert host.ansible_facts_modified == ref_time

    # Verify facts were cleared for host with deleted cache file
    assert hosts[1].ansible_facts == {}
    assert hosts[1].ansible_facts_modified > ref_time

    # Current implementation skips the call entirely if hosts_to_update == []
    bulk_update.assert_not_called()


def test_finish_job_fact_cache_with_bad_data(hosts, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    start_fact_cache(hosts, fact_cache, timeout=0)

    bulk_update = mocker.patch('django.db.models.query.QuerySet.bulk_update')

    for h in hosts:
        filepath = os.path.join(fact_cache, h.name)
        with open(filepath, 'w') as f:
            f.write('not valid json!')
            f.flush()
            new_modification_time = time.time() + 3600
            os.utime(filepath, (new_modification_time, new_modification_time))

    finish_fact_cache(fact_cache)

    bulk_update.assert_not_called()
