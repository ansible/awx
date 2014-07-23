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
# Copyright 2009 RedRata Ltd

import sys
import unittest
from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.rimuhosting import RimuHostingNodeDriver

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures


class RimuHostingTest(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        RimuHostingNodeDriver.connectionCls.conn_classes = (None,
                                                            RimuHostingMockHttp)
        self.driver = RimuHostingNodeDriver('foo')

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(node.public_ips[0], "1.2.3.4")
        self.assertEqual(node.public_ips[1], "1.2.3.5")
        self.assertEqual(node.extra['order_oid'], 88833465)
        self.assertEqual(node.id, "order-88833465-api-ivan-net-nz")

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 1)
        size = sizes[0]
        self.assertEqual(size.ram, 950)
        self.assertEqual(size.disk, 20)
        self.assertEqual(size.bandwidth, 75)
        self.assertEqual(size.price, 32.54)

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), 6)
        image = images[0]
        self.assertEqual(image.name, "Debian 5.0 (aka Lenny, RimuHosting"
                         " recommended distro)")
        self.assertEqual(image.id, "lenny")

    def test_reboot_node(self):
        # Raises exception on failure
        node = self.driver.list_nodes()[0]
        self.driver.reboot_node(node)

    def test_destroy_node(self):
        # Raises exception on failure
        node = self.driver.list_nodes()[0]
        self.driver.destroy_node(node)

    def test_create_node(self):
        # Raises exception on failure
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        self.driver.create_node(name="api.ivan.net.nz", image=image, size=size)


class RimuHostingMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('rimuhosting')

    def _r_orders(self, method, url, body, headers):
        body = self.fixtures.load('r_orders.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _r_pricing_plans(self, method, url, body, headers):
        body = self.fixtures.load('r_pricing_plans.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _r_distributions(self, method, url, body, headers):
        body = self.fixtures.load('r_distributions.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _r_orders_new_vps(self, method, url, body, headers):
        body = self.fixtures.load('r_orders_new_vps.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _r_orders_order_88833465_api_ivan_net_nz_vps(self, method, url, body, headers):
        body = self.fixtures.load(
            'r_orders_order_88833465_api_ivan_net_nz_vps.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _r_orders_order_88833465_api_ivan_net_nz_vps_running_state(
        self, method,
        url, body,
            headers):
        body = self.fixtures.load(
            'r_orders_order_88833465_api_ivan_net_nz_vps_running_state.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
