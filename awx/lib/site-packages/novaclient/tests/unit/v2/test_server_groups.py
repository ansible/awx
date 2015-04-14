# Copyright (c) 2014 VMware, Inc.
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

from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit.fixture_data import server_groups as data
from novaclient.tests.unit import utils
from novaclient.v2 import server_groups


class ServerGroupsTest(utils.FixturedTestCase):

    client_fixture_class = client.V1
    data_fixture_class = data.Fixture

    def test_list_server_groups(self):
        result = self.cs.server_groups.list()
        self.assert_called('GET', '/os-server-groups')
        for server_group in result:
            self.assertTrue(isinstance(server_group,
                                       server_groups.ServerGroup))

    def test_create_server_group(self):
        kwargs = {'name': 'ig1',
                  'policies': ['anti-affinity']}
        server_group = self.cs.server_groups.create(**kwargs)
        body = {'server_group': kwargs}
        self.assert_called('POST', '/os-server-groups', body)
        self.assertTrue(isinstance(server_group,
                                   server_groups.ServerGroup))

    def test_get_server_group(self):
        id = '2cbd51f4-fafe-4cdb-801b-cf913a6f288b'
        server_group = self.cs.server_groups.get(id)
        self.assert_called('GET', '/os-server-groups/%s' % id)
        self.assertTrue(isinstance(server_group,
                                   server_groups.ServerGroup))

    def test_delete_server_group(self):
        id = '2cbd51f4-fafe-4cdb-801b-cf913a6f288b'
        self.cs.server_groups.delete(id)
        self.assert_called('DELETE', '/os-server-groups/%s' % id)

    def test_delete_server_group_object(self):
        id = '2cbd51f4-fafe-4cdb-801b-cf913a6f288b'
        server_group = self.cs.server_groups.get(id)
        server_group.delete()
        self.assert_called('DELETE', '/os-server-groups/%s' % id)
