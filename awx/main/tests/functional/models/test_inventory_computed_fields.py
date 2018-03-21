
# Python
import pytest

# AWX
from awx.main.models import Inventory, Host, Group, ActivityStream

# Django
from django.test import TransactionTestCase


@pytest.mark.django_db
class TestWorkflowDAGFunctional(TransactionTestCase):
    def dense_inventory(self, **kwargs):
        """
        Inventory with dense group and host relationships
        """
        return self._make_inventory(strategy='dense', **kwargs)

    def linear_inventory(self, **kwargs):
        """
        Inventory group relationships that go in a line like A->B->C
        and all hosts are members of C
        """
        return self._make_inventory(strategy='linear', **kwargs)

    def _make_inventory(self, strategy='dense', Ng=3, Nh=3, initial_compute=True):
        inv = Inventory.objects.create(name='inv')
        groups = set([])
        hosts = set([])
        last_group = None
        for i in range(Ng):
            group = Group.objects.create(name='g{}'.format(i), inventory=inv)
            if strategy == 'dense':
                for child in groups:
                    group.children.add(child)
            elif strategy == 'linear' and last_group:
                group.children.add(last_group)
            groups.add(group)
            last_group = group
        for i in range(Nh):
            host = Host.objects.create(name='h{}'.format(i), inventory=inv)
            hosts.add(host)
            if strategy == 'dense':
                for group in groups:
                    group.hosts.add(host)
            elif strategy == 'linear':
                group = Group.objects.get(name='g0')
                group.hosts.add(host)
        if initial_compute:
            inv.update_computed_fields()
        return inv

    def print_computed_fields(self, inv):
        import json
        invdict = {}
        for field in [
                'has_active_failures',
                'total_hosts',
                'hosts_with_active_failures',
                'total_groups',
                'groups_with_active_failures',
                'has_inventory_sources',
                'total_inventory_sources',
                'inventory_sources_with_failures'
            ]:
            invdict[field] = getattr(inv, field)
        print ''
        print '  inventory fields '
        print json.dumps(invdict, indent=4)
        print '  group fields '
        for group in inv.groups.all():
            gdict = {}
            print '     group: ' + str(group.name)
            for field in ['total_hosts', 'has_active_failures',
                          'hosts_with_active_failures', 'total_groups',
                          'groups_with_active_failures', 'has_inventory_sources'
                ]:
                gdict[field] = getattr(group, field)
            print json.dumps(gdict, indent=4)
        for host in inv.hosts.all():
            hdict = {}
            print '      host: ' + str(host.name)
            for field in [
                    'has_active_failures',
                    'has_inventory_sources',
                ]:
                hdict[field] = getattr(host, field)
            print json.dumps(hdict, indent=4)

    def test_group_children_map(self):
        inv = self.linear_inventory()
        with self.assertNumQueries(1):
            gc_map = inv.get_group_children_map()
        # In linear inventory, g0 is the final child group
        # gN-1 is the top-most group
        bottom = Group.objects.get(name='g0')
        top = Group.objects.get(name='g2')
        assert bottom.pk not in gc_map
        assert gc_map[top.pk] == set([Group.objects.get(name='g1').pk])

    def test_group_decedents_map(self):
        inv = self.linear_inventory()
        top_group = inv.groups.get(name='g2')
        child_pks, host_pks = inv.get_group_decedents(top_group.pk)
        assert len(child_pks) == 2
        assert len(host_pks) == 3

    def test_existing_group_computed_fields(self):
        inv = self.linear_inventory()
        old_group_data = inv.get_existing_group_computed_fields()
        top_group = inv.groups.get(name='g2')
        assert old_group_data[top_group.pk] == {
            'total_hosts': 3,
            'groups_with_active_failures': 0,
            'has_active_failures': False,
            'has_inventory_sources': False,
            'hosts_with_active_failures': 0,
            'total_groups': 2
        }

    def test_group_differential_update(self):
        inv = self.linear_inventory()
        top_group = inv.groups.get(name='g2')
        assert top_group.total_groups == 3
        assert inv.total_groups == 3
        new_group = top_group.children.create(name='another-group', inventory=inv)
        new_group.update_computed_fields(add=True, parent=top_group)
        top_group.refresh_from_db()
        inv.refresh_from_db()
        assert top_group.total_groups == 4
        assert inv.total_groups == 4

    def test_no_activity_stream(self):
        inv = self.dense_inventory(initial_compute=False)
        starting_entries = ActivityStream.objects.count()
        inv.update_computed_fields()
        assert ActivityStream.objects.count() == starting_entries

    def test_computed_fields_query_number(self):
        inv = self.dense_inventory()
        self.print_computed_fields(inv)
        with self.assertNumQueries(4):
            inv.update_computed_fields()

