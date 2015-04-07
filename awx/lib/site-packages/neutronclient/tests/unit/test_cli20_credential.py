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

from neutronclient.neutron.v2_0 import credential
from neutronclient.tests.unit import test_cli20


class CLITestV20Credential(test_cli20.CLITestV20Base):

    def test_create_credential(self):
        """Create credential: myid."""
        resource = 'credential'
        cmd = credential.CreateCredential(test_cli20.MyApp(sys.stdout), None)
        name = 'myname'
        myid = 'myid'
        type = 'mytype'
        args = [name, type]
        position_names = ['credential_name', 'type']
        position_values = [name, type]
        self._test_create_resource(resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_credentials_detail(self):
        """List credentials: -D."""
        resources = 'credentials'
        cmd = credential.ListCredential(test_cli20.MyApp(sys.stdout), None)
        contents = [{'credential_name': 'myname', 'type': 'mytype'}]
        self._test_list_resources(resources, cmd, True,
                                  response_contents=contents)

    def test_list_credential_known_option_after_unknown(self):
        """List credential: -- --tags a b --request-format xml."""
        resources = 'credentials'
        cmd = credential.ListCredential(test_cli20.MyApp(sys.stdout), None)
        contents = [{'credential_name': 'myname', 'type': 'mytype'}]
        self._test_list_resources(resources, cmd, tags=['a', 'b'],
                                  response_contents=contents)

    def test_list_credential_fields(self):
        """List credential: --fields a --fields b -- --fields c d."""
        resources = 'credentials'
        cmd = credential.ListCredential(test_cli20.MyApp(sys.stdout), None)
        contents = [{'credential_name': 'myname', 'type': 'mytype'}]
        self._test_list_resources(resources, cmd,
                                  fields_1=['a', 'b'], fields_2=['c', 'd'],
                                  response_contents=contents)

    def test_show_credential(self):
        """Show credential: --fields id --fields name myid."""
        resource = 'credential'
        cmd = credential.ShowCredential(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(resource, cmd, self.test_id, args,
                                 ['id', 'name'])

    def test_delete_credential(self):
        """Delete credential: myid."""
        resource = 'credential'
        cmd = credential.DeleteCredential(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(resource, cmd, myid, args)
