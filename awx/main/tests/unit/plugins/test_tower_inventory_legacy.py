import pytest
import mock

# python
import os
import sys

# AWX main
from awx.main.utils.mem_inventory import MemGroup

# Add awx/plugins to sys.path so we can use the plugin
TEST_DIR = os.path.dirname(__file__)
path = os.path.abspath(os.path.join(
    TEST_DIR, '..', '..', '..', '..', 'plugins', 'ansible_inventory'))
if path not in sys.path:
    sys.path.insert(0, path)

# AWX plugin
from legacy import IniLoader  # noqa


@pytest.fixture
def loader():
    return IniLoader(TEST_DIR, MemGroup('all'))


@pytest.mark.inventory_import
class TestHostPatterns:

    def test_simple_host_pattern(self, loader):
        assert [h.name for h in loader.get_host_names_from_entry('server[1:3].io')] == [
            'server1.io', 'server2.io', 'server3.io']

    def test_host_with_port(self, loader):
        assert [h.name for h in loader.get_host_names_from_entry('server.com:8080')] == ['server.com']
        assert [h.variables['ansible_port'] for h in loader.get_host_names_from_entry('server.com:8080')] == [8080]

    def test_host_pattern_with_step(self, loader):
        assert [h.name for h in loader.get_host_names_from_entry('server[0:10:5].io')] == [
            'server0.io', 'server5.io', 'server10.io']

    def test_invalid_host_pattern_with_step(self, loader):
        with pytest.raises(ValueError):
            print [h.name for h in loader.get_host_names_from_entry('server[00:010:5].io')]

    def test_alphanumeric_pattern(self, loader):
        assert [h.name for h in loader.get_host_names_from_entry('server[a:c].io')] == [
            'servera.io', 'serverb.io', 'serverc.io']

    def test_invalid_alphanumeric_pattern(self, loader):
        with pytest.raises(ValueError):
            print [h.name for h in loader.get_host_names_from_entry('server[c:a].io')]


@pytest.mark.inventory_import
class TestLoader:

    def test_group_and_host(self, loader):
        group_and_host = mock.MagicMock(return_value=[
            '[my_group]',
            'my_host'
        ])
        with mock.patch.object(loader, 'file_line_iterable', group_and_host):
            inventory = loader.load()
            g = inventory.all_group.children[0]
            assert g.name == 'my_group'
            assert g.hosts[0].name

    def test_host_comment(self, loader):
        group_and_host = mock.MagicMock(return_value=['my_host     # and a comment'])
        with mock.patch.object(loader, 'file_line_iterable', group_and_host):
            inventory = loader.load()
            assert inventory.all_group.hosts[0].name == 'my_host'

    def test_group_parentage(self, loader):
        group_and_host = mock.MagicMock(return_value=[
            '[my_group]     # and a comment',
            '[my_group:children]  # and a comment',
            'child_group       # and a comment'
        ])
        with mock.patch.object(loader, 'file_line_iterable', group_and_host):
            inventory = loader.load()
            g = inventory.get_group('my_group')
            assert g.name == 'my_group'
            child = g.children[0]
            assert child.name == 'child_group'
            # We can not list non-root-level groups in the all_group
            assert child not in inventory.all_group.children
