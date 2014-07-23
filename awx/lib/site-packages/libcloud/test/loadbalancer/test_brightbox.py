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
from libcloud.loadbalancer.drivers.brightbox import BrightboxLBDriver
from libcloud.loadbalancer.types import State

from libcloud.test import MockHttpTestCase
from libcloud.test.secrets import LB_BRIGHTBOX_PARAMS
from libcloud.test.file_fixtures import LoadBalancerFileFixtures


class BrightboxLBTests(unittest.TestCase):
    def setUp(self):
        BrightboxLBDriver.connectionCls.conn_classes = (None,
                                                        BrightboxLBMockHttp)
        BrightboxLBMockHttp.type = None
        self.driver = BrightboxLBDriver(*LB_BRIGHTBOX_PARAMS)

    def test_list_protocols(self):
        protocols = self.driver.list_protocols()

        self.assertEqual(len(protocols), 2)
        self.assertTrue('tcp' in protocols)
        self.assertTrue('http' in protocols)

    def test_list_balancers(self):
        balancers = self.driver.list_balancers()

        self.assertEqual(len(balancers), 1)
        self.assertEqual(balancers[0].id, 'lba-1235f')
        self.assertEqual(balancers[0].name, 'lb1')

    def test_get_balancer(self):
        balancer = self.driver.get_balancer(balancer_id='lba-1235f')

        self.assertEqual(balancer.id, 'lba-1235f')
        self.assertEqual(balancer.name, 'lb1')
        self.assertEqual(balancer.state, State.RUNNING)

    def test_destroy_balancer(self):
        balancer = self.driver.get_balancer(balancer_id='lba-1235f')

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
        balancer = self.driver.get_balancer(balancer_id='lba-1235f')
        members = balancer.list_members()

        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].balancer, balancer)
        self.assertEqual('srv-lv426', members[0].id)

    def test_balancer_attach_member(self):
        balancer = self.driver.get_balancer(balancer_id='lba-1235f')
        member = balancer.attach_member(Member('srv-kg983', ip=None,
                                               port=None))

        self.assertEqual(member.id, 'srv-kg983')

    def test_balancer_detach_member(self):
        balancer = self.driver.get_balancer(balancer_id='lba-1235f')
        member = Member('srv-lv426', None, None)

        self.assertTrue(balancer.detach_member(member))


class BrightboxLBMockHttp(MockHttpTestCase):
    fixtures = LoadBalancerFileFixtures('brightbox')

    def _token(self, method, url, body, headers):
        if method == 'POST':
            return self.response(httplib.OK, self.fixtures.load('token.json'))

    def _1_0_load_balancers(self, method, url, body, headers):
        if method == 'GET':
            return self.response(httplib.OK,
                                 self.fixtures.load('load_balancers.json'))
        elif method == 'POST':
            body = self.fixtures.load('load_balancers_post.json')
            return self.response(httplib.ACCEPTED, body)

    def _1_0_load_balancers_lba_1235f(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('load_balancers_lba_1235f.json')
            return self.response(httplib.OK, body)
        elif method == 'DELETE':
            return self.response(httplib.ACCEPTED, '')

    def _1_0_load_balancers_lba_1235f_add_nodes(self, method, url, body,
                                                headers):
        if method == 'POST':
            return self.response(httplib.ACCEPTED, '')

    def _1_0_load_balancers_lba_1235f_remove_nodes(self, method, url, body,
                                                   headers):
        if method == 'POST':
            return self.response(httplib.ACCEPTED, '')

    def response(self, status, body):
        return (status, body, {'content-type': 'application/json'},
                httplib.responses[status])


if __name__ == "__main__":
    sys.exit(unittest.main())
