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

import unittest
import sys
import random
import string

from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.gandi import GandiNodeDriver
from libcloud.common.gandi import GandiException
from libcloud.compute.types import NodeState

from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import GANDI_PARAMS
from libcloud.test.common.test_gandi import BaseGandiMockHttp


class GandiTests(unittest.TestCase):

    node_name = 'test2'

    def setUp(self):
        GandiNodeDriver.connectionCls.conn_classes = (
            GandiMockHttp, GandiMockHttp)
        GandiMockHttp.type = None
        self.driver = GandiNodeDriver(*GANDI_PARAMS)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertTrue(len(nodes) > 0)
        self.assertTrue(len(nodes[0].public_ips) > 1)

    def test_list_locations(self):
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        self.assertEqual(loc.country, 'France')

    def test_list_images(self):
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        images = self.driver.list_images(loc)
        self.assertTrue(len(images) > 2)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertTrue(len(sizes) >= 1)

    def test_destroy_node_running(self):
        nodes = self.driver.list_nodes()
        test_node = list(filter(lambda x: x.state == NodeState.RUNNING,
                                nodes))[0]
        self.assertTrue(self.driver.destroy_node(test_node))

    def test_destroy_node_halted(self):
        nodes = self.driver.list_nodes()
        test_node = list(filter(lambda x: x.state == NodeState.TERMINATED,
                                nodes))[0]
        self.assertTrue(self.driver.destroy_node(test_node))

    def test_reboot_node(self):
        nodes = self.driver.list_nodes()
        test_node = list(filter(lambda x: x.state == NodeState.RUNNING,
                                nodes))[0]
        self.assertTrue(self.driver.reboot_node(test_node))

    def test_create_node(self):
        login = 'libcloud'
        passwd = ''.join(random.choice(string.ascii_letters)
                         for i in range(10))

        # Get france datacenter
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]

        # Get a debian image
        images = self.driver.list_images(loc)
        images = [x for x in images if x.name.lower().startswith('debian')]
        img = list(filter(lambda x: '5' in x.name, images))[0]

        # Get a configuration size
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(name=self.node_name, login=login,
                                       password=passwd, image=img,
                                       location=loc, size=size)
        self.assertEqual(node.name, self.node_name)

    def test_create_volume(self):
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        volume = self.driver.create_volume(
            size=1024, name='libcloud', location=loc)
        self.assertEqual(volume.name, 'libcloud')
        self.assertEqual(volume.size, 1024)

    def test_list_volumes(self):
        disks = self.driver.list_volumes()
        self.assertTrue(len(disks) > 0)

    def test_destroy_volume(self):
        volumes = self.driver.list_volumes()
        test_vol = list(filter(lambda x: x.name == 'test_disk',
                               volumes))[0]
        self.assertTrue(self.driver.destroy_volume(test_vol))

    def test_attach_volume(self):
        disks = self.driver.list_volumes()
        nodes = self.driver.list_nodes()
        res = self.driver.attach_volume(nodes[0], disks[0])
        self.assertTrue(res)

    def test_detach_volume(self):
        disks = self.driver.list_volumes()
        nodes = self.driver.list_nodes()
        res = self.driver.detach_volume(nodes[0], disks[0])
        self.assertTrue(res)

    def test_ex_list_interfaces(self):
        ifaces = self.driver.ex_list_interfaces()
        self.assertTrue(len(ifaces) > 0)

    def test_ex_attach_interface(self):
        ifaces = self.driver.ex_list_interfaces()
        nodes = self.driver.list_nodes()
        res = self.driver.ex_node_attach_interface(nodes[0], ifaces[0])
        self.assertTrue(res)

    def test_ex_detach_interface(self):
        ifaces = self.driver.ex_list_interfaces()
        nodes = self.driver.list_nodes()
        res = self.driver.ex_node_detach_interface(nodes[0], ifaces[0])
        self.assertTrue(res)

    def test_ex_snapshot_disk(self):
        disks = self.driver.list_volumes()
        self.assertTrue(self.driver.ex_snapshot_disk(disks[2]))
        self.assertRaises(GandiException,
                          self.driver.ex_snapshot_disk, disks[0])

    def test_ex_update_disk(self):
        disks = self.driver.list_volumes()
        self.assertTrue(self.driver.ex_update_disk(disks[0], new_size=4096))


class GandiRatingTests(unittest.TestCase):

    """Tests where rating model is involved"""

    node_name = 'test2'

    def setUp(self):
        GandiNodeDriver.connectionCls.conn_classes = (
            GandiMockRatingHttp, GandiMockRatingHttp)
        GandiMockRatingHttp.type = None
        self.driver = GandiNodeDriver(*GANDI_PARAMS)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 4)

    def test_create_node(self):
        login = 'libcloud'
        passwd = ''.join(random.choice(string.ascii_letters)
                         for i in range(10))

        # Get france datacenter
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]

        # Get a debian image
        images = self.driver.list_images(loc)
        images = [x for x in images if x.name.lower().startswith('debian')]
        img = list(filter(lambda x: '5' in x.name, images))[0]

        # Get a configuration size
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(name=self.node_name, login=login,
                                       password=passwd, image=img,
                                       location=loc, size=size)
        self.assertEqual(node.name, self.node_name)


class GandiMockHttp(BaseGandiMockHttp):

    fixtures = ComputeFileFixtures('gandi')

    def _xmlrpc__hosting_datacenter_list(self, method, url, body, headers):
        body = self.fixtures.load('datacenter_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_image_list(self, method, url, body, headers):
        body = self.fixtures.load('image_list_dc0.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_list(self, method, url, body, headers):
        body = self.fixtures.load('vm_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_ip_list(self, method, url, body, headers):
        body = self.fixtures.load('ip_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_account_info(self, method, url, body, headers):
        body = self.fixtures.load('account_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_info(self, method, url, body, headers):
        body = self.fixtures.load('vm_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_delete(self, method, url, body, headers):
        body = self.fixtures.load('vm_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__operation_info(self, method, url, body, headers):
        body = self.fixtures.load('operation_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_create_from(self, method, url, body, headers):
        body = self.fixtures.load('vm_create_from.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_reboot(self, method, url, body, headers):
        body = self.fixtures.load('vm_reboot.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_stop(self, method, url, body, headers):
        body = self.fixtures.load('vm_stop.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_iface_list(self, method, url, body, headers):
        body = self.fixtures.load('iface_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_list(self, method, url, body, headers):
        body = self.fixtures.load('disk_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_iface_attach(self, method, url, body, headers):
        body = self.fixtures.load('iface_attach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_iface_detach(self, method, url, body, headers):
        body = self.fixtures.load('iface_detach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_disk_attach(self, method, url, body, headers):
        body = self.fixtures.load('disk_attach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_disk_detach(self, method, url, body, headers):
        body = self.fixtures.load('disk_detach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_create(self, method, url, body, headers):
        body = self.fixtures.load('disk_create.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_create_from(self, method, url, body, headers):
        body = self.fixtures.load('disk_create_from.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_info(self, method, url, body, headers):
        body = self.fixtures.load('disk_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_update(self, method, url, body, headers):
        body = self.fixtures.load('disk_update.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_delete(self, method, url, body, headers):
        body = self.fixtures.load('disk_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


class GandiMockRatingHttp(BaseGandiMockHttp):

    """Fixtures needed for tests related to rating model"""

    fixtures = ComputeFileFixtures('gandi')

    def _xmlrpc__hosting_datacenter_list(self, method, url, body, headers):
        body = self.fixtures.load('datacenter_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_image_list(self, method, url, body, headers):
        body = self.fixtures.load('image_list_dc0.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_create_from(self, method, url, body, headers):
        body = self.fixtures.load('vm_create_from.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__operation_info(self, method, url, body, headers):
        body = self.fixtures.load('operation_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_info(self, method, url, body, headers):
        body = self.fixtures.load('vm_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    # Specific to rating tests
    def _xmlrpc__hosting_account_info(self, method, url, body, headers):
        body = self.fixtures.load('account_info_rating.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
