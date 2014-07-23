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

try:
    import simplejson as json
except:
    import json

from libcloud.utils.py3 import httplib

from libcloud.common.types import InvalidCredsError
from libcloud.compute.drivers.cloudsigma import CloudSigmaNodeDriver
from libcloud.compute.drivers.cloudsigma import CloudSigma_2_0_NodeDriver
from libcloud.compute.drivers.cloudsigma import CloudSigmaError
from libcloud.compute.types import NodeState

from libcloud.test import unittest
from libcloud.test import MockHttpTestCase
from libcloud.test.file_fixtures import ComputeFileFixtures


class CloudSigmaAPI20BaseTestCase(object):
    def setUp(self):
        self.driver_klass.connectionCls.conn_classes = \
            (CloudSigmaMockHttp, CloudSigmaMockHttp)

        CloudSigmaMockHttp.type = None
        CloudSigmaMockHttp.use_param = 'do'

        self.driver = self.driver_klass(*self.driver_args,
                                        **self.driver_kwargs)
        self.driver.DRIVE_TRANSITION_SLEEP_INTERVAL = 0.1
        self.driver.DRIVE_TRANSITION_TIMEOUT = 1
        self.node = self.driver.list_nodes()[0]

    def test_invalid_api_versions(self):
        expected_msg = 'Unsupported API version: invalid'
        self.assertRaisesRegexp(NotImplementedError, expected_msg,
                                CloudSigmaNodeDriver, 'username', 'password',
                                api_version='invalid')

    def test_invalid_credentials(self):
        CloudSigmaMockHttp.type = 'INVALID_CREDS'
        self.assertRaises(InvalidCredsError, self.driver.list_nodes)

    def test_invalid_region(self):
        expected_msg = 'Invalid region:'
        self.assertRaisesRegexp(ValueError, expected_msg,
                                CloudSigma_2_0_NodeDriver, 'foo', 'bar',
                                region='invalid')

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()

        size = sizes[0]
        self.assertEqual(size.id, 'micro-regular')

    def test_list_images(self):
        images = self.driver.list_images()

        image = images[0]
        self.assertEqual(image.name, 'ubuntu-10.04-toMP')
        self.assertEqual(image.extra['image_type'], 'preinst')
        self.assertEqual(image.extra['media'], 'disk')
        self.assertEqual(image.extra['os'], 'linux')

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()

        node = nodes[0]
        self.assertEqual(len(nodes), 2)
        self.assertEqual(node.id, '9de75ed6-fd33-45e2-963f-d405f31fd911')
        self.assertEqual(node.name, 'test no drives')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.public_ips, ['185.12.5.181', '178.22.68.55'])
        self.assertEqual(node.private_ips, [])

    def test_create_node(self):
        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]
        metadata = {'foo': 'bar'}

        node = self.driver.create_node(name='test node', size=size, image=image,
                                       ex_metadata=metadata)
        self.assertEqual(node.name, 'test node')
        self.assertEqual(len(node.extra['nics']), 1)
        self.assertEqual(node.extra['nics'][0]['ip_v4_conf']['conf'], 'dhcp')

    def test_create_node_with_vlan(self):
        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]

        vlan_uuid = '39ae851d-433f-4ac2-a803-ffa24cb1fa3e'

        node = self.driver.create_node(name='test node vlan', size=size,
                                       image=image, ex_vlan=vlan_uuid)
        self.assertEqual(node.name, 'test node vlan')
        self.assertEqual(len(node.extra['nics']), 2)
        self.assertEqual(node.extra['nics'][0]['ip_v4_conf']['conf'], 'dhcp')
        self.assertEqual(node.extra['nics'][1]['vlan']['uuid'], vlan_uuid)

    def test_destroy_node(self):
        status = self.driver.destroy_node(node=self.node)
        self.assertTrue(status)

    def test_ex_start_node(self):
        status = self.driver.ex_start_node(node=self.node)
        self.assertTrue(status)

    def test_ex_start_node_avoid_mode(self):
        CloudSigmaMockHttp.type = 'AVOID_MODE'
        ex_avoid = ['1', '2']
        status = self.driver.ex_start_node(node=self.node,
                                           ex_avoid=ex_avoid)
        self.assertTrue(status)

    def test_ex_start_node_already_started(self):
        CloudSigmaMockHttp.type = 'ALREADY_STARTED'

        expected_msg = 'Cannot start guest in state "started". Guest should ' \
                       'be in state "stopped'

        self.assertRaisesRegexp(CloudSigmaError, expected_msg,
                                self.driver.ex_start_node, node=self.node)

    def test_ex_stop_node(self):
        status = self.driver.ex_stop_node(node=self.node)
        self.assertTrue(status)

    def test_ex_stop_node_already_stopped(self):
        CloudSigmaMockHttp.type = 'ALREADY_STOPPED'

        expected_msg = 'Cannot stop guest in state "stopped"'
        self.assertRaisesRegexp(CloudSigmaError, expected_msg,
                                self.driver.ex_stop_node, node=self.node)

    def test_ex_clone_node(self):
        node_to_clone = self.driver.list_nodes()[0]

        cloned_node = self.driver.ex_clone_node(node=node_to_clone,
                                                name='test cloned node')
        self.assertEqual(cloned_node.name, 'test cloned node')

    def test_ex_open_vnc_tunnel(self):
        node = self.driver.list_nodes()[0]
        vnc_url = self.driver.ex_open_vnc_tunnel(node=node)
        self.assertEqual(vnc_url, 'vnc://direct.lvs.cloudsigma.com:41111')

    def test_ex_close_vnc_tunnel(self):
        node = self.driver.list_nodes()[0]
        status = self.driver.ex_close_vnc_tunnel(node=node)
        self.assertTrue(status)

    def test_ex_list_library_drives(self):
        drives = self.driver.ex_list_library_drives()

        drive = drives[0]
        self.assertEqual(drive.name, 'IPCop 2.0.2')
        self.assertEqual(drive.size, 1000000000)
        self.assertEqual(drive.media, 'cdrom')
        self.assertEqual(drive.status, 'unmounted')

    def test_ex_list_user_drives(self):
        drives = self.driver.ex_list_user_drives()

        drive = drives[0]
        self.assertEqual(drive.name, 'test node 2-drive')
        self.assertEqual(drive.size, 13958643712)
        self.assertEqual(drive.media, 'disk')
        self.assertEqual(drive.status, 'unmounted')

    def test_ex_create_drive(self):
        CloudSigmaMockHttp.type = 'CREATE'

        name = 'test drive 5'
        size = 2000 * 1024 * 1024

        drive = self.driver.ex_create_drive(name=name, size=size, media='disk')
        self.assertEqual(drive.name, 'test drive 5')
        self.assertEqual(drive.media, 'disk')

    def test_ex_clone_drive(self):
        drive = self.driver.ex_list_user_drives()[0]
        cloned_drive = self.driver.ex_clone_drive(drive=drive,
                                                  name='cloned drive')

        self.assertEqual(cloned_drive.name, 'cloned drive')

    def test_ex_resize_drive(self):
        drive = self.driver.ex_list_user_drives()[0]

        size = 1111 * 1024 * 1024

        resized_drive = self.driver.ex_resize_drive(drive=drive, size=size)
        self.assertEqual(resized_drive.name, 'test drive 5')
        self.assertEqual(resized_drive.media, 'disk')
        self.assertEqual(resized_drive.size, size)

    def test_ex_list_firewall_policies(self):
        policies = self.driver.ex_list_firewall_policies()

        policy = policies[1]
        rule = policy.rules[0]
        self.assertEqual(policy.name, 'My awesome policy')
        self.assertEqual(rule.action, 'drop')
        self.assertEqual(rule.direction, 'out')
        self.assertEqual(rule.dst_ip, '23.0.0.0/32')
        self.assertEqual(rule.ip_proto, 'tcp')
        self.assertEqual(rule.dst_port, None)
        self.assertEqual(rule.src_ip, None)
        self.assertEqual(rule.src_port, None)
        self.assertEqual(rule.comment, 'Drop traffic from the VM to IP address 23.0.0.0/32')

    def test_ex_create_firewall_policy_no_rules(self):
        CloudSigmaMockHttp.type = 'CREATE_NO_RULES'
        policy = self.driver.ex_create_firewall_policy(name='test policy 1')

        self.assertEqual(policy.name, 'test policy 1')
        self.assertEqual(policy.rules, [])

    def test_ex_create_firewall_policy_with_rules(self):
        CloudSigmaMockHttp.type = 'CREATE_WITH_RULES'
        rules = [
            {
                'action': 'accept',
                'direction': 'out',
                'ip_proto': 'tcp',
                'src_ip': '127.0.0.1',
                'dst_ip': '127.0.0.1'
            }
        ]

        policy = self.driver.ex_create_firewall_policy(name='test policy 2',
                                                       rules=rules)
        rule = policy.rules[0]

        self.assertEqual(policy.name, 'test policy 2')
        self.assertEqual(len(policy.rules), 1)

        self.assertEqual(rule.action, 'accept')
        self.assertEqual(rule.direction, 'out')
        self.assertEqual(rule.ip_proto, 'tcp')

    def test_ex_attach_firewall_policy(self):
        policy = self.driver.ex_list_firewall_policies()[0]
        node = self.driver.list_nodes()[0]

        CloudSigmaMockHttp.type = 'ATTACH_POLICY'
        updated_node = self.driver.ex_attach_firewall_policy(policy=policy,
                                                             node=node)
        nic = updated_node.extra['nics'][0]
        self.assertEqual(nic['firewall_policy']['uuid'],
                         '461dfb8c-e641-43d7-a20e-32e2aa399086')

    def test_ex_attach_firewall_policy_inexistent_nic(self):
        policy = self.driver.ex_list_firewall_policies()[0]
        node = self.driver.list_nodes()[0]

        nic_mac = 'inexistent'
        expected_msg = 'Cannot find the NIC interface to attach a policy to'
        self.assertRaisesRegexp(ValueError, expected_msg,
                                self.driver.ex_attach_firewall_policy,
                                policy=policy,
                                node=node,
                                nic_mac=nic_mac)

    def test_ex_delete_firewall_policy(self):
        policy = self.driver.ex_list_firewall_policies()[0]
        status = self.driver.ex_delete_firewall_policy(policy=policy)
        self.assertTrue(status)

    def test_ex_list_tags(self):
        tags = self.driver.ex_list_tags()

        tag = tags[0]
        self.assertEqual(tag.id, 'a010ec41-2ead-4630-a1d0-237fa77e4d4d')
        self.assertEqual(tag.name, 'test tag 2')

    def test_ex_get_tag(self):
        tag = self.driver.ex_get_tag(tag_id='a010ec41-2ead-4630-a1d0-237fa77e4d4d')

        self.assertEqual(tag.id, 'a010ec41-2ead-4630-a1d0-237fa77e4d4d')
        self.assertEqual(tag.name, 'test tag 2')

    def test_ex_create_tag(self):
        tag = self.driver.ex_create_tag(name='test tag 3')
        self.assertEqual(tag.name, 'test tag 3')

    def test_ex_create_tag_with_resources(self):
        CloudSigmaMockHttp.type = 'WITH_RESOURCES'
        resource_uuids = ['1']
        tag = self.driver.ex_create_tag(name='test tag 3',
                                        resource_uuids=resource_uuids)
        self.assertEqual(tag.name, 'test tag 3')
        self.assertEqual(tag.resources, resource_uuids)

    def test_ex_tag_resource(self):
        node = self.driver.list_nodes()[0]
        tag = self.driver.ex_list_tags()[0]

        updated_tag = self.driver.ex_tag_resource(resource=node, tag=tag)
        self.assertEqual(updated_tag.name, 'test tag 3')

    def test_ex_tag_resources(self):
        nodes = self.driver.list_nodes()
        tag = self.driver.ex_list_tags()[0]

        updated_tag = self.driver.ex_tag_resources(resources=nodes, tag=tag)
        self.assertEqual(updated_tag.name, 'test tag 3')

    def test_ex_tag_resource_invalid_resource_object(self):
        tag = self.driver.ex_list_tags()[0]

        expected_msg = 'Resource doesn\'t have id attribute'
        self.assertRaisesRegexp(ValueError, expected_msg,
                                self.driver.ex_tag_resource, tag=tag,
                                resource={})

    def test_ex_delete_tag(self):
        tag = self.driver.ex_list_tags()[0]
        status = self.driver.ex_delete_tag(tag=tag)
        self.assertTrue(status)

    def test_ex_get_balance(self):
        balance = self.driver.ex_get_balance()
        self.assertEqual(balance['balance'], '10.00')
        self.assertEqual(balance['currency'], 'USD')

    def test_ex_get_pricing(self):
        pricing = self.driver.ex_get_pricing()

        self.assertTrue('current' in pricing)
        self.assertTrue('next' in pricing)
        self.assertTrue('objects' in pricing)

    def test_ex_get_usage(self):
        pricing = self.driver.ex_get_usage()

        self.assertTrue('balance' in pricing)
        self.assertTrue('usage' in pricing)

    def test_ex_list_subscriptions(self):
        subscriptions = self.driver.ex_list_subscriptions()

        subscription = subscriptions[0]
        self.assertEqual(len(subscriptions), 5)
        self.assertEqual(subscription.id, '7272')
        self.assertEqual(subscription.resource, 'vlan')
        self.assertEqual(subscription.amount, 1)
        self.assertEqual(subscription.period, '345 days, 0:00:00')
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(subscription.price, '0E-20')

    def test_ex_create_subscription(self):
        CloudSigmaMockHttp.type = 'CREATE_SUBSCRIPTION'
        subscription = self.driver.ex_create_subscription(amount=1,
                                                          period='1 month',
                                                          resource='vlan')
        self.assertEqual(subscription.amount, 1)
        self.assertEqual(subscription.period, '1 month')
        self.assertEqual(subscription.resource, 'vlan')
        self.assertEqual(subscription.price, '10.26666666666666666666666667')
        self.assertEqual(subscription.auto_renew, False)
        self.assertEqual(subscription.subscribed_object, '2494079f-8376-40bf-9b37-34d633b8a7b7')

    def test_ex_list_subscriptions_status_filterting(self):
        CloudSigmaMockHttp.type = 'STATUS_FILTER'
        self.driver.ex_list_subscriptions(status='active')

    def test_ex_list_subscriptions_resource_filterting(self):
        CloudSigmaMockHttp.type = 'RESOURCE_FILTER'
        resources = ['cpu', 'mem']
        self.driver.ex_list_subscriptions(resources=resources)

    def test_ex_toggle_subscription_auto_renew(self):
        subscription = self.driver.ex_list_subscriptions()[0]
        status = self.driver.ex_toggle_subscription_auto_renew(
            subscription=subscription)
        self.assertTrue(status)

    def test_ex_list_capabilities(self):
        capabilities = self.driver.ex_list_capabilities()
        self.assertEqual(capabilities['servers']['cpu']['min'], 250)

    def test_ex_list_servers_availability_groups(self):
        groups = self.driver.ex_list_servers_availability_groups()
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[0]), 2)
        self.assertEqual(len(groups[2]), 1)

    def test_ex_list_drives_availability_groups(self):
        groups = self.driver.ex_list_drives_availability_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 11)

    def test_wait_for_drive_state_transition_timeout(self):
        drive = self.driver.ex_list_user_drives()[0]
        state = 'timeout'

        expected_msg = 'Timed out while waiting for drive transition'
        self.assertRaisesRegexp(Exception, expected_msg,
                                self.driver._wait_for_drive_state_transition,
                                drive=drive, state=state,
                                timeout=0.5)

    def test_wait_for_drive_state_transition_success(self):
        drive = self.driver.ex_list_user_drives()[0]
        state = 'unmounted'

        drive = self.driver._wait_for_drive_state_transition(drive=drive,
                                                             state=state,
                                                             timeout=0.5)
        self.assertEqual(drive.status, state)


class CloudSigmaAPI20DirectTestCase(CloudSigmaAPI20BaseTestCase,
                                    unittest.TestCase):
    driver_klass = CloudSigma_2_0_NodeDriver
    driver_args = ('foo', 'bar')
    driver_kwargs = {}


class CloudSigmaAPI20IndirectTestCase(CloudSigmaAPI20BaseTestCase,
                                      unittest.TestCase):
    driver_klass = CloudSigmaNodeDriver
    driver_args = ('foo', 'bar')
    driver_kwargs = {'api_version': '2.0'}


class CloudSigmaMockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('cloudsigma_2_0')

    def _api_2_0_servers_detail_INVALID_CREDS(self, method, url, body, headers):
        body = self.fixtures.load('libdrives.json')
        return (httplib.UNAUTHORIZED, body, {},
                httplib.responses[httplib.UNAUTHORIZED])

    def _api_2_0_libdrives(self, method, url, body, headers):
        body = self.fixtures.load('libdrives.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_servers_detail(self, method, url, body, headers):
        body = self.fixtures.load('servers_detail_mixed_state.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911(self, method, url, body, headers):
        body = ''
        return (httplib.NO_CONTENT, body, {}, httplib.responses[httplib.NO_CONTENT])

    def _api_2_0_servers(self, method, url, body, headers):
        if method == 'POST':
            # create_node

            parsed = json.loads(body)

            if 'vlan' in parsed['name']:
                self.assertEqual(len(parsed['nics']), 2)
                body = self.fixtures.load('servers_create_with_vlan.json')
            else:
                body = self.fixtures.load('servers_create.json')

            return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_start(self, method, url, body, headers):
        body = self.fixtures.load('start_success.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_AVOID_MODE_start(self, method, url, body, headers):
        self.assertUrlContainsQueryParams(url, {'avoid': '1,2'})

        body = self.fixtures.load('start_success.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_ALREADY_STARTED_start(self, method, url, body, headers):
        body = self.fixtures.load('start_already_started.json')
        return (httplib.FORBIDDEN, body, {}, httplib.responses[httplib.FORBIDDEN])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_stop(self, method, url, body, headers):
        body = self.fixtures.load('stop_success.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_ALREADY_STOPPED_stop(self, method, url, body, headers):
        body = self.fixtures.load('stop_already_stopped.json')
        return (httplib.FORBIDDEN, body, {}, httplib.responses[httplib.FORBIDDEN])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_clone(self, method, url, body, headers):
        body = self.fixtures.load('servers_clone.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_open_vnc(self, method, url, body, headers):
        body = self.fixtures.load('servers_open_vnc.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_action_close_vnc(self, method, url, body, headers):
        body = self.fixtures.load('servers_close_vnc.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_drives_detail(self, method, url, body, headers):
        body = self.fixtures.load('drives_detail.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_drives_b02311e2_a83c_4c12_af10_b30d51c86913(self, method, url, body, headers):
        body = self.fixtures.load('drives_get.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_drives_9d1d2cf3_08c1_462f_8485_f4b073560809(self, method, url, body, headers):
        body = self.fixtures.load('drives_get.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_drives_CREATE(self, method, url, body, headers):
        body = self.fixtures.load('drives_create.json')
        return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_drives_9d1d2cf3_08c1_462f_8485_f4b073560809_action_clone(self, method, url, body, headers):
        body = self.fixtures.load('drives_clone.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_drives_5236b9ee_f735_42fd_a236_17558f9e12d3_action_clone(self, method, url, body, headers):
        body = self.fixtures.load('drives_clone.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_drives_b02311e2_a83c_4c12_af10_b30d51c86913_action_resize(self, method, url, body, headers):
        body = self.fixtures.load('drives_resize.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_drives_9d1d2cf3_08c1_462f_8485_f4b073560809_action_resize(self, method, url, body, headers):
        body = self.fixtures.load('drives_resize.json')
        return (httplib.ACCEPTED, body, {}, httplib.responses[httplib.ACCEPTED])

    def _api_2_0_fwpolicies_detail(self, method, url, body, headers):
        body = self.fixtures.load('fwpolicies_detail.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_fwpolicies_CREATE_NO_RULES(self, method, url, body, headers):
        body = self.fixtures.load('fwpolicies_create_no_rules.json')
        return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_fwpolicies_CREATE_WITH_RULES(self, method, url, body, headers):
        body = self.fixtures.load('fwpolicies_create_with_rules.json')
        return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_servers_9de75ed6_fd33_45e2_963f_d405f31fd911_ATTACH_POLICY(self, method, url, body, headers):
        body = self.fixtures.load('servers_attach_policy.json')
        return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_fwpolicies_0e339282_0cb5_41ac_a9db_727fb62ff2dc(self, method, url, body, headers):
        if method == 'DELETE':
            body = ''
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _api_2_0_tags_detail(self, method, url, body, headers):
        body = self.fixtures.load('tags_detail.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_tags(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('tags_create.json')
            return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_tags_WITH_RESOURCES(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('tags_create_with_resources.json')
            return (httplib.CREATED, body, {}, httplib.responses[httplib.CREATED])

    def _api_2_0_tags_a010ec41_2ead_4630_a1d0_237fa77e4d4d(self, method, url, body, headers):
        if method == 'GET':
            # ex_get_tag
            body = self.fixtures.load('tags_get.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == 'PUT':
            # ex_tag_resource
            body = self.fixtures.load('tags_update.json')
            return (httplib.OK, body, {}, httplib.responses[httplib.OK])
        elif method == 'DELETE':
            # ex_delete_tag
            body = ''
            return (httplib.NO_CONTENT, body, {},
                    httplib.responses[httplib.NO_CONTENT])

    def _api_2_0_balance(self, method, url, body, headers):
        body = self.fixtures.load('balance.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_pricing(self, method, url, body, headers):
        body = self.fixtures.load('pricing.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_currentusage(self, method, url, body, headers):
        body = self.fixtures.load('currentusage.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_subscriptions(self, method, url, body, headers):
        body = self.fixtures.load('subscriptions.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_subscriptions_STATUS_FILTER(self, method, url, body, headers):
        self.assertUrlContainsQueryParams(url, {'status': 'active'})

        body = self.fixtures.load('subscriptions.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_subscriptions_RESOURCE_FILTER(self, method, url, body, headers):
        expected_params = {'resource': 'cpu,mem', 'status': 'all'}
        self.assertUrlContainsQueryParams(url, expected_params)

        body = self.fixtures.load('subscriptions.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_subscriptions_7272_action_auto_renew(self, method, url, body, headers):
        body = ''
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_subscriptions_CREATE_SUBSCRIPTION(self, method, url, body, headers):
        body = self.fixtures.load('create_subscription.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_capabilities(self, method, url, body, headers):
        body = self.fixtures.load('capabilities.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_servers_availability_groups(self, method, url, body, headers):
        body = self.fixtures.load('servers_avail_groups.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_2_0_drives_availability_groups(self, method, url, body, headers):
        body = self.fixtures.load('drives_avail_groups.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())
