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
"""
Tests for Google Compute Engine Load Balancer Driver
"""
import sys
import unittest

from libcloud.common.google import (GoogleBaseAuthConnection,
                                    GoogleInstalledAppAuthConnection,
                                    GoogleBaseConnection)
from libcloud.compute.drivers.gce import (GCENodeDriver)
from libcloud.loadbalancer.drivers.gce import (GCELBDriver)
from libcloud.test.common.test_google import GoogleAuthMockHttp
from libcloud.test.compute.test_gce import GCEMockHttp

from libcloud.test import LibcloudTestCase

from libcloud.test.secrets import GCE_PARAMS, GCE_KEYWORD_PARAMS


class GCELoadBalancerTest(LibcloudTestCase):
    GoogleBaseConnection._get_token_info_from_file = lambda x: None
    GoogleBaseConnection._write_token_info_to_file = lambda x: None
    GoogleInstalledAppAuthConnection.get_code = lambda x: '1234'
    datacenter = 'us-central1-a'

    def setUp(self):
        GCEMockHttp.test = self
        GCELBDriver.connectionCls.conn_classes = (GCEMockHttp, GCEMockHttp)
        GCENodeDriver.connectionCls.conn_classes = (GCEMockHttp, GCEMockHttp)
        GoogleBaseAuthConnection.conn_classes = (GoogleAuthMockHttp,
                                                 GoogleAuthMockHttp)
        GCEMockHttp.type = None
        kwargs = GCE_KEYWORD_PARAMS.copy()
        kwargs['auth_type'] = 'IA'
        kwargs['datacenter'] = self.datacenter
        self.driver = GCELBDriver(*GCE_PARAMS, **kwargs)

    def test_get_node_from_ip(self):
        ip = '23.236.58.15'
        expected_name = 'node-name'
        node = self.driver._get_node_from_ip(ip)
        self.assertEqual(node.name, expected_name)

        dummy_ip = '8.8.8.8'
        node = self.driver._get_node_from_ip(dummy_ip)
        self.assertTrue(node is None)

    def test_list_protocols(self):
        expected_protocols = ['TCP', 'UDP']
        protocols = self.driver.list_protocols()
        self.assertEqual(protocols, expected_protocols)

    def test_list_balancers(self):
        balancers = self.driver.list_balancers()
        balancers_all = self.driver.list_balancers(ex_region='all')
        balancer_name = 'lcforwardingrule'
        self.assertEqual(len(balancers), 2)
        self.assertEqual(len(balancers_all), 2)
        self.assertEqual(balancers[0].name, balancer_name)

    def test_create_balancer(self):
        balancer_name = 'libcloud-lb-demo-lb'
        tp_name = '%s-tp' % (balancer_name)
        port = '80'
        protocol = 'tcp'
        algorithm = None
        node0 = self.driver.gce.ex_get_node('libcloud-lb-demo-www-000',
                                            'us-central1-b')
        node1 = self.driver.gce.ex_get_node('libcloud-lb-demo-www-001',
                                            'us-central1-b')
        members = [node0, node1]
        balancer = self.driver.create_balancer(balancer_name, port, protocol,
                                               algorithm, members)
        self.assertEqual(balancer.name, balancer_name)
        self.assertEqual(balancer.extra['targetpool'].name, tp_name)
        self.assertEqual(len(balancer.list_members()), 3)

    def test_destory_balancer(self):
        balancer_name = 'lcforwardingrule'
        balancer = self.driver.get_balancer(balancer_name)
        destroyed = balancer.destroy()
        self.assertTrue(destroyed)

    def test_get_balancer(self):
        balancer_name = 'lcforwardingrule'
        tp_name = 'lctargetpool'
        balancer_ip = '173.255.119.224'
        balancer = self.driver.get_balancer(balancer_name)
        self.assertEqual(balancer.name, balancer_name)
        self.assertEqual(balancer.extra['forwarding_rule'].name, balancer_name)
        self.assertEqual(balancer.ip, balancer_ip)
        self.assertEqual(balancer.extra['targetpool'].name, tp_name)

    def test_attach_compute_node(self):
        node = self.driver.gce.ex_get_node('libcloud-lb-demo-www-001',
                                           'us-central1-b')
        balancer = self.driver.get_balancer('lcforwardingrule')
        member = self.driver._node_to_member(node, balancer)
        # Detach member first
        balancer.detach_member(member)
        self.assertEqual(len(balancer.list_members()), 1)
        # Attach Node
        balancer.attach_compute_node(node)
        self.assertEqual(len(balancer.list_members()), 2)

    def test_detach_attach_member(self):
        node = self.driver.gce.ex_get_node('libcloud-lb-demo-www-001',
                                           'us-central1-b')
        balancer = self.driver.get_balancer('lcforwardingrule')
        member = self.driver._node_to_member(node, balancer)

        # Check that balancer has 2 members
        self.assertEqual(len(balancer.list_members()), 2)

        # Remove a member and check that it now has 1 member
        balancer.detach_member(member)
        self.assertEqual(len(balancer.list_members()), 1)

        # Reattach member and check that it has 2 members again
        balancer.attach_member(member)
        self.assertEqual(len(balancer.list_members()), 2)

    def test_balancer_list_members(self):
        balancer = self.driver.get_balancer('lcforwardingrule')
        members = balancer.list_members()
        self.assertEqual(len(members), 2)
        member_ips = [m.ip for m in members]
        self.assertTrue('23.236.58.15' in member_ips)

    def test_ex_create_healthcheck(self):
        healthcheck_name = 'lchealthcheck'
        kwargs = {'host': 'lchost',
                  'path': '/lc',
                  'port': 8000,
                  'interval': 10,
                  'timeout': 10,
                  'unhealthy_threshold': 4,
                  'healthy_threshold': 3}
        hc = self.driver.ex_create_healthcheck(healthcheck_name, **kwargs)
        self.assertEqual(hc.name, healthcheck_name)
        self.assertEqual(hc.path, '/lc')
        self.assertEqual(hc.port, 8000)
        self.assertEqual(hc.interval, 10)

    def test_ex_list_healthchecks(self):
        healthchecks = self.driver.ex_list_healthchecks()
        self.assertEqual(len(healthchecks), 3)
        self.assertEqual(healthchecks[0].name, 'basic-check')

    def test_ex_balancer_detach_attach_healthcheck(self):
        healthcheck = self.driver.gce.ex_get_healthcheck(
            'libcloud-lb-demo-healthcheck')
        balancer = self.driver.get_balancer('lcforwardingrule')

        healthchecks = self.driver.ex_balancer_list_healthchecks(balancer)
        self.assertEqual(len(healthchecks), 1)
        # Detach Healthcheck
        detach_healthcheck = self.driver.ex_balancer_detach_healthcheck(
            balancer, healthcheck)
        self.assertTrue(detach_healthcheck)
        healthchecks = self.driver.ex_balancer_list_healthchecks(balancer)
        self.assertEqual(len(healthchecks), 0)

        # Reattach Healthcheck
        attach_healthcheck = self.driver.ex_balancer_attach_healthcheck(
            balancer, healthcheck)
        self.assertTrue(attach_healthcheck)
        healthchecks = self.driver.ex_balancer_list_healthchecks(balancer)
        self.assertEqual(len(healthchecks), 1)

    def test_ex_balancer_list_healthchecks(self):
        balancer = self.driver.get_balancer('lcforwardingrule')
        healthchecks = self.driver.ex_balancer_list_healthchecks(balancer)
        self.assertEqual(healthchecks[0].name, 'libcloud-lb-demo-healthcheck')

    def test_node_to_member(self):
        node = self.driver.gce.ex_get_node('libcloud-lb-demo-www-001',
                                           'us-central1-b')
        balancer = self.driver.get_balancer('lcforwardingrule')
        member = self.driver._node_to_member(node, balancer)
        self.assertEqual(member.ip, node.public_ips[0])
        self.assertEqual(member.id, node.name)
        self.assertEqual(member.port, balancer.port)

    def test_forwarding_rule_to_loadbalancer(self):
        fwr = self.driver.gce.ex_get_forwarding_rule('lcforwardingrule')
        balancer = self.driver._forwarding_rule_to_loadbalancer(fwr)
        self.assertEqual(fwr.name, balancer.name)
        self.assertEqual(fwr.address, balancer.ip)
        self.assertEqual(fwr.extra['portRange'], balancer.port)

if __name__ == '__main__':
    sys.exit(unittest.main())
