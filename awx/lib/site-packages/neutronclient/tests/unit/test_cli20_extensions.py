# Copyright 2013 NEC Corporation
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

import sys

from neutronclient.neutron.v2_0.extension import ListExt
from neutronclient.neutron.v2_0.extension import ShowExt
from neutronclient.tests.unit.test_cli20 import CLITestV20Base
from neutronclient.tests.unit.test_cli20 import MyApp


class CLITestV20Extension(CLITestV20Base):
    id_field = 'alias'

    def test_list_extensions(self):
        resources = 'extensions'
        cmd = ListExt(MyApp(sys.stdout), None)
        contents = [{'alias': 'ext1', 'name': 'name1', 'other': 'other1'},
                    {'alias': 'ext2', 'name': 'name2', 'other': 'other2'}]
        ret = self._test_list_resources(resources, cmd,
                                        response_contents=contents)
        ret_words = set(ret.split())
        # Check only the default columns are shown.
        self.assertIn('name', ret_words)
        self.assertIn('alias', ret_words)
        self.assertNotIn('other', ret_words)

    def test_show_extension(self):
        # -F option does not work for ext-show at the moment, so -F option
        # is not passed in the commandline args as other tests do.
        resource = 'extension'
        cmd = ShowExt(MyApp(sys.stdout), None)
        args = [self.test_id]
        ext_alias = self.test_id
        self._test_show_resource(resource, cmd, ext_alias, args, fields=[])
