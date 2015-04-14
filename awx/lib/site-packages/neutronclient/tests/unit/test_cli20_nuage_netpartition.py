# Copyright 2014 Alcatel-Lucent USA Inc.
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
# @author: Ronak Shah, Nuage Networks, Alcatel-Lucent USA Inc.

import sys

from neutronclient.neutron.v2_0 import netpartition
from neutronclient.tests.unit import test_cli20


class CLITestV20NetPartitionJSON(test_cli20.CLITestV20Base):
    resource = 'net_partition'

    def test_create_netpartition(self):
        cmd = netpartition.CreateNetPartition(test_cli20.MyApp(sys.stdout),
                                              None)
        name = 'myname'
        myid = 'myid'
        args = [name, ]
        position_names = ['name', ]
        position_values = [name, ]
        self._test_create_resource(self.resource, cmd, name, myid, args,
                                   position_names, position_values)

    def test_list_netpartitions(self):
        resources = '%ss' % self.resource
        cmd = netpartition.ListNetPartition(test_cli20.MyApp(sys.stdout),
                                            None)
        self._test_list_resources(resources, cmd, True)

    def test_show_netpartition(self):
        cmd = netpartition.ShowNetPartition(test_cli20.MyApp(sys.stdout),
                                            None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self.resource, cmd, self.test_id, args,
                                 ['id', 'name'])

    def test_delete_netpartition(self):
        cmd = netpartition.DeleteNetPartition(test_cli20.MyApp(sys.stdout),
                                              None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(self.resource, cmd, myid, args)


class CLITestV20NetPartitionXML(CLITestV20NetPartitionJSON):
    format = 'xml'
