# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_compute
----------------------------------

Functional tests for `shade` compute methods.
"""

from novaclient.v2.servers import Server
from shade import openstack_cloud
from shade.tests import base
from shade.tests.functional.util import pick_flavor, pick_image


class TestCompute(base.TestCase):
    def setUp(self):
        super(TestCompute, self).setUp()
        # Shell should have OS-* envvars from openrc, typically loaded by job
        self.cloud = openstack_cloud()
        self.nova = self.cloud.nova_client
        self.flavor = pick_flavor(self.nova.flavors.list())
        if self.flavor is None:
            self.addDetail('pick_flavor', 'no sensible flavor available')
        self.image = pick_image(self.nova.images.list())
        if self.image is None:
            self.addDetail('pick_image', 'no sensible image available')

    def _cleanup_servers(self):
        for i in self.nova.servers.list():
            if i.name.startswith('test_create'):
                self.nova.servers.delete(i)

    def test_create_server(self):
        self.addCleanup(self._cleanup_servers)
        server = self.cloud.create_server(name='test_create_server',
                                          image=self.image, flavor=self.flavor)
        self.assertIsInstance(server, Server)
        self.assertEquals(server.name, 'test_create_server')
        self.assertEquals(server.image['id'], self.image.id)
        self.assertEquals(server.flavor['id'], self.flavor.id)

    def test_delete_server(self):
        self.cloud.create_server(name='test_delete_server',
                                 image=self.image, flavor=self.flavor)
        server_deleted = self.cloud.delete_server('test_delete_server')
        self.assertIsNone(server_deleted)
