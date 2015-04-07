# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import testtools

import troveclient.v1.client

from troveclient import client as other_client
from troveclient.openstack.common.apiclient import client
from troveclient.openstack.common.apiclient import exceptions


class ClientTest(testtools.TestCase):

    def test_get_client_class_v1(self):
        version_map = other_client.get_version_map()
        output = client.BaseClient.get_class('database',
                                             '1.0', version_map)
        self.assertEqual(output, troveclient.v1.client.Client)

    def test_get_client_class_unknown(self):
        version_map = other_client.get_version_map()
        self.assertRaises(exceptions.UnsupportedVersion,
                          client.BaseClient.get_class, 'database',
                          '0', version_map)
