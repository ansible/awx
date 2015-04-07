# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testtools

from shade import meta


class TestMeta(testtools.TestCase):
    def test_find_nova_addresses_key_name(self):
        # Note 198.51.100.0/24 is TEST-NET-2 from rfc5737
        addrs = {'public': [{'addr': '198.51.100.1', 'version': 4}],
                 'private': [{'addr': '192.0.2.5', 'version': 4}]}
        self.assertEqual(
            ['198.51.100.1'],
            meta.find_nova_addresses(addrs, key_name='public'))
        self.assertEqual([], meta.find_nova_addresses(addrs, key_name='foo'))

    def test_find_nova_addresses_ext_tag(self):
        addrs = {'public': [{'OS-EXT-IPS:type': 'fixed',
                             'addr': '198.51.100.2',
                             'version': 4}]}
        self.assertEqual(
            ['198.51.100.2'], meta.find_nova_addresses(addrs, ext_tag='fixed'))
        self.assertEqual([], meta.find_nova_addresses(addrs, ext_tag='foo'))

    def test_get_server_ip(self):
        class Server(object):
            addresses = {'private': [{'OS-EXT-IPS:type': 'fixed',
                                      'addr': '198.51.100.3',
                                      'version': 4}],
                         'public': [{'OS-EXT-IPS:type': 'floating',
                                     'addr': '192.0.2.99',
                                     'version': 4}]}
        srv = Server()
        self.assertEqual('198.51.100.3', meta.get_server_private_ip(srv))
        self.assertEqual('192.0.2.99', meta.get_server_public_ip(srv))

    def test_get_groups_from_server(self):
        class Cloud(object):
            region_name = 'test-region'
            name = 'test-name'

        class Server(object):
            id = 'test-id-0'
            metadata = {'group': 'test-group'}

        server_vars = {'flavor': 'test-flavor',
                       'image': 'test-image',
                       'az': 'test-az'}
        self.assertEqual(
            ['test-name',
             'test-region',
             'test-name_test-region',
             'test-group',
             'instance-test-id-0',
             'meta-group_test-group',
             'test-az',
             'test-region_test-az',
             'test-name_test-region_test-az'],
            meta.get_groups_from_server(Cloud(), Server(), server_vars))
