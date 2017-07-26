# -*- coding: utf-8 -*-

import pytest

from awx.main.models import (
    Job,
    Inventory,
    Host,
)

import datetime
import json
import base64
from dateutil.tz import tzutc


class CacheMock(object):
    def __init__(self):
        self.d = dict()

    def get(self, key):
        if key not in self.d:
            return None
        return self.d[key]

    def set(self, key, val):
        self.d[key] = val

    def delete(self, key):
        del self.d[key]


@pytest.fixture
def old_time():
    return (datetime.datetime.now(tzutc()) - datetime.timedelta(minutes=60))


@pytest.fixture()
def new_time():
    return (datetime.datetime.now(tzutc()))


@pytest.fixture
def hosts(old_time, inventory):
    return [
        Host(name='host1', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=old_time, inventory=inventory),
        Host(name='host2', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=old_time, inventory=inventory),
        Host(name='host3', ansible_facts={"a": 1, "b": 2}, ansible_facts_modified=old_time, inventory=inventory),
    ]


@pytest.fixture
def hosts2(inventory):
    return [
        Host(name='host2', ansible_facts="foobar", ansible_facts_modified=old_time, inventory=inventory),
    ]


@pytest.fixture
def inventory():
    return Inventory(id=5)


@pytest.fixture
def mock_cache(mocker):
    cache = CacheMock()
    mocker.patch.object(cache, 'set', wraps=cache.set)
    mocker.patch.object(cache, 'get', wraps=cache.get)
    mocker.patch.object(cache, 'delete', wraps=cache.delete)
    return cache


@pytest.fixture
def job(mocker, hosts, inventory, mock_cache):
    j = Job(inventory=inventory, id=2)
    j._get_inventory_hosts = mocker.Mock(return_value=hosts)
    j._get_memcache_connection = mocker.Mock(return_value=mock_cache)
    return j


@pytest.fixture
def job2(mocker, hosts2, inventory, mock_cache):
    j = Job(inventory=inventory, id=3)
    j._get_inventory_hosts = mocker.Mock(return_value=hosts2)
    j._get_memcache_connection = mocker.Mock(return_value=mock_cache)
    return j


def test_start_job_fact_cache(hosts, job, inventory, mocker):

    job.start_job_fact_cache()

    job._get_memcache_connection().set.assert_any_call('5', [h.name for h in hosts])
    for host in hosts:  
        job._get_memcache_connection().set.assert_any_call('{}-{}'.format(5, base64.b64encode(host.name)), json.dumps(host.ansible_facts))
        job._get_memcache_connection().set.assert_any_call('{}-{}-modified'.format(5, base64.b64encode(host.name)), host.ansible_facts_modified.isoformat())


def test_start_job_fact_cache_existing_host(hosts, hosts2, job, job2, inventory, mocker):

    job.start_job_fact_cache()

    for host in hosts:  
        job._get_memcache_connection().set.assert_any_call('{}-{}'.format(5, base64.b64encode(host.name)), json.dumps(host.ansible_facts))
        job._get_memcache_connection().set.assert_any_call('{}-{}-modified'.format(5, base64.b64encode(host.name)), host.ansible_facts_modified.isoformat())

    job._get_memcache_connection().set.reset_mock()

    job2.start_job_fact_cache()

    # Ensure hosts2 ansible_facts didn't overwrite hosts ansible_facts
    ansible_facts_cached = job._get_memcache_connection().get('{}-{}'.format(5, base64.b64encode(hosts2[0].name)))
    assert ansible_facts_cached == json.dumps(hosts[1].ansible_facts)


def test_memcached_fact_host_key_unicode(job):
    host_name = u'Iñtërnâtiônàlizætiøn'
    host_key = job.memcached_fact_host_key(host_name)
    assert host_key == '5-ScOxdMOrcm7DonRpw7Ruw6BsaXrDpnRpw7hu'


def test_memcached_fact_modified_key_unicode(job):
    host_name = u'Iñtërnâtiônàlizætiøn'
    host_key = job.memcached_fact_modified_key(host_name)
    assert host_key == '5-ScOxdMOrcm7DonRpw7Ruw6BsaXrDpnRpw7hu-modified'


def test_finish_job_fact_cache(job, hosts, inventory, mocker, new_time):

    job.start_job_fact_cache()
    for h in hosts:
        h.save = mocker.Mock()

    host_key = job.memcached_fact_host_key(hosts[1].name)
    modified_key = job.memcached_fact_modified_key(hosts[1].name)

    ansible_facts_new = {"foo": "bar", "insights": {"system_id": "updated_by_scan"}}
    job._get_memcache_connection().set(host_key, json.dumps(ansible_facts_new))
    job._get_memcache_connection().set(modified_key, new_time.isoformat())
    
    job.finish_job_fact_cache()

    hosts[0].save.assert_not_called()
    hosts[2].save.assert_not_called()
    assert hosts[1].ansible_facts == ansible_facts_new
    assert hosts[1].insights_system_id == "updated_by_scan"
    hosts[1].save.assert_called_once_with()

