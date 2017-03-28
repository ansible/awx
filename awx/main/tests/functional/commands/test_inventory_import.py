# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Python
import pytest
import mock

# Django
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands.inventory_import import (
    Command
)
from awx.main.models import Inventory, Host, Group


TEST_INVENTORY_INI = '''\
# Some comment about blah blah blah...

[webservers]
web1.example.com ansible_ssh_host=w1.example.net
web2.example.com
web3.example.com:1022

[webservers:vars]   # Comment on a section
webvar=blah         # Comment on an option

[dbservers]
db1.example.com
db2.example.com

[dbservers:vars]
dbvar=ugh

[servers:children]
webservers
dbservers

[servers:vars]
varb=B

[all:vars]
vara=A

[others]
10.11.12.13
10.12.14.16:8022
fe80::1610:9fff:fedd:654b
[fe80::1610:9fff:fedd:b654]:1022
::1
'''


@pytest.fixture(scope='session')
def test_dir(tmpdir_factory):
    return tmpdir_factory.mktemp('inv_files', numbered=False)


@pytest.fixture(scope='session')
def ini_file(test_dir):
    fn = test_dir.join('test_hosts')
    fn.write(TEST_INVENTORY_INI)
    return fn


@pytest.mark.django_db
@mock.patch.object(Command, 'check_license', mock.MagicMock())
class TestInvalidOptionsFunctional:

    def test_invalid_options_invalid_source(self, inventory):
        # Give invalid file to the command
        cmd = Command()
        with mock.patch('django.db.transaction.rollback'):
            with pytest.raises(IOError) as err:
                cmd.handle_noargs(
                    inventory_id=inventory.id,
                    source='/tmp/pytest-of-root/pytest-7/inv_files0-invalid')
        assert 'Source does not exist' in err.value.message

    def test_invalid_inventory_id(self, ini_file):
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle_noargs(inventory_id=42, source=ini_file.dirname)
        assert 'id = 42' in err.value.message
        assert 'cannot be found' in err.value.message

    def test_invalid_inventory_name(self, ini_file):
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle_noargs(inventory_name='fooservers', source=ini_file.dirname)
        assert 'name = fooservers' in err.value.message
        assert 'cannot be found' in err.value.message


@pytest.mark.django_db
@mock.patch.object(Command, 'check_license', mock.MagicMock())
class TestINIImports:

    def test_inventory_single_ini_import(self, inventory, ini_file, capsys):
        cmd = Command()
        r = cmd.handle_noargs(inventory_id=inventory.pk, source=ini_file.dirname)
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

        assert Host.objects.get(name='web1.example.com').variables_dict == {'ansible_ssh_host': 'w1.example.net'}
        assert Host.objects.get(name='web3.example.com').variables_dict == {'ansible_ssh_port': 1022}
        assert Host.objects.get(name='fe80::1610:9fff:fedd:b654').variables_dict == {'ansible_ssh_port': 1022}
        assert Host.objects.get(name='10.12.14.16').variables_dict == {'ansible_ssh_port': 8022}

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

    def test_inventory_import_group_vars_file(self, inventory, ini_file, tmpdir_factory):
        # Create an extra group_vars file for group webservers
        gvarf = tmpdir_factory.mktemp('inv_files/group_vars', numbered=False).join('webservers')
        gvarf.write('''webservers_only_variable: foobar\n''')

        cmd = Command()
        cmd.handle_noargs(inventory_id=inventory.pk, source=ini_file.dirname)

        servers = Group.objects.get(name='webservers')
        assert servers.variables_dict == {'webvar': 'blah', 'webservers_only_variable': 'foobar'}

    def test_inventory_import_host_vars_file(self, inventory, ini_file, tmpdir_factory):
        # Create an extra host_vars file for one specific host
        gvarf = tmpdir_factory.mktemp('inv_files/host_vars', numbered=False).join('web1.example.com')
        gvarf.write('''host_only_variable: foobar\n''')

        cmd = Command()
        cmd.handle_noargs(inventory_id=inventory.pk, source=ini_file.dirname)

        Host.objects.get(name='web1.example.com').variables_dict == {
            'ansible_ssh_host': 'w1.example.net', 'host_only_variable': 'foobar'}
