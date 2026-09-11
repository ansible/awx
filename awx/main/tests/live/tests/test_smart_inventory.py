"""Smart inventory tests that require PostgreSQL.

These tests exercise SmartFilter and smart inventory host resolution against
a real PostgreSQL database. Most are unit-style tests that set ansible_facts
directly on Host objects rather than running playbooks.

The smart inventory HostManager uses DISTINCT ON which requires PostgreSQL,
so any test that reads smart inventory hosts must run here (not in functional/).
"""

import pytest

from awx.main.models import Organization, Inventory, Host, Group
from awx.main.utils.filters import SmartFilter


@pytest.fixture
def fact_org():
    org, _ = Organization.objects.get_or_create(name='smart-inv-fact-test-org')
    return org


@pytest.fixture
def fact_inventory(fact_org):
    inv, created = Inventory.objects.get_or_create(name='smart-inv-fact-test-inv', organization=fact_org)
    if not created:
        inv.hosts.all().delete()
        inv.groups.all().delete()

    groupA = Group.objects.create(name='factGroupA', inventory=inv)
    groupB = Group.objects.create(name='factGroupB', inventory=inv)

    hostA = Host.objects.create(
        name='factHostA',
        inventory=inv,
        ansible_facts={
            'ansible_system': 'Linux',
            'ansible_distribution': 'CentOS',
            'ansible_python': {
                'version': {'major': 3, 'minor': 9, 'micro': 7},
                'version_info': [3, 9, 7, 'final', 0],
            },
            'ansible_env': {'HOME': '/root'},
        },
    )
    hostB = Host.objects.create(
        name='factHostB',
        inventory=inv,
        ansible_facts={
            'ansible_system': 'Linux',
            'ansible_distribution': 'Ubuntu',
            'ansible_python': {
                'version': {'major': 3, 'minor': 11, 'micro': 2},
                'version_info': [3, 11, 2, 'final', 0],
            },
            'ansible_env': {'HOME': '/home/user'},
        },
    )
    hostC = Host.objects.create(
        name='factHostC',
        inventory=inv,
        ansible_facts={
            'ansible_system': 'Darwin',
            'ansible_distribution': 'MacOSX',
            'ansible_python': {
                'version': {'major': 3, 'minor': 10, 'micro': 0},
                'version_info': [3, 10, 0, 'final', 0],
            },
            'ansible_env': {'HOME': '/Users/test'},
        },
    )

    groupA.hosts.add(hostA, hostC)
    groupB.hosts.add(hostB, hostC)

    yield {
        'org': fact_org,
        'inv': inv,
        'hosts': {'hostA': hostA, 'hostB': hostB, 'hostC': hostC},
        'groups': {'groupA': groupA, 'groupB': groupB},
    }

    hostA.delete()
    hostB.delete()
    hostC.delete()
    groupA.delete()
    groupB.delete()


@pytest.fixture
def smart_inventory_factory():
    created = []

    def _factory(name, host_filter, organization):
        inv = Inventory.objects.create(name=name, kind='smart', host_filter=host_filter, organization=organization)
        created.append(inv)
        return inv

    yield _factory
    for inv in reversed(created):
        inv.delete()


@pytest.fixture
def host_factory():
    created = []

    def _factory(**kwargs):
        host = Host.objects.create(**kwargs)
        created.append(host)
        return host

    yield _factory
    for host in reversed(created):
        if host.pk is not None:
            host.delete()


@pytest.fixture
def group_factory():
    created = []

    def _factory(**kwargs):
        group = Group.objects.create(**kwargs)
        created.append(group)
        return group

    yield _factory
    for group in reversed(created):
        group.delete()


def query_names(filter_string):
    return sorted(SmartFilter.query_from_string(filter_string).distinct().values_list('name', flat=True))


# --- Fact-based filter tests (require PostgreSQL for JSONField __contains) ---


def test_fact_based_host_filter(fact_inventory):
    assert query_names('ansible_facts__ansible_system=Linux') == ['factHostA', 'factHostB']
    assert query_names('ansible_facts__ansible_distribution=CentOS') == ['factHostA']
    assert query_names('ansible_facts__ansible_distribution=Ubuntu') == ['factHostB']
    assert query_names('ansible_facts__ansible_system=Darwin') == ['factHostC']
    assert query_names('ansible_facts__ansible_system=Windows') == []


def test_nested_fact_search(fact_inventory):
    assert query_names('ansible_facts__ansible_python__version__major=3') == ['factHostA', 'factHostB', 'factHostC']
    assert query_names('ansible_facts__ansible_python__version__minor=9') == ['factHostA']
    assert query_names('ansible_facts__ansible_python__version__minor=11') == ['factHostB']
    assert query_names('ansible_facts__ansible_env__HOME=/root') == ['factHostA']


def test_list_fact_search(fact_inventory):
    assert query_names('ansible_facts__ansible_python__version_info[]=9') == ['factHostA']
    assert query_names('ansible_facts__ansible_python__version_info[]=11') == ['factHostB']
    assert query_names('ansible_facts__ansible_python__version_info[]=3') == ['factHostA', 'factHostB', 'factHostC']


def test_fact_search_with_or(fact_inventory):
    assert query_names('ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=Linux') == ['factHostA', 'factHostB']
    assert query_names('ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=not_found') == ['factHostA', 'factHostB']
    assert query_names('ansible_facts__ansible_system=not_found or ansible_facts__ansible_system=not_found') == []
    assert query_names('ansible_facts__ansible_system=Linux or ansible_facts__ansible_system=Darwin') == ['factHostA', 'factHostB', 'factHostC']


def test_fact_search_with_and(fact_inventory):
    assert query_names('ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=Linux') == ['factHostA', 'factHostB']
    assert query_names('ansible_facts__ansible_system=Linux and ansible_facts__ansible_system=not_found') == []
    assert query_names('ansible_facts__ansible_system=Linux and ansible_facts__ansible_distribution=CentOS') == ['factHostA']


def test_hybrid_fact_name_group_search(fact_inventory):
    assert query_names('name=factHostA or groups__name=factGroupB or ansible_facts__ansible_system=Linux') == ['factHostA', 'factHostB', 'factHostC']

    assert query_names('name=factHostA or groups__name=factGroupA or ansible_facts__ansible_system=not_found') == ['factHostA', 'factHostC']

    assert query_names('name=factHostA and groups__name=factGroupA and ansible_facts__ansible_system=not_found') == []

    assert query_names('name=factHostA and groups__name=factGroupA and ansible_facts__ansible_system=Linux') == ['factHostA']


def test_advanced_hybrid_with_parentheses(fact_inventory):
    assert query_names('name=factHostA or (groups__name=factGroupB and ansible_facts__ansible_system=not_found)') == ['factHostA']

    assert query_names('name=not_found or (groups__name=factGroupB and ansible_facts__ansible_system=Linux)') == ['factHostB']

    assert query_names('(name=factHostA or groups__name=factGroupB) and ansible_facts__ansible_system=not_found') == []

    assert query_names('(name=factHostA or groups__name=factGroupB) and ansible_facts__ansible_system=Linux') == ['factHostA', 'factHostB']

    assert query_names('(name=factHostC or groups__name=factGroupA) and ansible_facts__ansible_system=Darwin') == ['factHostC']


# --- Smart inventory host resolution tests (require PostgreSQL for DISTINCT ON) ---


def test_smart_inventory_hosts_by_name(fact_inventory, smart_inventory_factory):
    org = fact_inventory['org']
    smart_inv = smart_inventory_factory('smart-by-name', 'name=factHostA', org)
    hosts = sorted(smart_inv.hosts.values_list('name', flat=True))
    assert hosts == ['factHostA']


def test_smart_inventory_hosts_by_group(fact_inventory, smart_inventory_factory):
    org = fact_inventory['org']
    smart_inv = smart_inventory_factory('smart-by-group', 'groups__name=factGroupA', org)
    hosts = sorted(smart_inv.hosts.values_list('name', flat=True))
    assert hosts == ['factHostA', 'factHostC']


def test_smart_inventory_with_facts(fact_inventory, smart_inventory_factory):
    org = fact_inventory['org']
    smart_inv = smart_inventory_factory('fact-smart-inv', 'ansible_facts__ansible_system=Linux', org)
    hosts = sorted(smart_inv.hosts.values_list('name', flat=True))
    assert hosts == ['factHostA', 'factHostB']
    assert smart_inv.total_hosts == 2


def test_smart_inventory_with_nested_facts(fact_inventory, smart_inventory_factory):
    org = fact_inventory['org']
    smart_inv = smart_inventory_factory(
        'nested-fact-smart-inv',
        'ansible_facts__ansible_distribution=CentOS and ansible_facts__ansible_python__version__minor=9',
        org,
    )
    hosts = list(smart_inv.hosts.values_list('name', flat=True))
    assert hosts == ['factHostA']


def test_host_filter_is_organization_scoped(fact_inventory, smart_inventory_factory, host_factory):
    """Smart inventory only includes hosts from its own organization."""
    org1 = fact_inventory['org']
    org2, _ = Organization.objects.get_or_create(name='smart-inv-other-org')
    inv2, _ = Inventory.objects.get_or_create(name='other-org-inv', organization=org2)
    Host.objects.filter(name='factHostA', inventory=inv2).delete()
    host_factory(name='factHostA', inventory=inv2)

    smart_inv = smart_inventory_factory('scoped-smart', 'name=factHostA', org1)
    hosts = list(smart_inv.hosts.all())
    assert len(hosts) == 1
    assert hosts[0].inventory_id == fact_inventory['inv'].id


def test_duplicate_hosts_deduplicated(smart_inventory_factory, host_factory):
    """Same-name hosts across inventories in the same org yield only one smart inventory entry."""
    org, _ = Organization.objects.get_or_create(name='smart-inv-dedup-org')
    inv1, _ = Inventory.objects.get_or_create(name='dedup-inv1', organization=org)
    inv2, _ = Inventory.objects.get_or_create(name='dedup-inv2', organization=org)
    Host.objects.filter(name='dedup_host', inventory__in=[inv1, inv2]).delete()
    host1 = host_factory(name='dedup_host', inventory=inv1)
    host2 = host_factory(name='dedup_host', inventory=inv2)

    smart_inv = smart_inventory_factory('dedup-smart', 'name=dedup_host', org)
    hosts = list(smart_inv.hosts.all())
    assert len(hosts) == 1
    assert hosts[0].id == min(host1.id, host2.id)


def test_host_sources_original_inventory(fact_inventory, smart_inventory_factory):
    """Hosts in a smart inventory still reference their source inventory."""
    org = fact_inventory['org']
    source_inv = fact_inventory['inv']

    smart_inv = smart_inventory_factory('sources-original', 'name=factHostA', org)
    host = smart_inv.hosts.first()
    assert host.inventory_id == source_inv.id


def test_host_updates_reflected_in_smart_inventory(fact_inventory, smart_inventory_factory, host_factory):
    """Editing or deleting a host is immediately reflected in a smart inventory."""
    org = fact_inventory['org']
    inv = fact_inventory['inv']
    host = host_factory(name='mutable_host', inventory=inv)

    smart_inv = smart_inventory_factory('updates-reflected', 'name=mutable_host', org)
    assert smart_inv.hosts.count() == 1

    host.description = 'updated'
    host.save()
    assert smart_inv.hosts.first().description == 'updated'

    host.delete()
    assert smart_inv.hosts.count() == 0


def test_smart_inventory_duplicate_hosts_matching_group_names(fact_inventory, smart_inventory_factory, host_factory, group_factory):
    """A host in multiple groups whose names match an icontains filter appears only once."""
    org = fact_inventory['org']
    inv = fact_inventory['inv']
    g1 = group_factory(name='dedup_another_group', inventory=inv)
    g2 = group_factory(name='dedup_yet_another_group', inventory=inv)
    host = host_factory(name='dedup_grouped_host', inventory=inv)
    g1.hosts.add(host)
    g2.hosts.add(host)

    smart_inv = smart_inventory_factory('group-dedup-smart', 'groups__name__icontains=dedup_another', org)
    assert smart_inv.hosts.count() == 1


def test_smart_inventory_computed_fields(fact_inventory, smart_inventory_factory):
    """Smart inventory total_hosts and related computed fields are accurate."""
    org = fact_inventory['org']
    smart_inv = smart_inventory_factory('computed-fields', 'name=factHostA or name=factHostB', org)
    assert smart_inv.total_hosts == 2
    assert smart_inv.total_groups == 0
    assert smart_inv.total_inventory_sources == 0
    assert smart_inv.has_inventory_sources is False


def test_smart_inventory_matches_host_filter(fact_inventory, smart_inventory_factory):
    """Smart inventory hosts should match the equivalent SmartFilter query."""
    org = fact_inventory['org']
    host_filter = 'groups__name=factGroupA or groups__name=factGroupB'

    smart_inv = smart_inventory_factory('match-filter', host_filter, org)
    smart_names = sorted(smart_inv.hosts.values_list('name', flat=True))
    filter_names = sorted(SmartFilter.query_from_string(host_filter).distinct().values_list('name', flat=True))
    assert smart_names == filter_names
