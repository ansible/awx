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
from libcloud.utils.py3 import urlparse

from libcloud.common.types import LibcloudError
from libcloud.compute.base import Node
from libcloud.compute.drivers.dummy import DummyNodeDriver
from libcloud.loadbalancer.base import LoadBalancer, Member, Algorithm
from libcloud.loadbalancer.drivers.gogrid import GoGridLBDriver

from libcloud.test import MockHttpTestCase
from libcloud.test.file_fixtures import LoadBalancerFileFixtures


class GoGridTests(unittest.TestCase):

    def setUp(self):
        GoGridLBDriver.connectionCls.conn_classes = (None,
                                                     GoGridLBMockHttp)
        GoGridLBMockHttp.type = None
        self.driver = GoGridLBDriver('user', 'key')

    def test_list_supported_algorithms(self):
        algorithms = self.driver.list_supported_algorithms()

        self.assertTrue(Algorithm.ROUND_ROBIN in algorithms)
        self.assertTrue(Algorithm.LEAST_CONNECTIONS in algorithms)

    def test_list_protocols(self):
        protocols = self.driver.list_protocols()

        self.assertEqual(len(protocols), 1)
        self.assertEqual(protocols[0], 'http')

    def test_list_balancers(self):
        balancers = self.driver.list_balancers()

        self.assertEqual(len(balancers), 2)
        self.assertEqual(balancers[0].name, "foo")
        self.assertEqual(balancers[0].id, "23517")
        self.assertEqual(balancers[1].name, "bar")
        self.assertEqual(balancers[1].id, "23526")

    def test_create_balancer(self):
        balancer = self.driver.create_balancer(name='test2',
                                               port=80,
                                               protocol='http',
                                               algorithm=Algorithm.ROUND_ROBIN,
                                               members=(
                                                   Member(
                                                       None, '10.1.0.10', 80),
                                                   Member(None, '10.1.0.11', 80))
                                               )

        self.assertEqual(balancer.name, 'test2')
        self.assertEqual(balancer.id, '123')

    def test_create_balancer_UNEXPECTED_ERROR(self):
        # Try to create new balancer and attach members with an IP address which
        # does not belong to this account
        GoGridLBMockHttp.type = 'UNEXPECTED_ERROR'

        try:
            self.driver.create_balancer(name='test2',
                                        port=80,
                                        protocol='http',
                                        algorithm=Algorithm.ROUND_ROBIN,
                                        members=(Member(None, '10.1.0.10', 80),
                                                 Member(None, '10.1.0.11', 80))
                                        )
        except LibcloudError:
            e = sys.exc_info()[1]
            self.assertTrue(
                str(e).find('tried to add a member with an IP address not assigned to your account') != -1)
        else:
            self.fail('Exception was not thrown')

    def test_destroy_balancer(self):
        balancer = self.driver.list_balancers()[0]

        ret1 = self.driver.destroy_balancer(balancer)
        ret2 = balancer.destroy()

        self.assertTrue(ret1)
        self.assertTrue(ret2)

    def test_get_balancer(self):
        balancer = self.driver.get_balancer(balancer_id='23530')

        self.assertEqual(balancer.name, 'test2')
        self.assertEqual(balancer.id, '23530')

    def test_balancer_list_members(self):
        balancer = self.driver.get_balancer(balancer_id='23530')
        members1 = self.driver.balancer_list_members(balancer=balancer)
        members2 = balancer.list_members()

        expected_members = set(['10.0.0.78:80', '10.0.0.77:80',
                                '10.0.0.76:80'])

        self.assertEqual(len(members1), 3)
        self.assertEqual(len(members2), 3)
        self.assertEqual(expected_members,
                         set(["%s:%s" % (member.ip, member.port) for member in members1]))
        self.assertEquals(members1[0].balancer, balancer)

    def test_balancer_attach_compute_node(self):
        balancer = LoadBalancer(23530, None, None, None, None, self.driver)
        node = Node(id='1', name='test', state=None, public_ips=['10.0.0.75'],
                    private_ips=[], driver=DummyNodeDriver)
        member1 = self.driver.balancer_attach_compute_node(balancer, node)
        member2 = balancer.attach_compute_node(node)

        self.assertEqual(member1.ip, '10.0.0.75')
        self.assertEqual(member1.port, 80)
        self.assertEqual(member2.ip, '10.0.0.75')
        self.assertEqual(member2.port, 80)

    def test_balancer_attach_member(self):
        balancer = LoadBalancer(23530, None, None, None, None, self.driver)
        member = Member(None, ip='10.0.0.75', port='80')
        member1 = self.driver.balancer_attach_member(balancer, member=member)
        member2 = balancer.attach_member(member=member)

        self.assertEqual(member1.ip, '10.0.0.75')
        self.assertEqual(member1.port, 80)
        self.assertEqual(member2.ip, '10.0.0.75')
        self.assertEqual(member2.port, 80)

    def test_balancer_detach_member(self):
        balancer = LoadBalancer(23530, None, None, None, None, self.driver)
        member = self.driver.balancer_list_members(balancer)[0]

        ret1 = self.driver.balancer_detach_member(balancer, member)
        ret2 = balancer.detach_member(member)

        self.assertTrue(ret1)
        self.assertTrue(ret2)


class GoGridLBMockHttp(MockHttpTestCase):
    fixtures = LoadBalancerFileFixtures('gogrid')

    def _api_grid_loadbalancer_list(self, method, url, body, headers):
        body = self.fixtures.load('loadbalancer_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_grid_ip_list(self, method, url, body, headers):
        body = self.fixtures.load('ip_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_grid_loadbalancer_add(self, method, url, body, headers):
        query = urlparse.urlparse(url).query
        self.assertTrue(query.find('loadbalancer.type=round+robin') != -1)

        body = self.fixtures.load('loadbalancer_add.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_grid_ip_list_UNEXPECTED_ERROR(self, method, url, body, headers):
        return self._api_grid_ip_list(method, url, body, headers)

    def _api_grid_loadbalancer_add_UNEXPECTED_ERROR(self, method, url, body, headers):
        body = self.fixtures.load('unexpected_error.json')
        return (httplib.INTERNAL_SERVER_ERROR, body, {}, httplib.responses[httplib.OK])

    def _api_grid_loadbalancer_delete(self, method, url, body, headers):
        body = self.fixtures.load('loadbalancer_add.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_grid_loadbalancer_get(self, method, url, body, headers):
        body = self.fixtures.load('loadbalancer_get.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_grid_loadbalancer_edit(self, method, url, body, headers):
        body = self.fixtures.load('loadbalancer_edit.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == "__main__":
    sys.exit(unittest.main())
