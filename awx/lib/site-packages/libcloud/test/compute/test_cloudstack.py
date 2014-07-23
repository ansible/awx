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
import os

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import parse_qsl

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.common.types import ProviderError
from libcloud.compute.drivers.cloudstack import CloudStackNodeDriver
from libcloud.compute.types import LibcloudError, Provider, InvalidCredsError
from libcloud.compute.types import KeyPairDoesNotExistError
from libcloud.compute.providers import get_driver

from libcloud.test import unittest
from libcloud.test import MockHttpTestCase
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures


class CloudStackCommonTestCase(TestCaseMixin):
    driver_klass = CloudStackNodeDriver

    def setUp(self):
        self.driver_klass.connectionCls.conn_classes = \
            (None, CloudStackMockHttp)
        self.driver = self.driver_klass('apikey', 'secret',
                                        path='/test/path',
                                        host='api.dummy.com')
        self.driver.path = '/test/path'
        self.driver.type = -1
        CloudStackMockHttp.type = None
        CloudStackMockHttp.fixture_tag = 'default'
        self.driver.connection.poll_interval = 0.0

    def test_invalid_credentials(self):
        CloudStackMockHttp.type = 'invalid_credentials'
        driver = self.driver_klass('invalid', 'invalid', path='/test/path',
                                   host='api.dummy.com')
        self.assertRaises(InvalidCredsError, driver.list_nodes)

    def test_import_keypair_from_string_api_error(self):
        CloudStackMockHttp.type = 'api_error'

        name = 'test-pair'
        key_material = ''

        expected_msg = 'Public key is invalid'
        self.assertRaisesRegexp(ProviderError, expected_msg,
                                self.driver.import_key_pair_from_string,
                                name=name, key_material=key_material)

    def test_create_node_immediate_failure(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        CloudStackMockHttp.fixture_tag = 'deployfail'
        try:
            self.driver.create_node(name='node-name',
                                    image=image,
                                    size=size)
        except:
            return
        self.assertTrue(False)

    def test_create_node_delayed_failure(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        CloudStackMockHttp.fixture_tag = 'deployfail2'
        try:
            self.driver.create_node(name='node-name',
                                    image=image,
                                    size=size)
        except:
            return
        self.assertTrue(False)

    def test_create_node_default_location_success(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        default_location = self.driver.list_locations()[0]

        node = self.driver.create_node(name='fred',
                                       image=image,
                                       size=size)

        self.assertEqual(node.name, 'fred')
        self.assertEqual(node.public_ips, [])
        self.assertEqual(node.private_ips, ['192.168.1.2'])
        self.assertEqual(node.extra['zone_id'], default_location.id)

    def test_create_node_ex_security_groups(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        location = self.driver.list_locations()[0]
        sg = [sg['name'] for sg in self.driver.ex_list_security_groups()]
        CloudStackMockHttp.fixture_tag = 'deploysecuritygroup'
        node = self.driver.create_node(name='test',
                                       location=location,
                                       image=image,
                                       size=size,
                                       ex_security_groups=sg)
        self.assertEqual(node.name, 'test')
        self.assertEqual(node.extra['security_group'], sg)
        self.assertEqual(node.id, 'fc4fd31a-16d3-49db-814a-56b39b9ef986')

    def test_create_node_ex_keyname(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        location = self.driver.list_locations()[0]
        CloudStackMockHttp.fixture_tag = 'deploykeyname'
        node = self.driver.create_node(name='test',
                                       location=location,
                                       image=image,
                                       size=size,
                                       ex_keyname='foobar')
        self.assertEqual(node.name, 'test')
        self.assertEqual(node.extra['key_name'], 'foobar')

    def test_create_node_project(self):
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        location = self.driver.list_locations()[0]
        project = self.driver.ex_list_projects()[0]
        CloudStackMockHttp.fixture_tag = 'deployproject'
        node = self.driver.create_node(name='test',
                                       location=location,
                                       image=image,
                                       size=size,
                                       project=project)
        self.assertEqual(node.name, 'TestNode')
        self.assertEqual(node.extra['project'], 'Test Project')

    def test_list_images_no_images_available(self):
        CloudStackMockHttp.fixture_tag = 'notemplates'

        images = self.driver.list_images()
        self.assertEqual(0, len(images))

    def test_list_images(self):
        _, fixture = CloudStackMockHttp()._load_fixture(
            'listTemplates_default.json')
        templates = fixture['listtemplatesresponse']['template']

        images = self.driver.list_images()
        for i, image in enumerate(images):
            # NodeImage expects id to be a string,
            # the CloudStack fixture has an int
            tid = str(templates[i]['id'])
            tname = templates[i]['name']
            self.assertIsInstance(image.driver, CloudStackNodeDriver)
            self.assertEqual(image.id, tid)
            self.assertEqual(image.name, tname)

    def test_ex_list_disk_offerings(self):
        diskOfferings = self.driver.ex_list_disk_offerings()
        self.assertEqual(1, len(diskOfferings))

        diskOffering, = diskOfferings

        self.assertEqual('Disk offer 1', diskOffering.name)
        self.assertEqual(10, diskOffering.size)

    def test_ex_list_networks(self):
        _, fixture = CloudStackMockHttp()._load_fixture(
            'listNetworks_default.json')
        fixture_networks = fixture['listnetworksresponse']['network']

        networks = self.driver.ex_list_networks()

        for i, network in enumerate(networks):
            self.assertEqual(network.id, fixture_networks[i]['id'])
            self.assertEqual(
                network.displaytext, fixture_networks[i]['displaytext'])
            self.assertEqual(network.name, fixture_networks[i]['name'])
            self.assertEqual(
                network.networkofferingid,
                fixture_networks[i]['networkofferingid'])
            self.assertEqual(network.zoneid, fixture_networks[i]['zoneid'])

    def test_ex_list_network_offerings(self):
        _, fixture = CloudStackMockHttp()._load_fixture(
            'listNetworkOfferings_default.json')
        fixture_networkoffers = \
            fixture['listnetworkofferingsresponse']['networkoffering']

        networkoffers = self.driver.ex_list_network_offerings()

        for i, networkoffer in enumerate(networkoffers):
            self.assertEqual(networkoffer.id, fixture_networkoffers[i]['id'])
            self.assertEqual(networkoffer.name,
                             fixture_networkoffers[i]['name'])
            self.assertEqual(networkoffer.display_text,
                             fixture_networkoffers[i]['displaytext'])
            self.assertEqual(networkoffer.for_vpc,
                             fixture_networkoffers[i]['forvpc'])
            self.assertEqual(networkoffer.guest_ip_type,
                             fixture_networkoffers[i]['guestiptype'])
            self.assertEqual(networkoffer.service_offering_id,
                             fixture_networkoffers[i]['serviceofferingid'])

    def test_ex_create_network(self):
        _, fixture = CloudStackMockHttp()._load_fixture(
            'createNetwork_default.json')

        fixture_network = fixture['createnetworkresponse']['network']

        netoffer = self.driver.ex_list_network_offerings()[0]
        location = self.driver.list_locations()[0]
        network = self.driver.ex_create_network(display_text='test',
                                                name='test',
                                                network_offering=netoffer,
                                                location=location,
                                                gateway='10.1.1.1',
                                                netmask='255.255.255.0',
                                                network_domain='cloud.local',
                                                vpc_id="2",
                                                project_id="2")

        self.assertEqual(network.name, fixture_network['name'])
        self.assertEqual(network.displaytext, fixture_network['displaytext'])
        self.assertEqual(network.id, fixture_network['id'])
        self.assertEqual(network.extra['gateway'], fixture_network['gateway'])
        self.assertEqual(network.extra['netmask'], fixture_network['netmask'])
        self.assertEqual(network.networkofferingid,
                         fixture_network['networkofferingid'])
        self.assertEqual(network.extra['vpc_id'], fixture_network['vpcid'])
        self.assertEqual(network.extra['project_id'],
                         fixture_network['projectid'])

    def test_ex_delete_network(self):

        network = self.driver.ex_list_networks()[0]

        result = self.driver.ex_delete_network(network=network)
        self.assertTrue(result)

    def test_ex_list_projects(self):
        _, fixture = CloudStackMockHttp()._load_fixture(
            'listProjects_default.json')
        fixture_projects = fixture['listprojectsresponse']['project']

        projects = self.driver.ex_list_projects()

        for i, project in enumerate(projects):
            self.assertEqual(project.id, fixture_projects[i]['id'])
            self.assertEqual(
                project.display_text, fixture_projects[i]['displaytext'])
            self.assertEqual(project.name, fixture_projects[i]['name'])
            self.assertEqual(
                project.extra['domainid'],
                fixture_projects[i]['domainid'])
            self.assertEqual(
                project.extra['cpulimit'],
                fixture_projects[i]['cpulimit'])

    def test_create_volume(self):
        volumeName = 'vol-0'
        location = self.driver.list_locations()[0]

        volume = self.driver.create_volume(10, volumeName, location)

        self.assertEqual(volumeName, volume.name)
        self.assertEqual(10, volume.size)

    def test_create_volume_no_noncustomized_offering_with_size(self):
        """If the sizes of disk offerings are not configurable and there
        are no disk offerings with the requested size, an exception should
        be thrown."""

        location = self.driver.list_locations()[0]

        self.assertRaises(
            LibcloudError,
            self.driver.create_volume,
            'vol-0', location, 11)

    def test_create_volume_with_custom_disk_size_offering(self):
        CloudStackMockHttp.fixture_tag = 'withcustomdisksize'

        volumeName = 'vol-0'
        location = self.driver.list_locations()[0]

        volume = self.driver.create_volume(10, volumeName, location)

        self.assertEqual(volumeName, volume.name)

    def test_attach_volume(self):
        node = self.driver.list_nodes()[0]
        volumeName = 'vol-0'
        location = self.driver.list_locations()[0]

        volume = self.driver.create_volume(10, volumeName, location)
        attachReturnVal = self.driver.attach_volume(volume, node)

        self.assertTrue(attachReturnVal)

    def test_detach_volume(self):
        volumeName = 'gre-test-volume'
        location = self.driver.list_locations()[0]
        volume = self.driver.create_volume(10, volumeName, location)
        res = self.driver.detach_volume(volume)
        self.assertTrue(res)

    def test_destroy_volume(self):
        volumeName = 'gre-test-volume'
        location = self.driver.list_locations()[0]
        volume = self.driver.create_volume(10, volumeName, location)
        res = self.driver.destroy_volume(volume)
        self.assertTrue(res)

    def test_list_volumes(self):
        volumes = self.driver.list_volumes()
        self.assertEqual(1, len(volumes))
        self.assertEqual('ROOT-69942', volumes[0].name)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(2, len(nodes))
        self.assertEqual('test', nodes[0].name)
        self.assertEqual('2600', nodes[0].id)
        self.assertEqual([], nodes[0].extra['security_group'])
        self.assertEqual(None, nodes[0].extra['key_name'])

    def test_list_locations(self):
        location = self.driver.list_locations()[0]
        self.assertEqual('1', location.id)
        self.assertEqual('Sydney', location.name)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual('Compute Micro PRD', sizes[0].name)
        self.assertEqual('105', sizes[0].id)
        self.assertEqual(384, sizes[0].ram)
        self.assertEqual('Compute Large PRD', sizes[2].name)
        self.assertEqual('69', sizes[2].id)
        self.assertEqual(6964, sizes[2].ram)

    def test_ex_start_node(self):
        node = self.driver.list_nodes()[0]
        res = node.ex_start()
        self.assertEqual('Starting', res)

    def test_ex_stop_node(self):
        node = self.driver.list_nodes()[0]
        res = node.ex_stop()
        self.assertEqual('Stopped', res)

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        res = node.destroy()
        self.assertTrue(res)

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        res = node.reboot()
        self.assertTrue(res)

    def test_list_key_pairs(self):
        keypairs = self.driver.list_key_pairs()
        fingerprint = '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:' + \
                      '00:00:00:00:00'

        self.assertEqual(keypairs[0].name, 'cs-keypair')
        self.assertEqual(keypairs[0].fingerprint, fingerprint)

        # Test old and deprecated way
        keypairs = self.driver.ex_list_keypairs()

        self.assertEqual(keypairs[0]['name'], 'cs-keypair')
        self.assertEqual(keypairs[0]['fingerprint'], fingerprint)

    def test_list_key_pairs_no_keypair_key(self):
        CloudStackMockHttp.fixture_tag = 'no_keys'
        keypairs = self.driver.list_key_pairs()
        self.assertEqual(keypairs, [])

    def test_get_key_pair(self):
        CloudStackMockHttp.fixture_tag = 'get_one'
        key_pair = self.driver.get_key_pair(name='cs-keypair')
        self.assertEqual(key_pair.name, 'cs-keypair')

    def test_get_key_pair_doesnt_exist(self):
        CloudStackMockHttp.fixture_tag = 'get_one_doesnt_exist'

        self.assertRaises(KeyPairDoesNotExistError, self.driver.get_key_pair,
                          name='does-not-exist')

    def test_create_keypair(self):
        key_pair = self.driver.create_key_pair(name='test-keypair')

        self.assertEqual(key_pair.name, 'test-keypair')
        self.assertTrue(key_pair.fingerprint is not None)
        self.assertTrue(key_pair.private_key is not None)

        # Test old and deprecated way
        res = self.driver.ex_create_keypair(name='test-keypair')
        self.assertEqual(res['name'], 'test-keypair')
        self.assertTrue(res['fingerprint'] is not None)
        self.assertTrue(res['privateKey'] is not None)

    def test_import_keypair_from_file(self):
        fingerprint = 'c4:a1:e5:d4:50:84:a9:4c:6b:22:ee:d6:57:02:b8:15'
        path = os.path.join(os.path.dirname(__file__), 'fixtures',
                            'cloudstack',
                            'dummy_rsa.pub')

        key_pair = self.driver.import_key_pair_from_file('foobar', path)
        self.assertEqual(key_pair.name, 'foobar')
        self.assertEqual(key_pair.fingerprint, fingerprint)

        # Test old and deprecated way
        res = self.driver.ex_import_keypair('foobar', path)
        self.assertEqual(res['keyName'], 'foobar')
        self.assertEqual(res['keyFingerprint'], fingerprint)

    def test_ex_import_keypair_from_string(self):
        fingerprint = 'c4:a1:e5:d4:50:84:a9:4c:6b:22:ee:d6:57:02:b8:15'
        path = os.path.join(os.path.dirname(__file__), 'fixtures',
                            'cloudstack',
                            'dummy_rsa.pub')
        fh = open(path)
        key_material = fh.read()
        fh.close()

        key_pair = self.driver.import_key_pair_from_string('foobar', key_material=key_material)
        self.assertEqual(key_pair.name, 'foobar')
        self.assertEqual(key_pair.fingerprint, fingerprint)

        # Test old and deprecated way
        res = self.driver.ex_import_keypair_from_string('foobar', key_material=key_material)
        self.assertEqual(res['keyName'], 'foobar')
        self.assertEqual(res['keyFingerprint'], fingerprint)

    def test_delete_key_pair(self):
        key_pair = self.driver.list_key_pairs()[0]

        res = self.driver.delete_key_pair(key_pair=key_pair)
        self.assertTrue(res)

        # Test old and deprecated way
        res = self.driver.ex_delete_keypair(keypair='cs-keypair')
        self.assertTrue(res)

    def test_ex_list_security_groups(self):
        groups = self.driver.ex_list_security_groups()
        self.assertEqual(2, len(groups))
        self.assertEqual(groups[0]['name'], 'default')
        self.assertEqual(groups[1]['name'], 'mongodb')

    def test_ex_list_security_groups_no_securitygroup_key(self):
        CloudStackMockHttp.fixture_tag = 'no_groups'

        groups = self.driver.ex_list_security_groups()
        self.assertEqual(groups, [])

    def test_ex_create_security_group(self):
        group = self.driver.ex_create_security_group(name='MySG')
        self.assertEqual(group['name'], 'MySG')

    def test_ex_delete_security_group(self):
        res = self.driver.ex_delete_security_group(name='MySG')
        self.assertTrue(res)

    def test_ex_authorize_security_group_ingress(self):
        res = self.driver.ex_authorize_security_group_ingress('MySG',
                                                              'TCP',
                                                              '22',
                                                              '22',
                                                              '0.0.0.0/0')
        self.assertTrue(res)

    def test_ex_list_public_ips(self):
        ips = self.driver.ex_list_public_ips()
        self.assertEqual(ips[0].address, '1.1.1.116')

    def test_ex_allocate_public_ip(self):
        addr = self.driver.ex_allocate_public_ip()
        self.assertEqual(addr.address, '7.5.6.1')
        self.assertEqual(addr.id, '10987171-8cc9-4d0a-b98f-1698c09ddd2d')

    def test_ex_release_public_ip(self):
        addresses = self.driver.ex_list_public_ips()
        res = self.driver.ex_release_public_ip(addresses[0])
        self.assertTrue(res)

    def test_ex_create_port_forwarding_rule(self):
        node = self.driver.list_nodes()[0]
        address = self.driver.ex_list_public_ips()[0]
        private_port = 33
        private_end_port = 34
        public_port = 33
        public_end_port = 34
        openfirewall = True
        protocol = 'TCP'
        rule = self.driver.ex_create_port_forwarding_rule(node,
                                                          address,
                                                          private_port,
                                                          public_port,
                                                          protocol,
                                                          public_end_port,
                                                          private_end_port,
                                                          openfirewall)
        self.assertEqual(rule.address, address)
        self.assertEqual(rule.protocol, protocol)
        self.assertEqual(rule.public_port, public_port)
        self.assertEqual(rule.public_end_port, public_end_port)
        self.assertEqual(rule.private_port, private_port)
        self.assertEqual(rule.private_end_port, private_end_port)

    def test_ex_list_port_forwarding_rules(self):
        rules = self.driver.ex_list_port_forwarding_rules()
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        self.assertTrue(rule.node)
        self.assertEqual(rule.protocol, 'tcp')
        self.assertEqual(rule.public_port, '33')
        self.assertEqual(rule.public_end_port, '34')
        self.assertEqual(rule.private_port, '33')
        self.assertEqual(rule.private_end_port, '34')
        self.assertEqual(rule.address.address, '1.1.1.116')

    def test_ex_delete_port_forwarding_rule(self):
        node = self.driver.list_nodes()[0]
        rule = self.driver.ex_list_port_forwarding_rules()[0]
        res = self.driver.ex_delete_port_forwarding_rule(node, rule)
        self.assertTrue(res)

    def test_node_ex_delete_port_forwarding_rule(self):
        node = self.driver.list_nodes()[0]
        self.assertEqual(len(node.extra['port_forwarding_rules']), 1)
        node.extra['port_forwarding_rules'][0].delete()
        self.assertEqual(len(node.extra['port_forwarding_rules']), 0)

    def test_node_ex_create_port_forwarding_rule(self):
        node = self.driver.list_nodes()[0]
        self.assertEqual(len(node.extra['port_forwarding_rules']), 1)
        address = self.driver.ex_list_public_ips()[0]
        private_port = 33
        private_end_port = 34
        public_port = 33
        public_end_port = 34
        openfirewall = True
        protocol = 'TCP'
        rule = node.ex_create_port_forwarding_rule(address,
                                                   private_port,
                                                   public_port,
                                                   protocol,
                                                   public_end_port,
                                                   private_end_port,
                                                   openfirewall)
        self.assertEqual(rule.address, address)
        self.assertEqual(rule.protocol, protocol)
        self.assertEqual(rule.public_port, public_port)
        self.assertEqual(rule.public_end_port, public_end_port)
        self.assertEqual(rule.private_port, private_port)
        self.assertEqual(rule.private_end_port, private_end_port)
        self.assertEqual(len(node.extra['port_forwarding_rules']), 2)

    def test_ex_limits(self):
        limits = self.driver.ex_limits()
        self.assertEqual(limits['max_images'], 20)
        self.assertEqual(limits['max_networks'], 20)
        self.assertEqual(limits['max_public_ips'], -1)
        self.assertEqual(limits['max_vpc'], 20)
        self.assertEqual(limits['max_instances'], 20)
        self.assertEqual(limits['max_projects'], -1)
        self.assertEqual(limits['max_volumes'], 20)
        self.assertEqual(limits['max_snapshots'], 20)

    def test_ex_create_tags(self):
        node = self.driver.list_nodes()[0]
        tags = {'Region': 'Canada'}
        resp = self.driver.ex_create_tags([node.id], 'UserVm', tags)
        self.assertTrue(resp)

    def test_ex_delete_tags(self):
        node = self.driver.list_nodes()[0]
        tag_keys = ['Region']
        resp = self.driver.ex_delete_tags([node.id], 'UserVm', tag_keys)
        self.assertTrue(resp)


class CloudStackTestCase(CloudStackCommonTestCase, unittest.TestCase):
    def test_driver_instantiation(self):
        urls = [
            'http://api.exoscale.ch/compute1',  # http, default port
            'https://api.exoscale.ch/compute2',  # https, default port
            'http://api.exoscale.ch:8888/compute3',  # https, custom port
            'https://api.exoscale.ch:8787/compute4',  # https, custom port
            'https://api.test.com/compute/endpoint'  # https, default port
        ]

        expected_values = [
            {'host': 'api.exoscale.ch', 'port': 80, 'path': '/compute1'},
            {'host': 'api.exoscale.ch', 'port': 443, 'path': '/compute2'},
            {'host': 'api.exoscale.ch', 'port': 8888, 'path': '/compute3'},
            {'host': 'api.exoscale.ch', 'port': 8787, 'path': '/compute4'},
            {'host': 'api.test.com', 'port': 443, 'path': '/compute/endpoint'}
        ]

        cls = get_driver(Provider.CLOUDSTACK)

        for url, expected in zip(urls, expected_values):
            driver = cls('key', 'secret', url=url)

            self.assertEqual(driver.host, expected['host'])
            self.assertEqual(driver.path, expected['path'])
            self.assertEqual(driver.connection.port, expected['port'])

    def test_user_must_provide_host_and_path_or_url(self):
        expected_msg = ('When instantiating CloudStack driver directly '
                        'you also need to provide url or host and path '
                        'argument')
        cls = get_driver(Provider.CLOUDSTACK)

        self.assertRaisesRegexp(Exception, expected_msg, cls,
                                'key', 'secret')

        try:
            cls('key', 'secret', True, 'localhost', '/path')
        except Exception:
            self.fail('host and path provided but driver raised an exception')

        try:
            cls('key', 'secret', url='https://api.exoscale.ch/compute')
        except Exception:
            self.fail('url provided but driver raised an exception')


class CloudStackMockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('cloudstack')
    fixture_tag = 'default'

    def _load_fixture(self, fixture):
        body = self.fixtures.load(fixture)
        return body, json.loads(body)

    def _test_path_invalid_credentials(self, method, url, body, headers):
        body = ''
        return (httplib.UNAUTHORIZED, body, {},
                httplib.responses[httplib.UNAUTHORIZED])

    def _test_path_api_error(self, method, url, body, headers):
        body = self.fixtures.load('registerSSHKeyPair_error.json')
        return (431, body, {},
                httplib.responses[httplib.OK])

    def _test_path(self, method, url, body, headers):
        url = urlparse.urlparse(url)
        query = dict(parse_qsl(url.query))

        self.assertTrue('apiKey' in query)
        self.assertTrue('command' in query)
        self.assertTrue('response' in query)
        self.assertTrue('signature' in query)

        self.assertTrue(query['response'] == 'json')

        del query['apiKey']
        del query['response']
        del query['signature']
        command = query.pop('command')

        if hasattr(self, '_cmd_' + command):
            return getattr(self, '_cmd_' + command)(**query)
        else:
            fixture = command + '_' + self.fixture_tag + '.json'
            body, obj = self._load_fixture(fixture)
            return (httplib.OK, body, obj, httplib.responses[httplib.OK])

    def _cmd_queryAsyncJobResult(self, jobid):
        fixture = 'queryAsyncJobResult' + '_' + str(jobid) + '.json'
        body, obj = self._load_fixture(fixture)
        return (httplib.OK, body, obj, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
