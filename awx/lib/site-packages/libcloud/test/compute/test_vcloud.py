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

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from libcloud.utils.py3 import httplib, b

from libcloud.compute.drivers.vcloud import TerremarkDriver, VCloudNodeDriver, Subject
from libcloud.compute.drivers.vcloud import VCloud_1_5_NodeDriver, ControlAccess
from libcloud.compute.drivers.vcloud import VCloud_5_1_NodeDriver
from libcloud.compute.drivers.vcloud import Vdc
from libcloud.compute.base import Node, NodeImage
from libcloud.compute.types import NodeState

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures

from libcloud.test.secrets import VCLOUD_PARAMS


class TerremarkTests(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        VCloudNodeDriver.connectionCls.host = "test"
        VCloudNodeDriver.connectionCls.conn_classes = (None, TerremarkMockHttp)
        TerremarkMockHttp.type = None
        self.driver = TerremarkDriver(*VCLOUD_PARAMS)

    def test_list_images(self):
        ret = self.driver.list_images()
        self.assertEqual(
            ret[0].id, 'https://services.vcloudexpress.terremark.com/api/v0.8/vAppTemplate/5')

    def test_list_sizes(self):
        ret = self.driver.list_sizes()
        self.assertEqual(ret[0].ram, 512)

    def test_create_node(self):
        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(
            name='testerpart2',
            image=image,
            size=size,
            vdc='https://services.vcloudexpress.terremark.com/api/v0.8/vdc/224',
            network='https://services.vcloudexpress.terremark.com/api/v0.8/network/725',
            cpus=2,
        )
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(
            node.id, 'https://services.vcloudexpress.terremark.com/api/v0.8/vapp/14031')
        self.assertEqual(node.name, 'testerpart2')

    def test_list_nodes(self):
        ret = self.driver.list_nodes()
        node = ret[0]
        self.assertEqual(
            node.id, 'https://services.vcloudexpress.terremark.com/api/v0.8/vapp/14031')
        self.assertEqual(node.name, 'testerpart2')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.public_ips, [])
        self.assertEqual(node.private_ips, ['10.112.78.69'])

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        ret = self.driver.reboot_node(node)
        self.assertTrue(ret)

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)


class VCloud_1_5_Tests(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        VCloudNodeDriver.connectionCls.host = 'test'
        VCloudNodeDriver.connectionCls.conn_classes = (
            None, VCloud_1_5_MockHttp)
        VCloud_1_5_MockHttp.type = None
        self.driver = VCloud_1_5_NodeDriver(*VCLOUD_PARAMS)

    def test_list_images(self):
        ret = self.driver.list_images()
        self.assertEqual(
            'https://vm-vcloud/api/vAppTemplate/vappTemplate-ac1bc027-bf8c-4050-8643-4971f691c158', ret[0].id)

    def test_list_sizes(self):
        ret = self.driver.list_sizes()
        self.assertEqual(ret[0].ram, 512)

    def test_networks(self):
        ret = self.driver.networks
        self.assertEqual(
            ret[0].get('href'), 'https://vm-vcloud/api/network/dca8b667-6c8f-4c3e-be57-7a9425dba4f4')

    def test_create_node(self):
        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(
            name='testNode',
            image=image,
            size=size,
            ex_vdc='MyVdc',
            ex_network='vCloud - Default',
            cpus=2,
        )
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6a', node.id)
        self.assertEqual('testNode', node.name)

    def test_create_node_clone(self):
        image = self.driver.list_nodes()[0]
        node = self.driver.create_node(name='testNode', image=image)
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6a', node.id)
        self.assertEqual('testNode', node.name)

    def test_list_nodes(self):
        ret = self.driver.list_nodes()
        node = ret[0]
        self.assertEqual(
            node.id, 'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6a')
        self.assertEqual(node.name, 'testNode')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.public_ips, ['65.41.67.2'])
        self.assertEqual(node.private_ips, ['65.41.67.2'])
        self.assertEqual(node.extra, {'vdc': 'MyVdc',
                                      'vms': [{
                                          'id': 'https://vm-vcloud/api/vApp/vm-dd75d1d3-5b7b-48f0-aff3-69622ab7e045',
                                          'name': 'testVm',
                                          'state': NodeState.RUNNING,
                                          'public_ips': ['65.41.67.2'],
                                          'private_ips': ['65.41.67.2'],
                                          'os_type': 'rhel5_64Guest'
                                      }]})
        node = ret[1]
        self.assertEqual(
            node.id, 'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6b')
        self.assertEqual(node.name, 'testNode2')
        self.assertEqual(node.state, NodeState.RUNNING)
        self.assertEqual(node.public_ips, ['192.168.0.103'])
        self.assertEqual(node.private_ips, ['192.168.0.100'])
        self.assertEqual(node.extra, {'vdc': 'MyVdc',
                                      'vms': [{
                                          'id': 'https://vm-vcloud/api/vApp/vm-dd75d1d3-5b7b-48f0-aff3-69622ab7e046',
                                          'name': 'testVm2',
                                          'state': NodeState.RUNNING,
                                          'public_ips': ['192.168.0.103'],
                                          'private_ips': ['192.168.0.100'],
                                          'os_type': 'rhel5_64Guest'
                                      }]})

    def test_reboot_node(self):
        node = self.driver.list_nodes()[0]
        ret = self.driver.reboot_node(node)
        self.assertTrue(ret)

    def test_destroy_node(self):
        node = self.driver.list_nodes()[0]
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)

    def test_validate_vm_names(self):
        # valid inputs
        self.driver._validate_vm_names(['host-n-ame-name'])
        self.driver._validate_vm_names(['tc-mybuild-b1'])
        self.driver._validate_vm_names(None)
        # invalid inputs
        self.assertRaises(
            ValueError, self.driver._validate_vm_names, ['invalid.host'])
        self.assertRaises(
            ValueError, self.driver._validate_vm_names, ['inv-alid.host'])
        self.assertRaises(
            ValueError, self.driver._validate_vm_names, ['hostnametoooolong'])
        self.assertRaises(
            ValueError, self.driver._validate_vm_names, ['host$name'])

    def test_change_vm_names(self):
        self.driver._change_vm_names(
            '/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6a', ['changed1', 'changed2'])

    def test_is_node(self):
        self.assertTrue(self.driver._is_node(
            Node('testId', 'testNode', state=0, public_ips=[], private_ips=[], driver=self.driver)))
        self.assertFalse(self.driver._is_node(
            NodeImage('testId', 'testNode', driver=self.driver)))

    def test_ex_undeploy(self):
        node = self.driver.ex_undeploy_node(
            Node('https://test/api/vApp/undeployTest', 'testNode', state=0,
                 public_ips=[], private_ips=[], driver=self.driver))
        self.assertEqual(node.state, NodeState.STOPPED)

    def test_ex_undeploy_with_error(self):
        node = self.driver.ex_undeploy_node(
            Node('https://test/api/vApp/undeployErrorTest', 'testNode',
                 state=0, public_ips=[], private_ips=[], driver=self.driver))
        self.assertEqual(node.state, NodeState.STOPPED)

    def test_ex_find_node(self):
        node = self.driver.ex_find_node('testNode')
        self.assertEqual(node.name, "testNode")
        node = self.driver.ex_find_node('testNode', self.driver.vdcs[0])
        self.assertEqual(node.name, "testNode")
        node = self.driver.ex_find_node('testNonExisting', self.driver.vdcs[0])
        self.assertEqual(node, None)

    def test_ex_add_vm_disk__with_invalid_values(self):
        self.assertRaises(
            ValueError, self.driver.ex_add_vm_disk, 'dummy', 'invalid value')
        self.assertRaises(
            ValueError, self.driver.ex_add_vm_disk, 'dummy', '-1')

    def test_ex_add_vm_disk(self):
        self.driver.ex_add_vm_disk('https://test/api/vApp/vm-test', '20')

    def test_ex_set_vm_cpu__with_invalid_values(self):
        self.assertRaises(ValueError, self.driver.ex_set_vm_cpu, 'dummy', 50)
        self.assertRaises(ValueError, self.driver.ex_set_vm_cpu, 'dummy', -1)

    def test_ex_set_vm_cpu(self):
        self.driver.ex_set_vm_cpu('https://test/api/vApp/vm-test', 4)

    def test_ex_set_vm_memory__with_invalid_values(self):
        self.assertRaises(
            ValueError, self.driver.ex_set_vm_memory, 'dummy', 777)
        self.assertRaises(
            ValueError, self.driver.ex_set_vm_memory, 'dummy', -1024)

    def test_ex_set_vm_memory(self):
        self.driver.ex_set_vm_memory('https://test/api/vApp/vm-test', 1024)

    def test_vdcs(self):
        vdcs = self.driver.vdcs
        self.assertEqual(len(vdcs), 1)
        self.assertEqual(
            vdcs[0].id, 'https://vm-vcloud/api/vdc/3d9ae28c-1de9-4307-8107-9356ff8ba6d0')
        self.assertEqual(vdcs[0].name, 'MyVdc')
        self.assertEqual(vdcs[0].allocation_model, 'AllocationPool')
        self.assertEqual(vdcs[0].storage.limit, 5120000)
        self.assertEqual(vdcs[0].storage.used, 1984512)
        self.assertEqual(vdcs[0].storage.units, 'MB')
        self.assertEqual(vdcs[0].cpu.limit, 160000)
        self.assertEqual(vdcs[0].cpu.used, 0)
        self.assertEqual(vdcs[0].cpu.units, 'MHz')
        self.assertEqual(vdcs[0].memory.limit, 527360)
        self.assertEqual(vdcs[0].memory.used, 130752)
        self.assertEqual(vdcs[0].memory.units, 'MB')

    def test_ex_list_nodes(self):
        self.assertEqual(
            len(self.driver.ex_list_nodes()), len(self.driver.list_nodes()))

    def test_ex_list_nodes__masked_exception(self):
        """
        Test that we don't mask other exceptions.
        """
        brokenVdc = Vdc('/api/vdc/brokenVdc', 'brokenVdc', self.driver)
        self.assertRaises(AnotherError, self.driver.ex_list_nodes, (brokenVdc))

    def test_ex_power_off(self):
        node = Node(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6b',
            'testNode', NodeState.RUNNING, [], [], self.driver)
        self.driver.ex_power_off_node(node)

    def test_ex_query(self):
        results = self.driver.ex_query(
            'user', filter='name==jrambo', page=2, page_size=30, sort_desc='startDate')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'UserRecord')
        self.assertEqual(results[0]['name'], 'jrambo')
        self.assertEqual(results[0]['isLdapUser'], 'true')

    def test_ex_get_control_access(self):
        node = Node(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6b',
            'testNode', NodeState.RUNNING, [], [], self.driver)
        control_access = self.driver.ex_get_control_access(node)
        self.assertEqual(
            control_access.everyone_access_level, ControlAccess.AccessLevel.READ_ONLY)
        self.assertEqual(len(control_access.subjects), 1)
        self.assertEqual(control_access.subjects[0].type, 'group')
        self.assertEqual(control_access.subjects[0].name, 'MyGroup')
        self.assertEqual(control_access.subjects[
                         0].id, 'https://vm-vcloud/api/admin/group/b8202c48-7151-4e61-9a6c-155474c7d413')
        self.assertEqual(control_access.subjects[
                         0].access_level, ControlAccess.AccessLevel.FULL_CONTROL)

    def test_ex_set_control_access(self):
        node = Node(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6b',
            'testNode', NodeState.RUNNING, [], [], self.driver)
        control_access = ControlAccess(node, None, [Subject(
            name='MyGroup',
            type='group',
            access_level=ControlAccess.AccessLevel.FULL_CONTROL)])
        self.driver.ex_set_control_access(node, control_access)

    def test_ex_get_metadata(self):
        node = Node(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6b',
            'testNode', NodeState.RUNNING, [], [], self.driver)
        metadata = self.driver.ex_get_metadata(node)
        self.assertEqual(metadata, {'owners': 'msamia@netsuite.com'})

    def test_ex_set_metadata_entry(self):
        node = Node(
            'https://vm-vcloud/api/vApp/vapp-8c57a5b6-e61b-48ca-8a78-3b70ee65ef6b',
            'testNode', NodeState.RUNNING, [], [], self.driver)
        self.driver.ex_set_metadata_entry(node, 'foo', 'bar')


class VCloud_5_1_Tests(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        VCloudNodeDriver.connectionCls.host = 'test'
        VCloudNodeDriver.connectionCls.conn_classes = (
            None, VCloud_1_5_MockHttp)
        VCloud_1_5_MockHttp.type = None
        self.driver = VCloudNodeDriver(
            *VCLOUD_PARAMS, **{'api_version': '5.1'})

        self.assertTrue(isinstance(self.driver, VCloud_5_1_NodeDriver))

    def _test_create_node_valid_ex_vm_memory(self):
        # TODO: Hook up the fixture
        values = [4, 1024, 4096]

        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]

        for value in values:
            self.driver.create_node(
                name='testerpart2',
                image=image,
                size=size,
                vdc='https://services.vcloudexpress.terremark.com/api/v0.8/vdc/224',
                network='https://services.vcloudexpress.terremark.com/api/v0.8/network/725',
                cpus=2,
                ex_vm_memory=value
            )

    def test_create_node_invalid_ex_vm_memory(self):
        values = [1, 3, 7]

        image = self.driver.list_images()[0]
        size = self.driver.list_sizes()[0]

        for value in values:
            try:
                self.driver.create_node(
                    name='testerpart2',
                    image=image,
                    size=size,
                    vdc='https://services.vcloudexpress.terremark.com/api/v0.8/vdc/224',
                    network='https://services.vcloudexpress.terremark.com/api/v0.8/network/725',
                    cpus=2,
                    ex_vm_memory=value
                )
            except ValueError:
                pass
            else:
                self.fail('Exception was not thrown')

    def test_list_images(self):
        ret = self.driver.list_images()
        self.assertEqual(
            'https://vm-vcloud/api/vAppTemplate/vappTemplate-ac1bc027-bf8c-4050-8643-4971f691c158', ret[0].id)


class TerremarkMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('terremark')

    def _api_v0_8_login(self, method, url, body, headers):
        headers['set-cookie'] = 'vcloud-token=testtoken'
        body = self.fixtures.load('api_v0_8_login.xml')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_v0_8_org_240(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_org_240.xml')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_v0_8_vdc_224(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_vdc_224.xml')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_v0_8_vdc_224_catalog(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_vdc_224_catalog.xml')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_v0_8_catalogItem_5(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_catalogItem_5.xml')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_v0_8_vdc_224_action_instantiateVAppTemplate(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_v0_8_vdc_224_action_instantiateVAppTemplate.xml')
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _api_v0_8_vapp_14031_action_deploy(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_vapp_14031_action_deploy.xml')
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])

    def _api_v0_8_task_10496(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_task_10496.xml')
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])

    def _api_v0_8_vapp_14031_power_action_powerOn(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_v0_8_vapp_14031_power_action_powerOn.xml')
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])

    def _api_v0_8_vapp_14031(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('api_v0_8_vapp_14031_get.xml')
        elif method == 'DELETE':
            body = ''
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])

    def _api_v0_8_vapp_14031_power_action_reset(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_vapp_14031_power_action_reset.xml')
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])

    def _api_v0_8_vapp_14031_power_action_poweroff(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_v0_8_vapp_14031_power_action_poweroff.xml')
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])

    def _api_v0_8_task_11001(self, method, url, body, headers):
        body = self.fixtures.load('api_v0_8_task_11001.xml')
        return (httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED])


class AnotherErrorMember(Exception):

    """
    helper class for the synthetic exception
    """

    def __init__(self):
        self.tag = 'Error'

    def get(self, foo):
        return 'ACCESS_TO_RESOURCE_IS_FORBIDDEN_1'


class AnotherError(Exception):
    pass


class VCloud_1_5_MockHttp(MockHttp, unittest.TestCase):

    fixtures = ComputeFileFixtures('vcloud_1_5')

    def request(self, method, url, body=None, headers=None, raw=False):
        self.assertTrue(url.startswith('/api/'),
                        ('"%s" is invalid. Needs to '
                         'start with "/api". The passed URL should be just '
                         'the path, not full URL.', url))
        super(VCloud_1_5_MockHttp, self).request(method, url, body, headers,
                                                 raw)

    def _api_sessions(self, method, url, body, headers):
        headers['x-vcloud-authorization'] = 'testtoken'
        body = self.fixtures.load('api_sessions.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_org(self, method, url, body, headers):
        body = self.fixtures.load('api_org.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_org_96726c78_4ae3_402f_b08b_7a78c6903d2a(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_org_96726c78_4ae3_402f_b08b_7a78c6903d2a.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_network_dca8b667_6c8f_4c3e_be57_7a9425dba4f4(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_network_dca8b667_6c8f_4c3e_be57_7a9425dba4f4.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vdc_3d9ae28c_1de9_4307_8107_9356ff8ba6d0(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_vdc_3d9ae28c_1de9_4307_8107_9356ff8ba6d0.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vdc_brokenVdc(self, method, url, body, headers):
        body = self.fixtures.load('api_vdc_brokenVdc.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vapp_errorRaiser(self, method, url, body, headers):
        m = AnotherErrorMember()
        raise AnotherError(m)

    def _api_vdc_3d9ae28c_1de9_4307_8107_9356ff8ba6d0_action_instantiateVAppTemplate(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_vdc_3d9ae28c_1de9_4307_8107_9356ff8ba6d0_action_instantiateVAppTemplate.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a_power_action_powerOn(self, method, url, body, headers):
        return self._api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_power_action_all(method, url, body, headers)

    # Clone
    def _api_vdc_3d9ae28c_1de9_4307_8107_9356ff8ba6d0_action_cloneVApp(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_vdc_3d9ae28c_1de9_4307_8107_9356ff8ba6d0_action_cloneVApp.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_vApp_vm_dd75d1d3_5b7b_48f0_aff3_69622ab7e045_networkConnectionSection(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_task_b034df55_fe81_4798_bc81_1f0fd0ead450.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a(self, method, url, body, headers):
        status = httplib.OK
        if method == 'GET':
            body = self.fixtures.load(
                'api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a.xml')
            status = httplib.OK
        elif method == 'DELETE':
            body = self.fixtures.load(
                'api_task_b034df55_fe81_4798_bc81_1f0fd0ead450.xml')
            status = httplib.ACCEPTED
        return status, body, headers, httplib.responses[status]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6c(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6c.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vm_dd75d1d3_5b7b_48f0_aff3_69622ab7e045(self, method, url, body, headers):
        body = self.fixtures.load(
            'put_api_vApp_vm_dd75d1d3_5b7b_48f0_aff3_69622ab7e045_guestCustomizationSection.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_vApp_vm_dd75d1d3_5b7b_48f0_aff3_69622ab7e045_guestCustomizationSection(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'get_api_vApp_vm_dd75d1d3_5b7b_48f0_aff3_69622ab7e045_guestCustomizationSection.xml')
            status = httplib.OK
        else:
            body = self.fixtures.load(
                'put_api_vApp_vm_dd75d1d3_5b7b_48f0_aff3_69622ab7e045_guestCustomizationSection.xml')
            status = httplib.ACCEPTED
        return status, body, headers, httplib.responses[status]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a_power_action_reset(self, method, url, body, headers):
        return self._api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_power_action_all(method, url, body, headers)

    def _api_task_b034df55_fe81_4798_bc81_1f0fd0ead450(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_task_b034df55_fe81_4798_bc81_1f0fd0ead450.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_catalog_cddb3cb2_3394_4b14_b831_11fbc4028da4(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_catalog_cddb3cb2_3394_4b14_b831_11fbc4028da4.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_catalogItem_3132e037_759b_4627_9056_ca66466fa607(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_catalogItem_3132e037_759b_4627_9056_ca66466fa607.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_undeployTest(self, method, url, body, headers):
        body = self.fixtures.load('api_vApp_undeployTest.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_undeployTest_action_undeploy(self, method, url, body, headers):
        body = self.fixtures.load('api_task_undeploy.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_task_undeploy(self, method, url, body, headers):
        body = self.fixtures.load('api_task_undeploy.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_undeployErrorTest(self, method, url, body, headers):
        body = self.fixtures.load('api_vApp_undeployTest.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_undeployErrorTest_action_undeploy(self, method, url, body, headers):
        if b('shutdown') in b(body):
            body = self.fixtures.load('api_task_undeploy_error.xml')
        else:
            body = self.fixtures.load('api_task_undeploy.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_task_undeployError(self, method, url, body, headers):
        body = self.fixtures.load('api_task_undeploy_error.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vapp_access_to_resource_forbidden(self, method, url, body, headers):
        raise Exception(
            ET.fromstring(self.fixtures.load('api_vApp_vapp_access_to_resource_forbidden.xml')))

    def _api_vApp_vm_test(self, method, url, body, headers):
        body = self.fixtures.load('api_vApp_vm_test.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vm_test_virtualHardwareSection_disks(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'get_api_vApp_vm_test_virtualHardwareSection_disks.xml')
            status = httplib.OK
        else:
            body = self.fixtures.load(
                'put_api_vApp_vm_test_virtualHardwareSection_disks.xml')
            status = httplib.ACCEPTED
        return status, body, headers, httplib.responses[status]

    def _api_vApp_vm_test_virtualHardwareSection_cpu(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'get_api_vApp_vm_test_virtualHardwareSection_cpu.xml')
            status = httplib.OK
        else:
            body = self.fixtures.load(
                'put_api_vApp_vm_test_virtualHardwareSection_cpu.xml')
            status = httplib.ACCEPTED
        return status, body, headers, httplib.responses[status]

    def _api_vApp_vm_test_virtualHardwareSection_memory(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load(
                'get_api_vApp_vm_test_virtualHardwareSection_memory.xml')
            status = httplib.OK
        else:
            body = self.fixtures.load(
                'put_api_vApp_vm_test_virtualHardwareSection_memory.xml')
            status = httplib.ACCEPTED
        return status, body, headers, httplib.responses[status]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_power_action_powerOff(self, method, url, body, headers):
        return self._api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_power_action_all(method, url, body, headers)

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_power_action_all(self, method, url, body, headers):
        assert method == 'POST'
        body = self.fixtures.load(
            'api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a_power_action_all.xml')
        return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]

    def _api_query(self, method, url, body, headers):
        assert method == 'GET'
        if 'type=user' in url:
            self.assertTrue('page=2' in url)
            self.assertTrue('filter=(name==jrambo)' in url)
            self.assertTrue('sortDesc=startDate')
            body = self.fixtures.load('api_query_user.xml')
        elif 'type=group' in url:
            body = self.fixtures.load('api_query_group.xml')
        else:
            raise AssertionError('Unexpected query type')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_metadata(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('api_vapp_post_metadata.xml')
            return httplib.ACCEPTED, body, headers, httplib.responses[httplib.ACCEPTED]
        else:
            body = self.fixtures.load('api_vapp_get_metadata.xml')
            return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_controlAccess(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a_controlAccess.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6b_action_controlAccess(self, method, url, body, headers):
        body = str(body)
        self.assertTrue(method == 'POST')
        self.assertTrue(
            '<IsSharedToEveryone>false</IsSharedToEveryone>' in body)
        self.assertTrue(
            '<Subject href="https://vm-vcloud/api/admin/group/b8202c48-7151-4e61-9a6c-155474c7d413" />' in body)
        self.assertTrue('<AccessLevel>FullControl</AccessLevel>' in body)
        body = self.fixtures.load(
            'api_vApp_vapp_8c57a5b6_e61b_48ca_8a78_3b70ee65ef6a_controlAccess.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]

    def _api_admin_group_b8202c48_7151_4e61_9a6c_155474c7d413(self, method, url, body, headers):
        body = self.fixtures.load(
            'api_admin_group_b8202c48_7151_4e61_9a6c_155474c7d413.xml')
        return httplib.OK, body, headers, httplib.responses[httplib.OK]


if __name__ == '__main__':
    sys.exit(unittest.main())
