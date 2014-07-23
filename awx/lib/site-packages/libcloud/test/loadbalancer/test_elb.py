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
from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.drivers.elb import ElasticLBDriver
from libcloud.loadbalancer.types import State

from libcloud.test import MockHttpTestCase
from libcloud.test.secrets import LB_ELB_PARAMS
from libcloud.test.file_fixtures import LoadBalancerFileFixtures


class ElasticLBTests(unittest.TestCase):
    def setUp(self):
        ElasticLBMockHttp.test = self
        ElasticLBDriver.connectionCls.conn_classes = (None,
                                                      ElasticLBMockHttp)
        ElasticLBMockHttp.type = None
        ElasticLBMockHttp.use_param = 'Action'

        self.driver = ElasticLBDriver(*LB_ELB_PARAMS)

    def test_list_protocols(self):
        protocols = self.driver.list_protocols()

        self.assertEqual(len(protocols), 4)
        self.assertTrue('tcp' in protocols)
        self.assertTrue('http' in protocols)

    def test_list_balancers(self):
        balancers = self.driver.list_balancers()

        self.assertEqual(len(balancers), 1)
        self.assertEqual(balancers[0].id, 'tests')
        self.assertEqual(balancers[0].name, 'tests')

    def test_get_balancer(self):
        balancer = self.driver.get_balancer(balancer_id='tests')

        self.assertEqual(balancer.id, 'tests')
        self.assertEqual(balancer.name, 'tests')
        self.assertEqual(balancer.state, State.UNKNOWN)

    def test_destroy_balancer(self):
        balancer = self.driver.get_balancer(balancer_id='tests')

        self.assertTrue(self.driver.destroy_balancer(balancer))

    def test_create_balancer(self):
        members = [Member('srv-lv426', None, None)]

        balancer = self.driver.create_balancer(name='lb2', port=80,
                                               protocol='http',
                                               algorithm=Algorithm.ROUND_ROBIN,
                                               members=members)

        self.assertEqual(balancer.name, 'lb2')
        self.assertEqual(balancer.port, 80)
        self.assertEqual(balancer.state, State.PENDING)

    def test_balancer_list_members(self):
        balancer = self.driver.get_balancer(balancer_id='tests')
        members = balancer.list_members()

        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].balancer, balancer)
        self.assertEqual('i-64bd081c', members[0].id)

    def test_balancer_detach_member(self):
        balancer = self.driver.get_balancer(balancer_id='lba-1235f')
        member = Member('i-64bd081c', None, None)

        self.assertTrue(balancer.detach_member(member))

    def test_ex_list_balancer_policies(self):
        balancer = self.driver.get_balancer(balancer_id='tests')
        policies = self.driver.ex_list_balancer_policies(balancer)

        self.assertTrue('MyDurationStickyPolicy' in policies)

    def test_ex_list_balancer_policy_types(self):
        policy_types = self.driver.ex_list_balancer_policy_types()

        self.assertTrue('ProxyProtocolPolicyType' in policy_types)

    def test_ex_create_balancer_policy(self):
        self.assertTrue(
            self.driver.ex_create_balancer_policy(
                name='tests',
                policy_name='MyDurationProxyPolicy',
                policy_type='ProxyProtocolPolicyType'))

    def test_ex_delete_balancer_policy(self):
        self.assertTrue(
            self.driver.ex_delete_balancer_policy(
                name='tests',
                policy_name='MyDurationProxyPolicy'))

    def test_ex_set_balancer_policies_listener(self):
        self.assertTrue(
            self.driver.ex_set_balancer_policies_listener(
                name='tests',
                port=80,
                policies=['MyDurationStickyPolicy']))

    def test_ex_set_balancer_policies_backend_server(self):
        self.assertTrue(
            self.driver.ex_set_balancer_policies_backend_server(
                name='tests',
                instance_port=80,
                policies=['MyDurationProxyPolicy']))

    def text_ex_create_balancer_listeners(self):
        self.assertTrue(
            self.driver.ex_create_balancer_listeners(
                name='tests',
                listeners=[[1024, 65533, 'HTTP']]))


class ElasticLBMockHttp(MockHttpTestCase):
    fixtures = LoadBalancerFileFixtures('elb')

    def _2012_06_01_DescribeLoadBalancers(self, method, url, body, headers):
        body = self.fixtures.load('describe_load_balancers.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_CreateLoadBalancer(self, method, url, body, headers):
        body = self.fixtures.load('create_load_balancer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_DeregisterInstancesFromLoadBalancer(self, method, url,
                                                        body, headers):
        body = self.fixtures.load(
            'deregister_instances_from_load_balancer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_CreateLoadBalancerPolicy(self, method, url, body, headers):
        body = self.fixtures.load('create_load_balancer_policy.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_DeleteLoadBalancer(self, method, url, body, headers):
        body = ''
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_DescribeLoadBalancerPolicies(self, method, url, body,
                                                 headers):
        body = self.fixtures.load('describe_load_balancer_policies.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_DescribeLoadBalancerPolicyTypes(self, method, url, body,
                                                    headers):
        body = self.fixtures.load('describe_load_balancers_policy_types.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_DeleteLoadBalancerPolicy(self, method, url, body, headers):
        body = ''
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_SetLoadBalancerPoliciesOfListener(self, method, url, body,
                                                      headers):
        body = self.fixtures.load('set_load_balancer_policies_of_listener.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _2012_06_01_SetLoadBalancerPoliciesForBackendServer(self, method, url,
                                                            body, headers):
        body = self.fixtures.load(
            'set_load_balancer_policies_for_backend_server.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == "__main__":
    sys.exit(unittest.main())
