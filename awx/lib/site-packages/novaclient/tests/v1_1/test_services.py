# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM Corp.
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

from novaclient.v1_1 import services
from novaclient.tests.v1_1 import fakes
from novaclient.tests import utils


cs = fakes.FakeClient()


class ServicesTest(utils.TestCase):

    def test_list_services(self):
        svs = cs.services.list()
        cs.assert_called('GET', '/os-services')
        [self.assertTrue(isinstance(s, services.Service)) for s in svs]
        [self.assertEqual(s.binary, 'nova-compute') for s in svs]
        [self.assertEqual(s.host, 'host1') for s in svs]

    def test_list_services_with_hostname(self):
        svs = cs.services.list(host='host2')
        cs.assert_called('GET', '/os-services?host=host2')
        [self.assertTrue(isinstance(s, services.Service)) for s in svs]
        [self.assertEqual(s.binary, 'nova-compute') for s in svs]
        [self.assertEqual(s.host, 'host2') for s in svs]

    def test_list_services_with_binary(self):
        svs = cs.services.list(binary='nova-cert')
        cs.assert_called('GET', '/os-services?binary=nova-cert')
        [self.assertTrue(isinstance(s, services.Service)) for s in svs]
        [self.assertEqual(s.binary, 'nova-cert') for s in svs]
        [self.assertEqual(s.host, 'host1') for s in svs]

    def test_list_services_with_host_binary(self):
        svs = cs.services.list(host='host2', binary='nova-cert')
        cs.assert_called('GET', '/os-services?host=host2&binary=nova-cert')
        [self.assertTrue(isinstance(s, services.Service)) for s in svs]
        [self.assertEqual(s.binary, 'nova-cert') for s in svs]
        [self.assertEqual(s.host, 'host2') for s in svs]

    def test_services_enable(self):
        service = cs.services.enable('host1', 'nova-cert')
        values = {"host": "host1", 'binary': 'nova-cert'}
        cs.assert_called('PUT', '/os-services/enable', values)
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.status, 'enabled')

    def test_services_disable(self):
        service = cs.services.disable('host1', 'nova-cert')
        values = {"host": "host1", 'binary': 'nova-cert'}
        cs.assert_called('PUT', '/os-services/disable', values)
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.status, 'disabled')

    def test_services_disable_log_reason(self):
        service = cs.services.disable_log_reason('compute1', 'nova-compute',
                                                 'disable bad host')
        values = {'host': 'compute1', 'binary': 'nova-compute',
                  'disabled_reason': 'disable bad host'}
        cs.assert_called('PUT', '/os-services/disable-log-reason', values)
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.status, 'disabled')
