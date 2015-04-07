#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import sys

import six
import testresources
from testtools import matchers

from keystoneclient import exceptions
from keystoneclient.tests.unit import client_fixtures
from keystoneclient.tests.unit import utils as test_utils
from keystoneclient import utils


class FakeResource(object):
    pass


class FakeManager(object):

    resource_class = FakeResource

    resources = {
        '1234': {'name': 'entity_one'},
        '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0': {'name': 'entity_two'},
        '\xe3\x82\xbdtest': {'name': u'\u30bdtest'},
        '5678': {'name': '9876'}
    }

    def get(self, resource_id):
        try:
            return self.resources[str(resource_id)]
        except KeyError:
            raise exceptions.NotFound(resource_id)

    def find(self, name=None):
        if name == '9999':
            # NOTE(morganfainberg): special case that raises NoUniqueMatch.
            raise exceptions.NoUniqueMatch()
        for resource_id, resource in self.resources.items():
            if resource['name'] == str(name):
                return resource
        raise exceptions.NotFound(name)


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        super(FindResourceTestCase, self).setUp()
        self.manager = FakeManager()

    def test_find_none(self):
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          'asdf')

    def test_find_by_integer_id(self):
        output = utils.find_resource(self.manager, 1234)
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_str_id(self):
        output = utils.find_resource(self.manager, '1234')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_uuid(self):
        uuid = '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0'
        output = utils.find_resource(self.manager, uuid)
        self.assertEqual(output, self.manager.resources[uuid])

    def test_find_by_unicode(self):
        name = '\xe3\x82\xbdtest'
        output = utils.find_resource(self.manager, name)
        self.assertEqual(output, self.manager.resources[name])

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_int_name(self):
        output = utils.find_resource(self.manager, 9876)
        self.assertEqual(output, self.manager.resources['5678'])

    def test_find_no_unique_match(self):
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          9999)


class FakeObject(object):
    def __init__(self, name):
        self.name = name


class PrintTestCase(test_utils.TestCase):
    def setUp(self):
        super(PrintTestCase, self).setUp()
        self.old_stdout = sys.stdout
        self.stdout = six.moves.cStringIO()
        self.addCleanup(setattr, self, 'stdout', None)
        sys.stdout = self.stdout
        self.addCleanup(setattr, sys, 'stdout', self.old_stdout)

    def test_print_list_unicode(self):
        name = six.u('\u540d\u5b57')
        objs = [FakeObject(name)]
        # NOTE(Jeffrey4l) If the text's encode is proper, this method will not
        # raise UnicodeEncodeError exceptions
        utils.print_list(objs, ['name'])
        output = self.stdout.getvalue()
        # In Python 2, output will be bytes, while in Python 3, it will not.
        # Let's decode the value if needed.
        if isinstance(output, six.binary_type):
            output = output.decode('utf-8')
        self.assertIn(name, output)

    def test_print_dict_unicode(self):
        name = six.u('\u540d\u5b57')
        utils.print_dict({'name': name})
        output = self.stdout.getvalue()
        # In Python 2, output will be bytes, while in Python 3, it will not.
        # Let's decode the value if needed.
        if isinstance(output, six.binary_type):
            output = output.decode('utf-8')
        self.assertIn(name, output)


class TestPositional(test_utils.TestCase):

    @utils.positional(1)
    def no_vars(self):
        # positional doesn't enforce anything here
        return True

    @utils.positional(3, utils.positional.EXCEPT)
    def mixed_except(self, arg, kwarg1=None, kwarg2=None):
        # self, arg, and kwarg1 may be passed positionally
        return (arg, kwarg1, kwarg2)

    @utils.positional(3, utils.positional.WARN)
    def mixed_warn(self, arg, kwarg1=None, kwarg2=None):
        # self, arg, and kwarg1 may be passed positionally, only a warning
        # is emitted
        return (arg, kwarg1, kwarg2)

    def test_nothing(self):
        self.assertTrue(self.no_vars())

    def test_mixed_except(self):
        self.assertEqual((1, 2, 3), self.mixed_except(1, 2, kwarg2=3))
        self.assertEqual((1, 2, 3), self.mixed_except(1, kwarg1=2, kwarg2=3))
        self.assertEqual((1, None, None), self.mixed_except(1))
        self.assertRaises(TypeError, self.mixed_except, 1, 2, 3)

    def test_mixed_warn(self):
        logger_message = six.moves.cStringIO()
        handler = logging.StreamHandler(logger_message)
        handler.setLevel(logging.DEBUG)

        logger = logging.getLogger(utils.__name__)
        level = logger.getEffectiveLevel()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        self.addCleanup(logger.removeHandler, handler)
        self.addCleanup(logger.setLevel, level)

        self.mixed_warn(1, 2, 3)

        self.assertIn('takes at most 3 positional', logger_message.getvalue())

    @utils.positional(enforcement=utils.positional.EXCEPT)
    def inspect_func(self, arg, kwarg=None):
        return (arg, kwarg)

    def test_inspect_positions(self):
        self.assertEqual((1, None), self.inspect_func(1))
        self.assertEqual((1, 2), self.inspect_func(1, kwarg=2))
        self.assertRaises(TypeError, self.inspect_func)
        self.assertRaises(TypeError, self.inspect_func, 1, 2)

    @utils.positional.classmethod(1)
    def class_method(cls, a, b):
        return (cls, a, b)

    @utils.positional.method(1)
    def normal_method(self, a, b):
        self.assertIsInstance(self, TestPositional)
        return (self, a, b)

    def test_class_method(self):
        self.assertEqual((TestPositional, 1, 2), self.class_method(1, b=2))
        self.assertRaises(TypeError, self.class_method, 1, 2)

    def test_normal_method(self):
        self.assertEqual((self, 1, 2), self.normal_method(1, b=2))
        self.assertRaises(TypeError, self.normal_method, 1, 2)


class HashSignedTokenTestCase(test_utils.TestCase,
                              testresources.ResourcedTestCase):
    """Unit tests for utils.hash_signed_token()."""

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_default_md5(self):
        """The default hash method is md5."""
        token = self.examples.SIGNED_TOKEN_SCOPED
        if six.PY3:
            token = token.encode('utf-8')
        token_id_default = utils.hash_signed_token(token)
        token_id_md5 = utils.hash_signed_token(token, mode='md5')
        self.assertThat(token_id_default, matchers.Equals(token_id_md5))
        # md5 hash is 32 chars.
        self.assertThat(token_id_default, matchers.HasLength(32))

    def test_sha256(self):
        """Can also hash with sha256."""
        token = self.examples.SIGNED_TOKEN_SCOPED
        if six.PY3:
            token = token.encode('utf-8')
        token_id = utils.hash_signed_token(token, mode='sha256')
        # sha256 hash is 64 chars.
        self.assertThat(token_id, matchers.HasLength(64))


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
