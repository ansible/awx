# Copyright (c) 2011 OpenStack Foundation
# All Rights Reserved.
#
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

import collections
import json
import optparse
import sys

import mock
import testtools

from troveclient.compat import common

"""
 unit tests for common.py
"""


class CommonTest(testtools.TestCase):

    def setUp(self):
        super(CommonTest, self).setUp()
        self.orig_sys_exit = sys.exit
        sys.exit = mock.Mock(return_value=None)

    def tearDown(self):
        super(CommonTest, self).tearDown()
        sys.exit = self.orig_sys_exit

    def test_methods_of(self):
        class DummyClass:
            def dummyMethod(self):
                print("just for test")

        obj = DummyClass()
        result = common.methods_of(obj)
        self.assertEqual(1, len(result))
        method = result['dummyMethod']
        self.assertIsNotNone(method)

    def test_check_for_exceptions(self):
        status = [400, 422, 500]
        for s in status:
            resp = mock.Mock()
            # compat still uses status
            resp.status = s
            self.assertRaises(Exception,
                              common.check_for_exceptions, resp, "body")

        # a no-exception case
        resp = mock.Mock()
        resp.status_code = 200
        common.check_for_exceptions(resp, "body")

    def test_print_actions(self):
        cmd = "test-cmd"
        actions = {"test": "test action", "help": "help action"}
        common.print_actions(cmd, actions)
        pass

    def test_print_commands(self):
        commands = {"cmd-1": "cmd 1", "cmd-2": "cmd 2"}
        common.print_commands(commands)
        pass

    def test_limit_url(self):
        url = "test-url"
        limit = None
        marker = None
        self.assertEqual(url, common.limit_url(url))

        limit = "test-limit"
        marker = "test-marker"
        expected = "test-url?marker=test-marker&limit=test-limit"
        self.assertEqual(expected,
                         common.limit_url(url, limit=limit, marker=marker))


class CliOptionsTest(testtools.TestCase):

    def check_default_options(self, co):
        self.assertIsNone(co.username)
        self.assertIsNone(co.apikey)
        self.assertIsNone(co.tenant_id)
        self.assertIsNone(co.auth_url)
        self.assertEqual('keystone', co.auth_type)
        self.assertEqual('database', co.service_type)
        self.assertEqual('RegionOne', co.region)
        self.assertIsNone(co.service_url)
        self.assertFalse(co.insecure)
        self.assertFalse(co.verbose)
        self.assertFalse(co.debug)
        self.assertIsNone(co.token)

    def check_option(self, oparser, option_name):
        option = oparser.get_option("--%s" % option_name)
        self.assertNotEqual(None, option)
        if option_name in common.CliOptions.DEFAULT_VALUES:
            self.assertEqual(common.CliOptions.DEFAULT_VALUES[option_name],
                             option.default)

    def test___init__(self):
        co = common.CliOptions()
        self.check_default_options(co)

    def test_deafult(self):
        co = common.CliOptions.default()
        self.check_default_options(co)

    def test_load_from_file(self):
        co = common.CliOptions.load_from_file()
        self.check_default_options(co)

    def test_create_optparser(self):
        option_names = ["verbose", "debug", "auth_url", "username", "apikey",
                        "tenant_id", "auth_type", "service_type",
                        "service_name", "service_type", "service_name",
                        "service_url", "region", "insecure", "token",
                        "secure", "json", "terse", "hide-debug"]

        oparser = common.CliOptions.create_optparser(True)
        for option_name in option_names:
            self.check_option(oparser, option_name)

        oparser = common.CliOptions.create_optparser(False)
        for option_name in option_names:
            self.check_option(oparser, option_name)


class ArgumentRequiredTest(testtools.TestCase):

    def setUp(self):
        super(ArgumentRequiredTest, self).setUp()
        self.param = "test-param"
        self.arg_req = common.ArgumentRequired(self.param)

    def test___init__(self):
        self.assertEqual(self.param, self.arg_req.param)

    def test___str__(self):
        expected = 'Argument "--%s" required.' % self.param
        self.assertEqual(expected, self.arg_req.__str__())


class CommandsBaseTest(testtools.TestCase):

    def setUp(self):
        super(CommandsBaseTest, self).setUp()
        self.orig_sys_exit = sys.exit
        sys.exit = mock.Mock(return_value=None)
        self.orig_sys_argv = sys.argv
        sys.argv = ['fakecmd']
        parser = common.CliOptions().create_optparser(False)
        self.cmd_base = common.CommandsBase(parser)

    def tearDown(self):
        super(CommandsBaseTest, self).tearDown()
        sys.exit = self.orig_sys_exit
        sys.argv = self.orig_sys_argv

    def test___init__(self):
        self.assertNotEqual(None, self.cmd_base)

    def test__safe_exec(self):
        func = mock.Mock(return_value="test")
        self.cmd_base.debug = True
        r = self.cmd_base._safe_exec(func)
        self.assertEqual("test", r)

        self.cmd_base.debug = False
        r = self.cmd_base._safe_exec(func)
        self.assertEqual("test", r)

        func = mock.Mock(side_effect=ValueError)  # an arbitrary exception
        r = self.cmd_base._safe_exec(func)
        self.assertIsNone(r)

    def test__prepare_parser(self):
        parser = optparse.OptionParser()
        common.CommandsBase.params = ["test_1", "test_2"]
        self.cmd_base._prepare_parser(parser)
        option = parser.get_option("--%s" % "test_1")
        self.assertNotEqual(None, option)
        option = parser.get_option("--%s" % "test_2")
        self.assertNotEqual(None, option)

    def test__parse_options(self):
        parser = optparse.OptionParser()
        parser.add_option("--%s" % "test_1", default="test_1v")
        parser.add_option("--%s" % "test_2", default="test_2v")
        self.cmd_base._parse_options(parser)
        self.assertEqual("test_1v", self.cmd_base.test_1)
        self.assertEqual("test_2v", self.cmd_base.test_2)

    def test__require(self):
        self.assertRaises(common.ArgumentRequired,
                          self.cmd_base._require, "attr_1")
        self.cmd_base.attr_1 = None
        self.assertRaises(common.ArgumentRequired,
                          self.cmd_base._require, "attr_1")
        self.cmd_base.attr_1 = "attr_v1"
        self.cmd_base._require("attr_1")

    def test__make_list(self):
        self.assertRaises(AttributeError, self.cmd_base._make_list, "attr1")
        self.cmd_base.attr1 = "v1,v2"
        self.cmd_base._make_list("attr1")
        self.assertEqual(["v1", "v2"], self.cmd_base.attr1)
        self.cmd_base.attr1 = ["v3"]
        self.cmd_base._make_list("attr1")
        self.assertEqual(["v3"], self.cmd_base.attr1)

    def test__pretty_print(self):
        func = mock.Mock(return_value=None)
        self.cmd_base.verbose = True
        self.assertIsNone(self.cmd_base._pretty_print(func))
        self.cmd_base.verbose = False
        self.assertIsNone(self.cmd_base._pretty_print(func))

    def test__dumps(self):
        orig_dumps = json.dumps
        json.dumps = mock.Mock(return_value="test-dump")
        self.assertEqual("test-dump", self.cmd_base._dumps("item"))
        json.dumps = orig_dumps

    def test__pretty_list(self):
        func = mock.Mock(return_value=None)
        self.cmd_base.verbose = True
        self.assertIsNone(self.cmd_base._pretty_list(func))
        self.cmd_base.verbose = False
        self.assertIsNone(self.cmd_base._pretty_list(func))
        item = mock.Mock(return_value="test")
        item._info = "info"
        func = mock.Mock(return_value=[item])
        self.assertIsNone(self.cmd_base._pretty_list(func))

    def test__pretty_paged(self):
        self.cmd_base.limit = "5"
        func = mock.Mock(return_value=None)
        self.cmd_base.verbose = True
        self.assertIsNone(self.cmd_base._pretty_paged(func))

        self.cmd_base.verbose = False

        class MockIterable(collections.Iterable):
            links = ["item"]
            count = 1

            def __iter__(self):
                return ["item1"]

            def __len__(self):
                return self.count

        ret = MockIterable()
        func = mock.Mock(return_value=ret)
        self.assertIsNone(self.cmd_base._pretty_paged(func))

        ret.count = 0
        self.assertIsNone(self.cmd_base._pretty_paged(func))

        func = mock.Mock(side_effect=ValueError)
        self.assertIsNone(self.cmd_base._pretty_paged(func))
        self.cmd_base.debug = True
        self.cmd_base.marker = mock.Mock()
        self.assertRaises(ValueError, self.cmd_base._pretty_paged, func)


class AuthTest(testtools.TestCase):

    def setUp(self):
        super(AuthTest, self).setUp()
        self.orig_sys_exit = sys.exit
        sys.exit = mock.Mock(return_value=None)
        self.orig_sys_argv = sys.argv
        sys.argv = ['fakecmd']
        self.parser = common.CliOptions().create_optparser(False)
        self.auth = common.Auth(self.parser)

    def tearDown(self):
        super(AuthTest, self).tearDown()
        sys.exit = self.orig_sys_exit
        sys.argv = self.orig_sys_argv

    def test___init__(self):
        self.assertIsNone(self.auth.dbaas)
        self.assertIsNone(self.auth.apikey)

    def test_login(self):
        self.auth.username = "username"
        self.auth.apikey = "apikey"
        self.auth.tenant_id = "tenant_id"
        self.auth.auth_url = "auth_url"
        dbaas = mock.Mock()
        dbaas.authenticate = mock.Mock(return_value=None)
        dbaas.client = mock.Mock()
        dbaas.client.auth_token = mock.Mock()
        dbaas.client.service_url = mock.Mock()
        self.auth._get_client = mock.Mock(return_value=dbaas)
        self.auth.login()

        self.auth.debug = True
        self.auth._get_client = mock.Mock(side_effect=ValueError)
        self.assertRaises(ValueError, self.auth.login)

        self.auth.debug = False
        self.auth.login()


class AuthedCommandsBaseTest(testtools.TestCase):

    def setUp(self):
        super(AuthedCommandsBaseTest, self).setUp()
        self.orig_sys_exit = sys.exit
        sys.exit = mock.Mock(return_value=None)
        self.orig_sys_argv = sys.argv
        sys.argv = ['fakecmd']

    def tearDown(self):
        super(AuthedCommandsBaseTest, self).tearDown()
        sys.exit = self.orig_sys_exit
        self.orig_sys_argv = sys.argv

    def test___init__(self):
        parser = common.CliOptions().create_optparser(False)
        common.AuthedCommandsBase.debug = True
        dbaas = mock.Mock()
        dbaas.authenticate = mock.Mock(return_value=None)
        dbaas.client = mock.Mock()
        dbaas.client.auth_token = mock.Mock()
        dbaas.client.service_url = mock.Mock()
        dbaas.client.authenticate_with_token = mock.Mock()
        common.AuthedCommandsBase._get_client = mock.Mock(return_value=dbaas)
        common.AuthedCommandsBase(parser)


class PaginatedTest(testtools.TestCase):

    def setUp(self):
        super(PaginatedTest, self).setUp()
        self.items_ = ["item1", "item2"]
        self.next_marker_ = "next-marker"
        self.links_ = ["link1", "link2"]
        self.pgn = common.Paginated(self.items_, self.next_marker_,
                                    self.links_)

    def tearDown(self):
        super(PaginatedTest, self).tearDown()

    def test___init__(self):
        self.assertEqual(self.items_, self.pgn.items)
        self.assertEqual(self.next_marker_, self.pgn.next)
        self.assertEqual(self.links_, self.pgn.links)

    def test___len__(self):
        self.assertEqual(len(self.items_), self.pgn.__len__())

    def test___iter__(self):
        itr_expected = self.items_.__iter__()
        itr = self.pgn.__iter__()
        self.assertEqual(next(itr_expected), next(itr))
        self.assertEqual(next(itr_expected), next(itr))
        self.assertRaises(StopIteration, next, itr_expected)
        self.assertRaises(StopIteration, next, itr)

    def test___getitem__(self):
        self.assertEqual(self.items_[0], self.pgn.__getitem__(0))

    def test___setitem__(self):
        self.pgn.__setitem__(0, "new-item")
        self.assertEqual("new-item", self.pgn.items[0])

    def test___delitem(self):
        del self.pgn[0]
        self.assertEqual(1, self.pgn.__len__())

    def test___reversed__(self):
        itr = self.pgn.__reversed__()
        self.assertEqual("item2", next(itr))
        self.assertEqual("item1", next(itr))
        self.assertRaises(StopIteration, next, itr)

    def test___contains__(self):
        self.assertTrue(self.pgn.__contains__("item1"))
        self.assertTrue(self.pgn.__contains__("item2"))
        self.assertFalse(self.pgn.__contains__("item3"))
