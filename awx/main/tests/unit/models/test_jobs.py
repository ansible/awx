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
from awx.main.tasks.facts import start_fact_cache, finish_fact_cache


@pytest.fixture
def hosts():
    inventory = Inventory(id=5)
    return [
        Host(name='host1', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
        Host(name='host2', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
        Host(name='host3', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
        Host(name=u'Iñtërnâtiônàlizætiøn', ansible_facts={"a": 1, "b": 2}, inventory=inventory),
    ]


@pytest.fixture
def inventory(mocker, hosts):
    mocker.patch('awx.main.tasks.facts._get_inventory_hosts', return_value=hosts)
    return Inventory(id=5)


@pytest.fixture
def job(mocker, inventory):
    j = Job(inventory=inventory, id=2)
    # j._get_inventory_hosts = mocker.Mock(return_value=hosts)
    return j


def test_start_job_fact_cache(hosts, job, inventory, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    last_modified = start_fact_cache(inventory, fact_cache, timeout=0)

    for host in hosts:
        filepath = os.path.join(fact_cache, host.name)
        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            assert f.read() == json.dumps(host.ansible_facts)
        assert os.path.getmtime(filepath) <= last_modified


def test_fact_cache_with_invalid_path_traversal(job, inventory, tmpdir, mocker):
    mocker.patch(
        'awx.main.tasks.facts._get_inventory_hosts',
        return_value=[
            Host(
                name='../foo',
                ansible_facts={"a": 1, "b": 2},
            ),
        ],
    )

    fact_cache = os.path.join(tmpdir, 'facts')
    start_fact_cache(inventory, fact_cache, timeout=0)
    # a file called "foo" should _not_ be written outside the facts dir
    assert os.listdir(os.path.join(fact_cache, '..')) == ['facts']


def test_finish_job_fact_cache_with_existing_data(job, hosts, inventory, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    last_modified = start_fact_cache(inventory, fact_cache, timeout=0)

    bulk_update = mocker.patch('django.db.models.query.QuerySet.bulk_update')

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

    finish_fact_cache(inventory, fact_cache, last_modified)

    for host in (hosts[0], hosts[2], hosts[3]):
        assert host.ansible_facts == {"a": 1, "b": 2}
        assert host.ansible_facts_modified is None
    assert hosts[1].ansible_facts == ansible_facts_new
    bulk_update.assert_called_once_with([hosts[1]], ['ansible_facts', 'ansible_facts_modified'])


def test_finish_job_fact_cache_with_bad_data(job, hosts, inventory, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    last_modified = start_fact_cache(inventory, fact_cache, timeout=0)

    bulk_update = mocker.patch('django.db.models.query.QuerySet.bulk_update')

    for h in hosts:
        filepath = os.path.join(fact_cache, h.name)
        with open(filepath, 'w') as f:
            f.write('not valid json!')
            f.flush()
            new_modification_time = time.time() + 3600
            os.utime(filepath, (new_modification_time, new_modification_time))

    finish_fact_cache(inventory, fact_cache, last_modified)

    bulk_update.assert_not_called()


def test_finish_job_fact_cache_clear(job, hosts, inventory, mocker, tmpdir):
    fact_cache = os.path.join(tmpdir, 'facts')
    last_modified = start_fact_cache(inventory, fact_cache, timeout=0)

    bulk_update = mocker.patch('django.db.models.query.QuerySet.bulk_update')

    os.remove(os.path.join(fact_cache, hosts[1].name))
    finish_fact_cache(inventory, fact_cache, last_modified)

    for host in (hosts[0], hosts[2], hosts[3]):
        assert host.ansible_facts == {"a": 1, "b": 2}
        assert host.ansible_facts_modified is None
    assert hosts[1].ansible_facts == {}
    bulk_update.assert_called_once_with([hosts[1]], ['ansible_facts', 'ansible_facts_modified'])
