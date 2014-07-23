# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import unittest
from libcloud.utils.py3 import httplib

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.common.types import InvalidCredsError
from libcloud.compute.drivers.gridspot import GridspotNodeDriver
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.secrets import GRIDSPOT_PARAMS


class GridspotTest(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        GridspotNodeDriver.connectionCls.conn_classes = (
            None,
            GridspotMockHttp
        )
        GridspotMockHttp.type = None
        self.driver = GridspotNodeDriver(*GRIDSPOT_PARAMS)

    def test_invalid_creds(self):
        """
        Tests the error-handling for passing a bad API Key to the Gridspot API
        """
        GridspotMockHttp.type = 'BAD_AUTH'
        try:
            self.driver.list_nodes()
            # Above command should have thrown an InvalidCredsException
            self.assertTrue(False)
        except InvalidCredsError:
            self.assertTrue(True)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)

        running_node = nodes[0]
        starting_node = nodes[1]

        self.assertEqual(running_node.id, 'inst_CP2WrQi2WIS4iheyAVkQYw')
        self.assertEqual(running_node.state, NodeState.RUNNING)
        self.assertTrue('69.4.239.74' in running_node.public_ips)
        self.assertEqual(running_node.extra['port'], 62394)
        self.assertEqual(running_node.extra['vm_ram'], 1429436743)
        self.assertEqual(running_node.extra['start_state_time'], 1342108905)
        self.assertEqual(running_node.extra['vm_num_logical_cores'], 8)
        self.assertEqual(running_node.extra['vm_num_physical_cores'], 4)
        self.assertEqual(running_node.extra['winning_bid_id'],
                         'bid_X5xhotGYiGUk7_RmIqVafA')
        self.assertFalse('ended_state_time' in running_node.extra)
        self.assertEqual(running_node.extra['running_state_time'], 1342108989)

        self.assertEqual(starting_node.id, 'inst_CP2WrQi2WIS4iheyAVkQYw2')
        self.assertEqual(starting_node.state, NodeState.PENDING)
        self.assertTrue('69.4.239.74' in starting_node.public_ips)
        self.assertEqual(starting_node.extra['port'], 62395)
        self.assertEqual(starting_node.extra['vm_ram'], 1429436744)
        self.assertEqual(starting_node.extra['start_state_time'], 1342108906)
        self.assertEqual(starting_node.extra['vm_num_logical_cores'], 7)
        self.assertEqual(starting_node.extra['vm_num_physical_cores'], 5)
        self.assertEqual(starting_node.extra['winning_bid_id'],
                         'bid_X5xhotGYiGUk7_RmIqVafA1')
        self.assertFalse('ended_state_time' in starting_node.extra)
        self.assertEqual(starting_node.extra['running_state_time'], 1342108990)

    def test_create_node(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_destroy_node(self):
        """
        Test destroy_node for Gridspot driver
        """
        node = self.driver.list_nodes()[0]
        self.assertTrue(self.driver.destroy_node(node))

    def test_destroy_node_failure(self):
        """
        Gridspot does not fail a destroy node unless the parameters are bad, in
        which case it 404s
        """
        self.assertTrue(True)

    def test_reboot_node(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_reboot_node_failure(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_resize_node(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_reboot_node_response(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_list_images_response(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_create_node_response(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_destroy_node_response(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_list_sizes_response(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_resize_node_failure(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_list_images(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_list_sizes(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_list_locations(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)

    def test_list_locations_response(self):
        """
        Gridspot does not implement this functionality
        """
        self.assertTrue(True)


class GridspotMockHttp(MockHttp):

    def _compute_api_v1_list_instances_BAD_AUTH(self, method, url, body,
                                                headers):
        return (httplib.NOT_FOUND, "", {},
                httplib.responses[httplib.NOT_FOUND])

    def _compute_api_v1_list_instances(self, method, url, body, headers):
        body = json.dumps({
            "instances": [
                {
                    "instance_id": "inst_CP2WrQi2WIS4iheyAVkQYw",
                    "vm_num_logical_cores": 8,
                    "vm_num_physical_cores": 4,
                    "winning_bid_id": "bid_X5xhotGYiGUk7_RmIqVafA",
                    "vm_ram": 1429436743,
                    "start_state_time": 1342108905,
                    "vm_ssh_wan_ip_endpoint": "69.4.239.74:62394",
                    "current_state": "Running",
                    "ended_state_time": "null",
                    "running_state_time": 1342108989
                },
                {
                    "instance_id": "inst_CP2WrQi2WIS4iheyAVkQYw2",
                    "vm_num_logical_cores": 7,
                    "vm_num_physical_cores": 5,
                    "winning_bid_id": "bid_X5xhotGYiGUk7_RmIqVafA1",
                    "vm_ram": 1429436744,
                    "start_state_time": 1342108906,
                    "vm_ssh_wan_ip_endpoint": "69.4.239.74:62395",
                    "current_state": "Starting",
                    "ended_state_time": "null",
                    "running_state_time": 1342108990
                }
            ],
            "exception_name": ""
        })

        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _compute_api_v1_stop_instance(self, method, url, body, headers):
        body = json.dumps({"exception_name": ""})

        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
