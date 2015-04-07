# Copyright 2013 Cisco Systems Inc.
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
# @author: Kyle Mestery, Cisco Systems, Inc.
#

import sys

from neutronclient.neutron.v2_0 import policyprofile
from neutronclient.tests.unit import test_cli20


class CLITestV20PolicyProfile(test_cli20.CLITestV20Base):

    def test_list_policyprofile_detail(self):
        """List policyprofile: -D."""
        resources = 'policy_profiles'
        cmd = policyprofile.ListPolicyProfile(test_cli20.MyApp(sys.stdout),
                                              None)
        contents = [{'name': 'myname', 'segment_type': 'vlan'}]
        self._test_list_resources(resources, cmd, True,
                                  response_contents=contents)

    def test_list_policyprofile_known_option_after_unknown(self):
        """List policyprofile: -- --tags a b --request-format xml."""
        resources = 'policy_profiles'
        cmd = policyprofile.ListPolicyProfile(test_cli20.MyApp(sys.stdout),
                                              None)
        contents = [{'name': 'myname', 'segment_type': 'vlan'}]
        self._test_list_resources(resources, cmd, tags=['a', 'b'],
                                  response_contents=contents)

    def test_list_policyprofile_fields(self):
        """List policyprofile: --fields a --fields b -- --fields c d."""
        resources = 'policy_profiles'
        cmd = policyprofile.ListPolicyProfile(test_cli20.MyApp(sys.stdout),
                                              None)
        contents = [{'name': 'myname', 'segment_type': 'vlan'}]
        self._test_list_resources(resources, cmd,
                                  fields_1=['a', 'b'], fields_2=['c', 'd'],
                                  response_contents=contents)

    def test_show_policyprofile(self):
        """Show policyprofile: --fields id --fields name myid."""
        resource = 'policy_profile'
        cmd = policyprofile.ShowPolicyProfile(test_cli20.MyApp(sys.stdout),
                                              None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args,
                                 ['id', 'name'])

    def test_update_policyprofile(self):
        """Update policyprofile: myid --name myname --tags a b."""
        resource = 'policy_profile'
        cmd = policyprofile.UpdatePolicyProfile(test_cli20.MyApp(sys.stdout),
                                                None)
        self._test_update_resource(resource, cmd, 'myid',
                                   ['myid', '--name', 'myname',
                                    '--tags', 'a', 'b'],
                                   {'name': 'myname', 'tags': ['a', 'b'], }
                                   )
