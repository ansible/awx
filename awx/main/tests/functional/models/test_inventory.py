# -*- coding: utf-8 -*-

import pytest
from unittest import mock

from django.core.exceptions import ValidationError

# AWX
from awx.main.models import (
    Host,
    Inventory,
    InventorySource,
    InventoryUpdate,
    Job
)
from awx.main.utils.filters import SmartFilter


@pytest.mark.django_db
class TestInventoryScript:

    def test_hostvars(self, inventory):
        inventory.hosts.create(name='ahost', variables={"foo": "bar"})
        assert inventory.get_script_data(
            hostvars=True
        )['_meta']['hostvars']['ahost'] == {
            'foo': 'bar'
        }

    def test_towervars(self, inventory):
        host = inventory.hosts.create(name='ahost')
        assert inventory.get_script_data(
            hostvars=True,
            towervars=True
        )['_meta']['hostvars']['ahost'] == {
            'remote_tower_enabled': 'true',
            'remote_tower_id': host.id
        }

    def test_all_group(self, inventory):
        inventory.groups.create(name='all', variables={'a1': 'a1'})
        # make sure we return a1 details in output
        data = inventory.get_script_data()
        assert 'all' in data
        assert data['all'] == {
            'hosts': [],
            'children': [],
            'vars': {
                'a1': 'a1'
            }
        }

    def test_grandparent_group(self, inventory):
        g1 = inventory.groups.create(name='g1', variables={'v1': 'v1'})
        g2 = inventory.groups.create(name='g2', variables={'v2': 'v2'})
        h1 = inventory.hosts.create(name='h1')
        # h1 becomes indirect member of g1 group
        g1.children.add(g2)
        g2.hosts.add(h1)
        # make sure we return g1 details in output
        data = inventory.get_script_data(hostvars=1)
        assert 'g1' in data
        assert 'g2' in data
        assert data['g1'] == {
            'hosts': [],
            'children': ['g2'],
            'vars': {'v1': 'v1'}
        }
        assert data['g2'] == {
            'hosts': ['h1'],
            'children': [],
            'vars': {'v2': 'v2'}
        }

    def test_slice_subset(self, inventory):
        for i in range(3):
            inventory.hosts.create(name='host{}'.format(i))
        for i in range(3):
            assert inventory.get_script_data(slice_number=i + 1, slice_count=3) == {
                'all': {'hosts': ['host{}'.format(i)]}
            }

    def test_slice_subset_with_groups(self, inventory):
        hosts = []
        for i in range(3):
            host = inventory.hosts.create(name='host{}'.format(i))
            hosts.append(host)
        g1 = inventory.groups.create(name='contains_all_hosts')
        for host in hosts:
            g1.hosts.add(host)
        g2 = inventory.groups.create(name='contains_two_hosts')
        for host in hosts[:2]:
            g2.hosts.add(host)
        for i in range(3):
            expected_data = {
                'contains_all_hosts': {'hosts': ['host{}'.format(i)], 'children': [], 'vars': {}},
            }
            if i < 2:
                expected_data['contains_two_hosts'] = {'hosts': ['host{}'.format(i)], 'children': [], 'vars': {}}
            data = inventory.get_script_data(slice_number=i + 1, slice_count=3)
            data.pop('all')
            assert data == expected_data


@pytest.mark.django_db
class TestActiveCount:

    def test_host_active_count(self, organization):
        inv1 = Inventory.objects.create(name='inv1', organization=organization)
        inv2 = Inventory.objects.create(name='inv2', organization=organization)
        assert Host.objects.active_count() == 0
        inv1.hosts.create(name='host1')
        inv2.hosts.create(name='host1')
        assert Host.objects.active_count() == 1
        inv1.hosts.create(name='host2')
        assert Host.objects.active_count() == 2

    def test_active_count_minus_tower(self, inventory):
        inventory.hosts.create(name='locally-managed-host')
        source = inventory.inventory_sources.create(
            name='tower-source', source='tower'
        )
        source.hosts.create(
            name='remotely-managed-host', inventory=inventory
        )
        assert Host.objects.active_count() == 1


@pytest.mark.django_db
class TestSCMUpdateFeatures:

    def test_automatic_project_update_on_create(self, inventory, project):
        inv_src = InventorySource(
            source_project=project,
            source_path='inventory_file',
            inventory=inventory,
            update_on_project_update=True,
            source='scm')
        with mock.patch.object(inv_src, 'update') as mck_update:
            inv_src.save()
            mck_update.assert_called_once_with()

    def test_reset_scm_revision(self, scm_inventory_source):
        starting_rev = scm_inventory_source.scm_last_revision
        assert starting_rev != ''
        scm_inventory_source.source_path = '/newfolder/newfile.ini'
        scm_inventory_source.save()
        assert scm_inventory_source.scm_last_revision == ''

    def test_source_location(self, scm_inventory_source):
        # Combines project directory with the inventory file specified
        inventory_update = InventoryUpdate(
            inventory_source=scm_inventory_source,
            source_path=scm_inventory_source.source_path)
        assert inventory_update.get_actual_source_path().endswith('_92__test_proj/inventory_file')

    def test_no_unwanted_updates(self, scm_inventory_source):
        # Changing the non-sensitive fields should not trigger update
        with mock.patch.object(scm_inventory_source.source_project, 'update') as mck_update:
            scm_inventory_source.name = 'edited_inventory'
            scm_inventory_source.description = "I'm testing this!"
            scm_inventory_source.save()
            assert not mck_update.called


@pytest.mark.django_db
class TestRelatedJobs:

    def test_inventory_related(self, inventory):
        job = Job.objects.create(
            inventory=inventory
        )
        assert job.id in [jerb.id for jerb in inventory._get_related_jobs()]

    def test_related_group_jobs(self, group):
        job = Job.objects.create(
            inventory=group.inventory
        )
        assert job.id in [jerb.id for jerb in group._get_related_jobs()]

    def test_related_group_update(self, group):
        src = group.inventory_sources.create(name='foo')
        job = InventoryUpdate.objects.create(
            inventory_source=src
        )
        assert job.id in [jerb.id for jerb in group._get_related_jobs()]


@pytest.mark.django_db
class TestSCMClean:
    def test_clean_update_on_project_update_multiple(self, inventory):
        inv_src1 = InventorySource(inventory=inventory,
                                   update_on_project_update=True,
                                   source='scm')
        inv_src1.clean_update_on_project_update()
        inv_src1.save()

        inv_src1.source_vars = '---\nhello: world'
        inv_src1.clean_update_on_project_update()

        inv_src2 = InventorySource(inventory=inventory,
                                   update_on_project_update=True,
                                   source='scm')

        with pytest.raises(ValidationError):
            inv_src2.clean_update_on_project_update()


@pytest.fixture
def setup_ec2_gce(organization):
    ec2_inv = Inventory.objects.create(name='test_ec2', organization=organization)

    ec2_source = ec2_inv.inventory_sources.create(name='test_ec2_source', source='ec2')
    for i in range(2):
        ec2_host = ec2_inv.hosts.create(name='test_ec2_{0}'.format(i))
        ec2_host.inventory_sources.add(ec2_source)
    ec2_inv.save()

    gce_inv = Inventory.objects.create(name='test_gce', organization=organization)

    gce_source = gce_inv.inventory_sources.create(name='test_gce_source', source='gce')
    gce_host = gce_inv.hosts.create(name='test_gce_host')
    gce_host.inventory_sources.add(gce_source)
    gce_inv.save()


@pytest.fixture
def setup_inventory_groups(inventory, group_factory):

    groupA = group_factory('test_groupA')
    groupB = group_factory('test_groupB')

    host = Host.objects.create(name='single_host', inventory=inventory)

    groupA.hosts.add(host)
    groupA.save()

    groupB.hosts.add(host)
    groupB.save()


@pytest.mark.django_db
def test_inventory_update_name(inventory, inventory_source):
    iu = inventory_source.update()
    assert inventory_source.name != inventory.name
    assert iu.name == inventory.name + ' - ' + inventory_source.name


@pytest.mark.django_db
def test_inventory_name_with_unicode(inventory, inventory_source):
    inventory.name = 'オオオ'
    inventory.save()
    iu = inventory_source.update()
    assert iu.name.startswith(inventory.name)


@pytest.mark.django_db
def test_inventory_update_excessively_long_name(inventory, inventory_source):
    inventory.name = 'a' * 400  # field max length 512
    inventory_source.name = 'b' * 400
    iu = inventory_source.update()
    assert inventory_source.name != inventory.name
    assert iu.name.startswith(inventory.name)


@pytest.mark.django_db
class TestHostManager:
    def test_host_filter_not_smart(self, setup_ec2_gce, organization):
        smart_inventory = Inventory(name='smart',
                                    organization=organization,
                                    host_filter='inventory_sources__source=ec2')
        assert len(smart_inventory.hosts.all()) == 0

    def test_host_distinctness(self, setup_inventory_groups, organization):
        """
        two criteria would both yield the same host, check that we only get 1 copy here
        """
        assert (
            list(SmartFilter.query_from_string('name=single_host or name__startswith=single_')) ==
            [Host.objects.get(name='single_host')]
        )

    # Things we can not easily test due to SQLite backend:
    # 2 organizations with host of same name only has 1 entry in smart inventory
    # smart inventory in 1 organization does not include host from another
    # smart inventory correctly returns hosts in filter in same organization
