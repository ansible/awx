# Copyright 2012 OpenStack Foundation
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

from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import hypervisors as data
from novaclient.tests.v1_1 import test_hypervisors


class HypervisorsTest(test_hypervisors.HypervisorsTest):

    client_fixture_class = client.V3
    data_fixture_class = data.V3

    def test_hypervisor_search(self):
        expected = [
            dict(id=1234, hypervisor_hostname='hyper1'),
            dict(id=5678, hypervisor_hostname='hyper2'),
            ]

        result = self.cs.hypervisors.search('hyper')
        self.assert_called('GET', '/os-hypervisors/search?query=hyper')

        for idx, hyper in enumerate(result):
            self.compare_to_expected(expected[idx], hyper)

    def test_hypervisor_servers(self):
        expected = dict(id=1234,
                        hypervisor_hostname='hyper1',
                        servers=[
                            dict(name='inst1', id='uuid1'),
                            dict(name='inst2', id='uuid2')])

        result = self.cs.hypervisors.servers('1234')
        self.assert_called('GET', '/os-hypervisors/1234/servers')

        self.compare_to_expected(expected, result)
