# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Python
import pytest
import mock

# Django
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands import inventory_import
from awx.main.models import Inventory, Host, Group
from awx.main.utils.mem_inventory import dict_to_mem_data


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


TEST_MEM_OBJECTS = dict_to_mem_data(TEST_INVENTORY_CONTENT)


def mock_logging(self):
    pass


@pytest.mark.django_db
@pytest.mark.inventory_import
@mock.patch.object(inventory_import.Command, 'check_license', mock.MagicMock())
@mock.patch.object(inventory_import.Command, 'set_logging_level', mock_logging)
class TestInvalidOptionsFunctional:

    @mock.patch.object(inventory_import.InstanceGroup.objects, 'get', new=mock.MagicMock(return_value=None))
    def test_invalid_options_invalid_source(self, inventory):
        # Give invalid file to the command
        cmd = inventory_import.Command()
        with mock.patch('django.db.transaction.rollback'):
            with pytest.raises(IOError) as err:
                cmd.handle_noargs(
                    inventory_id=inventory.id,
                    source='/tmp/pytest-of-root/pytest-7/inv_files0-invalid')
        assert 'Source does not exist' in err.value.message

    def test_invalid_inventory_id(self):
        cmd = inventory_import.Command()
        with pytest.raises(CommandError) as err:
            cmd.handle_noargs(inventory_id=42, source='/notapath/shouldnotmatter')
        assert 'id = 42' in err.value.message
        assert 'cannot be found' in err.value.message

    def test_invalid_inventory_name(self):
        cmd = inventory_import.Command()
        with pytest.raises(CommandError) as err:
            cmd.handle_noargs(inventory_name='fooservers', source='/notapath/shouldnotmatter')
        assert 'name = fooservers' in err.value.message
        assert 'cannot be found' in err.value.message


@pytest.mark.django_db
@pytest.mark.inventory_import
@mock.patch.object(inventory_import.InstanceGroup.objects, 'get', new=mock.MagicMock(return_value=None))
@mock.patch.object(inventory_import.Command, 'check_license', new=mock.MagicMock())
@mock.patch.object(inventory_import.Command, 'set_logging_level', new=mock_logging)
class TestINIImports:

    @mock.patch.object(inventory_import.AnsibleInventoryLoader, 'load', mock.MagicMock(return_value=TEST_MEM_OBJECTS))
    def test_inventory_single_ini_import(self, inventory, capsys):
        cmd = inventory_import.Command()
        r = cmd.handle_noargs(
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

    @mock.patch.object(
        inventory_import, 'load_inventory_source', mock.MagicMock(
            return_value=dict_to_mem_data(
                {
                    "_meta": {
                        "hostvars": {"foo": {"some_hostvar": "foobar"}}
                    },
                    "all": {
                        "children": ["ungrouped"]
                    },
                    "ungrouped": {
                        "hosts": ["foo"]
                    }
                }).all_group
        )
    )
    def test_hostvars_are_saved(self, inventory):
        cmd = inventory_import.Command()
        cmd.handle_noargs(inventory_id=inventory.pk, source='doesnt matter')
        assert inventory.hosts.count() == 1
        h = inventory.hosts.all()[0]
        assert h.name == 'foo'
        assert h.variables_dict == {"some_hostvar": "foobar"}

    @mock.patch.object(
        inventory_import, 'load_inventory_source', mock.MagicMock(
            return_value=dict_to_mem_data(
                {
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
                }).all_group
        )
    )
    def test_recursive_group_error(self, inventory):
        cmd = inventory_import.Command()
        cmd.handle_noargs(inventory_id=inventory.pk, source='doesnt matter')
