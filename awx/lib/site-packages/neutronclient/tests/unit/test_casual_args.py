# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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
#

import testtools

from neutronclient.common import exceptions
from neutronclient.neutron import v2_0 as neutronV20


class CLITestArgs(testtools.TestCase):

    def test_empty(self):
        _mydict = neutronV20.parse_args_to_dict([])
        self.assertEqual({}, _mydict)

    def test_default_bool(self):
        _specs = ['--my_bool', '--arg1', 'value1']
        _mydict = neutronV20.parse_args_to_dict(_specs)
        self.assertTrue(_mydict['my_bool'])

    def test_bool_true(self):
        _specs = ['--my-bool', 'type=bool', 'true', '--arg1', 'value1']
        _mydict = neutronV20.parse_args_to_dict(_specs)
        self.assertTrue(_mydict['my_bool'])

    def test_bool_false(self):
        _specs = ['--my_bool', 'type=bool', 'false', '--arg1', 'value1']
        _mydict = neutronV20.parse_args_to_dict(_specs)
        self.assertFalse(_mydict['my_bool'])

    def test_nargs(self):
        _specs = ['--tag', 'x', 'y', '--arg1', 'value1']
        _mydict = neutronV20.parse_args_to_dict(_specs)
        self.assertIn('x', _mydict['tag'])
        self.assertIn('y', _mydict['tag'])

    def test_badarg(self):
        _specs = ['--tag=t', 'x', 'y', '--arg1', 'value1']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)

    def test_badarg_with_minus(self):
        _specs = ['--arg1', 'value1', '-D']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)

    def test_goodarg_with_minus_number(self):
        _specs = ['--arg1', 'value1', '-1', '-1.0']
        _mydict = neutronV20.parse_args_to_dict(_specs)
        self.assertEqual(['value1', '-1', '-1.0'],
                         _mydict['arg1'])

    def test_badarg_duplicate(self):
        _specs = ['--tag=t', '--arg1', 'value1', '--arg1', 'value1']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)

    def test_badarg_early_type_specification(self):
        _specs = ['type=dict', 'key=value']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)

    def test_arg(self):
        _specs = ['--tag=t', '--arg1', 'value1']
        self.assertEqual('value1',
                         neutronV20.parse_args_to_dict(_specs)['arg1'])

    def test_dict_arg(self):
        _specs = ['--tag=t', '--arg1', 'type=dict', 'key1=value1,key2=value2']
        arg1 = neutronV20.parse_args_to_dict(_specs)['arg1']
        self.assertEqual('value1', arg1['key1'])
        self.assertEqual('value2', arg1['key2'])

    def test_dict_arg_with_attribute_named_type(self):
        _specs = ['--tag=t', '--arg1', 'type=dict', 'type=value1,key2=value2']
        arg1 = neutronV20.parse_args_to_dict(_specs)['arg1']
        self.assertEqual('value1', arg1['type'])
        self.assertEqual('value2', arg1['key2'])

    def test_list_of_dict_arg(self):
        _specs = ['--tag=t', '--arg1', 'type=dict',
                  'list=true', 'key1=value1,key2=value2']
        arg1 = neutronV20.parse_args_to_dict(_specs)['arg1']
        self.assertEqual('value1', arg1[0]['key1'])
        self.assertEqual('value2', arg1[0]['key2'])

    def test_clear_action(self):
        _specs = ['--anyarg', 'action=clear']
        args = neutronV20.parse_args_to_dict(_specs)
        self.assertIsNone(args['anyarg'])

    def test_bad_values_str(self):
        _specs = ['--strarg', 'type=str']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)

    def test_bad_values_list(self):
        _specs = ['--listarg', 'list=true', 'type=str']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)
        _specs = ['--listarg', 'type=list']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)
        _specs = ['--listarg', 'type=list', 'action=clear']
        self.assertRaises(exceptions.CommandError,
                          neutronV20.parse_args_to_dict, _specs)
