# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Python
import pytest
from unittest import mock
import os

# Django
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands import inventory_import
from awx.main.models import Inventory, Host, Group, InventorySource
from awx.main.utils.mem_inventory import MemGroup


TEST_INVENTORY_CONTENT = {
    "_meta": {
        "hostvars": {}
    },
    "all": {
        "children": [
            "others",
            "servers",
            "ungrouped"
        ],
        "vars": {
            "vara": "A"
        }
    },
    "dbservers": {
        "hosts": [
            "db1.example.com",
            "db2.example.com"
        ],
        "vars": {
            "dbvar": "ugh"
        }
    },
    "others": {
        "hosts": {
            "10.11.12.13": {},
            "10.12.14.16": {"ansible_port": 8022},
            "::1": {},
            "fe80::1610:9fff:fedd:654b": {},
            "fe80::1610:9fff:fedd:b654": {"ansible_port": 1022}
        }
    },
    "servers": {
        "children": [
            "dbservers",
            "webservers"
        ],
        "vars": {
            "varb": "B"
        }
    },
    "ungrouped": {},
    "webservers": {
        "hosts": {
            "web1.example.com": {
                "ansible_ssh_host": "w1.example.net"
            },
            "web2.example.com": {},
            "web3.example.com": {
                "ansible_port": 1022
            }
        },
        "vars": {
            "webvar": "blah"
        }
    }
}


class MockLoader:

    def __init__(self, *args, **kwargs):
        pass

    def load(self):
        return self._data


def mock_logging(self):
    pass


@pytest.mark.django_db
@pytest.mark.inventory_import
@mock.patch.object(inventory_import.Command, 'check_license', mock.MagicMock())
@mock.patch.object(inventory_import.Command, 'set_logging_level', mock_logging)
class TestInvalidOptionsFunctional:

    def test_invalid_options_invalid_source(self, inventory):
        # Give invalid file to the command
        cmd = inventory_import.Command()
        with mock.patch('django.db.transaction.rollback'):
            with pytest.raises(OSError) as err:
                cmd.handle(
                    inventory_id=inventory.id,
                    source='/tmp/pytest-of-root/pytest-7/inv_files0-invalid')
        assert 'Source does not exist' in str(err.value)

    def test_invalid_inventory_id(self):
        cmd = inventory_import.Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(inventory_id=42, source='/notapath/shouldnotmatter')
        assert 'id = 42' in str(err.value)
        assert 'cannot be found' in str(err.value)

    def test_invalid_inventory_name(self):
        cmd = inventory_import.Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(inventory_name='fooservers', source='/notapath/shouldnotmatter')
        assert 'name = fooservers' in str(err.value)
        assert 'cannot be found' in str(err.value)


@pytest.mark.django_db
@pytest.mark.inventory_import
@mock.patch.object(inventory_import.Command, 'check_license', new=mock.MagicMock())
@mock.patch.object(inventory_import.Command, 'set_logging_level', new=mock_logging)
class TestINIImports:

    @mock.patch.object(inventory_import, 'AnsibleInventoryLoader', MockLoader)
    def test_inventory_single_ini_import(self, inventory, capsys):
        inventory_import.AnsibleInventoryLoader._data = TEST_INVENTORY_CONTENT
        cmd = inventory_import.Command()
        r = cmd.handle(
            inventory_id=inventory.pk, source=__file__,
            method='backport')
        out, err = capsys.readouterr()
        assert r is None
        assert out == ''

        assert set(inventory.groups.values_list('name', flat=True)) == set([
            'servers', 'dbservers', 'webservers', 'others'])

        assert set(inventory.hosts.values_list('name', flat=True)) == set([
            'web1.example.com', 'web2.example.com',
            'web3.example.com', 'db1.example.com',
            'db2.example.com', '10.11.12.13',
            '10.12.14.16', 'fe80::1610:9fff:fedd:654b',
            'fe80::1610:9fff:fedd:b654', '::1'])

        reloaded_inv = Inventory.objects.get(pk=inventory.pk)
        assert reloaded_inv.variables_dict == {'vara': 'A'}

        # Groups vars are applied to host in the newer versions
        assert Host.objects.get(name='web1.example.com').variables_dict == {'ansible_ssh_host': 'w1.example.net'}
        # Old version uses `ansible_ssh_port` but new version uses `ansible_port`
        assert Host.objects.get(name='web3.example.com').variables_dict == {'ansible_port': 1022}
        assert Host.objects.get(name='fe80::1610:9fff:fedd:b654').variables_dict == {'ansible_port': 1022}
        assert Host.objects.get(name='10.12.14.16').variables_dict == {'ansible_port': 8022}

        servers = Group.objects.get(name='servers')
        assert servers.variables_dict == {'varb': 'B'}
        assert set(servers.children.values_list('name', flat=True)) == set(['dbservers', 'webservers'])
        assert servers.hosts.count() == 0

        servers = Group.objects.get(name='dbservers')
        assert servers.variables_dict == {'dbvar': 'ugh'}
        assert servers.children.count() == 0
        assert set(servers.hosts.values_list('name', flat=True)) == set(['db1.example.com','db2.example.com'])

        servers = Group.objects.get(name='webservers')
        assert servers.variables_dict == {'webvar': 'blah'}
        assert servers.children.count() == 0
        assert set(servers.hosts.values_list('name', flat=True)) == set(['web1.example.com','web2.example.com', 'web3.example.com'])

        assert reloaded_inv.inventory_sources.filter().count() == 1
        invsrc = reloaded_inv.inventory_sources.first()
        assert invsrc.source == 'file'
        assert invsrc.inventory_updates.count() == 1
        assert invsrc.inventory_updates.first().status == 'successful'

        # Check creation of ad-hoc inventory source - this was not called with one specified
        assert reloaded_inv.inventory_sources.count() == 1
        assert reloaded_inv.inventory_sources.all()[0].source == 'file'

    @mock.patch.object(inventory_import, 'AnsibleInventoryLoader', MockLoader)
    def test_hostvars_are_saved(self, inventory):
        inventory_import.AnsibleInventoryLoader._data = {
            "_meta": {
                "hostvars": {"foo": {"some_hostvar": "foobar"}}
            },
            "all": {
                "children": ["ungrouped"]
            },
            "ungrouped": {
                "hosts": ["foo"]
            }
        }
        cmd = inventory_import.Command()
        cmd.handle(inventory_id=inventory.pk, source=__file__)
        assert inventory.hosts.count() == 1
        h = inventory.hosts.all()[0]
        assert h.name == 'foo'
        assert h.variables_dict == {"some_hostvar": "foobar"}

    @mock.patch.object(inventory_import, 'AnsibleInventoryLoader', MockLoader)
    def test_memberships_are_respected(self, inventory):
        """This tests that if import 1 added a group-group and group-host memberhip
        that import 2 will not remove those memberships, even when adding
        importing the same parent groups
        """
        inventory_import.AnsibleInventoryLoader._data = {
            "_meta": {
                "hostvars": {"foo": {}}
            },
            "all": {
                "children": ["ungrouped", "is_a_parent", "has_a_host", "is_a_child"]
            },
            "is_a_parent": {
                "children": ["is_a_child"]
            },
            "has_a_host": {
                "hosts": ["foo"]
            },
            "ungrouped": {
                "hosts": []
            }
        }
        cmd = inventory_import.Command()
        cmd.handle(inventory_id=inventory.pk, source=__file__)
        assert inventory.hosts.count() == 1  # baseline worked

        inv_src2 = inventory.inventory_sources.create(
            name='bar', overwrite=True, source='ec2'
        )
        os.environ['INVENTORY_SOURCE_ID'] = str(inv_src2.pk)
        os.environ['INVENTORY_UPDATE_ID'] = str(inv_src2.create_unified_job().pk)
        # scenario where groups are already imported, and overwrite is true
        inv_src2.groups.add(inventory.groups.get(name='is_a_parent'))
        inv_src2.groups.add(inventory.groups.get(name='has_a_host'))

        inventory_import.AnsibleInventoryLoader._data = {
            "_meta": {
                "hostvars": {"bar": {}}
            },
            "all": {
                "children": ["ungrouped", "is_a_parent", "has_a_host"]
            },
            "ungrouped": {
                "hosts": ["bar"]
            }
        }
        cmd = inventory_import.Command()
        cmd.handle(inventory_id=inventory.pk, source=__file__, overwrite=True)

        del os.environ['INVENTORY_SOURCE_ID']
        del os.environ['INVENTORY_UPDATE_ID']

        # the overwriting import did not destroy relationships from first import
        parent_group = inventory.groups.get(name='is_a_parent')
        assert parent_group.children.count() == 1
        has_host_group = inventory.groups.get(name='has_a_host')
        assert has_host_group.hosts.count() == 1

    @mock.patch.object(inventory_import, 'AnsibleInventoryLoader', MockLoader)
    def test_recursive_group_error(self, inventory):
        inventory_import.AnsibleInventoryLoader._data = {
            "_meta": {
                "hostvars": {}
            },
            "all": {
                "children": ["fooland", "barland"]
            },
            "fooland": {
                "children": ["barland"]
            },
            "barland": {
                "children": ["fooland"]
            }
        }
        cmd = inventory_import.Command()
        cmd.handle(inventory_id=inventory.pk, source=__file__)


@pytest.mark.django_db
@pytest.mark.inventory_import
class TestEnabledVar:
    '''
    Meaning of return values
    None - import script did not give an indication of enablement
    True - host is enabled
    False - host is not enabled
    '''

    @pytest.fixture
    def cmd(self):
        cmd = inventory_import.Command()
        cmd.enabled_var = 'foo.bar'
        cmd.enabled_value = 'barfoo'
        return cmd

    def test_enabled_var_not_present(self, cmd):
        assert cmd._get_enabled({'ansible_connection': 'local'}) is None

    def test_enabled_dot_var_not_present(self, cmd):
        assert cmd._get_enabled({'foo': 'barfoo'}) is None

    def test_enabled_var_not_enabled_value(self, cmd):
        assert cmd._get_enabled({'foo': {'bar': 'foooooo'}}) is False

    def test_enabled_var_is_enabled_value(self, cmd):
        assert cmd._get_enabled({'foo': {'bar': 'barfoo'}}) is True


def test_tower_version_compare():
    cmd = inventory_import.Command()
    cmd.inventory_source = InventorySource(source='tower')
    cmd.all_group = MemGroup('all')
    # mimic example from https://github.com/ansible/ansible/pull/52747
    # until that is merged, this is the best testing we can do
    cmd.all_group.variables = {
        'tower_metadata': {
            "ansible_version": "2.7.5",
            "license_type": "open",
            "version": "2.0.1-1068-g09684e2c41"
        }
    }
    with pytest.raises(CommandError):
        cmd.remote_tower_license_compare('very_supported')
    cmd.remote_tower_license_compare('open')
