# -*- coding: utf-8 -*-
import json
import os
import time

import pytest

from awx.main.models import (
    Job,
    Inventory,
    Host,
)


@pytest.fixture
def hosts(inventory):
    return [
        Host(name='host1', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
        Host(name='host2', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
        Host(name='host3', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
        Host(name=u'Iñtërnâtiônàlizætiøn', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
    ]


@pytest.fixture
def inventory():
    return Inventory(id=5)


@pytest.fixture
def job(mocker, hosts, inventory):
    j = Job(inventory=inventory, id=2)
    j._get_inventory_hosts = mocker.Mock(return_value=hosts)
    return j


def test_start_job_fact_cache(hosts, job, inventory, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    modified_times = {}
    job.start_job_fact_cache(fact_cache, modified_times, 0)

    for host in hosts:
        filepath = os.path.join(fact_cache, host.name)
        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            assert f.read() == json.dumps(host.ansible_facts)
        assert filepath in modified_times


def test_fact_cache_with_invalid_path_traversal(job, inventory, tmpdir, mocker):
    job._get_inventory_hosts = mocker.Mock(
        return_value=[
            Host(
                name='../foo',
                ansible_facts={"a": 1, "b": 2},
            ),
        ]
    )

    fact_cache = os.path.join(tmpdir, 'facts')
    job.start_job_fact_cache(fact_cache, {}, 0)
    # a file called "foo" should _not_ be written outside the facts dir
    assert os.listdir(os.path.join(fact_cache, '..')) == ['facts']


def test_finish_job_fact_cache_with_existing_data(job, hosts, inventory, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    modified_times = {}
    job.start_job_fact_cache(fact_cache, modified_times, 0)

    for h in hosts:
        h.save = mocker.Mock()

    ansible_facts_new = {"foo": "bar"}
    filepath = os.path.join(fact_cache, hosts[1].name)
    with open(filepath, 'w') as f:
        f.write(json.dumps(ansible_facts_new))
        f.flush()
        # I feel kind of gross about calling `os.utime` by hand, but I noticed
        # that in our container-based dev environment, the resolution for
        # `os.stat()` after a file write was over a second, and I don't want to put
        # a sleep() in this test
        new_modification_time = time.time() + 3600
        os.utime(filepath, (new_modification_time, new_modification_time))

    job.finish_job_fact_cache(fact_cache, modified_times)

    for host in (hosts[0], hosts[2], hosts[3]):
        host.save.assert_not_called()
        assert host.ansible_facts == {"a": 1, "b": 2}
        assert host.ansible_facts_modified is None
    assert hosts[1].ansible_facts == ansible_facts_new
    hosts[1].save.assert_called_once_with()


def test_finish_job_fact_cache_with_bad_data(job, hosts, inventory, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    modified_times = {}
    job.start_job_fact_cache(fact_cache, modified_times, 0)

    for h in hosts:
        h.save = mocker.Mock()

    for h in hosts:
        filepath = os.path.join(fact_cache, h.name)
        with open(filepath, 'w') as f:
            f.write('not valid json!')
            f.flush()
            new_modification_time = time.time() + 3600
            os.utime(filepath, (new_modification_time, new_modification_time))

    job.finish_job_fact_cache(fact_cache, modified_times)

    for h in hosts:
        h.save.assert_not_called()


def test_finish_job_fact_cache_clear(job, hosts, inventory, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    modified_times = {}
    job.start_job_fact_cache(fact_cache, modified_times, 0)

    for h in hosts:
        h.save = mocker.Mock()

    os.remove(os.path.join(fact_cache, hosts[1].name))
    job.finish_job_fact_cache(fact_cache, modified_times)

    for host in (hosts[0], hosts[2], hosts[3]):
        host.save.assert_not_called()
        assert host.ansible_facts == {"a": 1, "b": 2}
        assert host.ansible_facts_modified is None
    assert hosts[1].ansible_facts == {}
    hosts[1].save.assert_called_once_with()
