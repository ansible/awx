import pytest

from awx.main.models import (
    Job,
    Inventory,
    Host,
)


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
def hosts():
    return [
        Host(name='host1', ansible_facts={"a": 1, "b": 2}),
        Host(name='host2', ansible_facts={"a": 1, "b": 2}),
        Host(name='host3', ansible_facts={"a": 1, "b": 2}),
    ]


@pytest.fixture
def hosts2():
    return [
        Host(name='host2', ansible_facts="foobar"),
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

    job._get_memcache_connection().set.assert_any_call('{}'.format(5), [h.name for h in hosts])
    for host in hosts:  
        job._get_memcache_connection().set.assert_any_call('{}-{}'.format(5, host.name), host.ansible_facts)
        job._get_memcache_connection().set.assert_any_call('{}-{}-modified'.format(5, host.name), False)


def test_start_job_fact_cache_existing_host(hosts, hosts2, job, job2, inventory, mocker):

    job.start_job_fact_cache()

    for host in hosts:  
        job._get_memcache_connection().set.assert_any_call('{}-{}'.format(5, host.name), host.ansible_facts)
        job._get_memcache_connection().set.assert_any_call('{}-{}-modified'.format(5, host.name), False)

    job._get_memcache_connection().set.reset_mock()

    job2.start_job_fact_cache()

    # Ensure hosts2 ansible_facts didn't overwrite hosts ansible_facts
    ansible_facts_cached = job._get_memcache_connection().get('{}-{}'.format(5, hosts2[0].name))
    assert ansible_facts_cached == hosts[1].ansible_facts


def test_finish_job_fact_cache(job, hosts, inventory, mocker):

    job.start_job_fact_cache()

    host = hosts[1]
    host_key = job.memcached_fact_host_key(host.name)
    modified_key = job.memcached_fact_modified_key(host.name)
    host.save = mocker.Mock()

    job._get_memcache_connection().set(host_key, 'blah')
    job._get_memcache_connection().set(modified_key, True)
    
    job.finish_job_fact_cache()

    assert host.ansible_facts == 'blah'
    host.save.assert_called_once_with()

