import sys

import mock
import six

from novaclient import exceptions
from novaclient import utils
from novaclient import base
from novaclient.tests import utils as test_utils

UUID = '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0'


class FakeResource(object):
    NAME_ATTR = 'name'

    def __init__(self, _id, properties):
        self.id = _id
        try:
            self.name = properties['name']
        except KeyError:
            pass


class FakeManager(base.ManagerWithFind):

    resource_class = FakeResource

    resources = [
        FakeResource('1234', {'name': 'entity_one'}),
        FakeResource(UUID, {'name': 'entity_two'}),
        FakeResource('5678', {'name': '9876'})
    ]

    def get(self, resource_id):
        for resource in self.resources:
            if resource.id == str(resource_id):
                return resource
        raise exceptions.NotFound(resource_id)

    def list(self):
        return self.resources


class FakeDisplayResource(object):
    NAME_ATTR = 'display_name'

    def __init__(self, _id, properties):
        self.id = _id
        try:
            self.display_name = properties['display_name']
        except KeyError:
            pass


class FakeDisplayManager(FakeManager):

    resource_class = FakeDisplayResource

    resources = [
        FakeDisplayResource('4242', {'display_name': 'entity_three'}),
    ]


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        super(FindResourceTestCase, self).setUp()
        self.manager = FakeManager(None)

    def test_find_none(self):
        """Test a few non-valid inputs."""
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          'asdf')
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          None)
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          {})

    def test_find_by_integer_id(self):
        output = utils.find_resource(self.manager, 1234)
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_str_id(self):
        output = utils.find_resource(self.manager, '1234')
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_uuid(self):
        output = utils.find_resource(self.manager, UUID)
        self.assertEqual(output, self.manager.get(UUID))

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.get('1234'))

    def test_find_by_str_displayname(self):
        display_manager = FakeDisplayManager(None)
        output = utils.find_resource(display_manager, 'entity_three')
        self.assertEqual(output, display_manager.get('4242'))


class _FakeResult(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class PrintResultTestCase(test_utils.TestCase):
    @mock.patch('sys.stdout', six.StringIO())
    def test_print_list_sort_by_str(self):
        objs = [_FakeResult("k1", 1),
                _FakeResult("k3", 2),
                _FakeResult("k2", 3)]

        utils.print_list(objs, ["Name", "Value"], sortby_index=0)

        self.assertEqual(sys.stdout.getvalue(),
                         '+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k1   | 1     |\n'
                         '| k2   | 3     |\n'
                         '| k3   | 2     |\n'
                         '+------+-------+\n')

    @mock.patch('sys.stdout', six.StringIO())
    def test_print_list_sort_by_integer(self):
        objs = [_FakeResult("k1", 1),
                _FakeResult("k3", 2),
                _FakeResult("k2", 3)]

        utils.print_list(objs, ["Name", "Value"], sortby_index=1)

        self.assertEqual(sys.stdout.getvalue(),
                         '+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k1   | 1     |\n'
                         '| k3   | 2     |\n'
                         '| k2   | 3     |\n'
                         '+------+-------+\n')

    # without sorting
    @mock.patch('sys.stdout', six.StringIO())
    def test_print_list_sort_by_none(self):
        objs = [_FakeResult("k1", 1),
                _FakeResult("k3", 3),
                _FakeResult("k2", 2)]

        utils.print_list(objs, ["Name", "Value"], sortby_index=None)

        self.assertEqual(sys.stdout.getvalue(),
                         '+------+-------+\n'
                         '| Name | Value |\n'
                         '+------+-------+\n'
                         '| k1   | 1     |\n'
                         '| k3   | 3     |\n'
                         '| k2   | 2     |\n'
                         '+------+-------+\n')
