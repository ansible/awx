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
"""
Abiquo Test Suite
"""
import unittest
import sys

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.abiquo import AbiquoNodeDriver
from libcloud.common.abiquo import ForbiddenError, get_href
from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.compute.base import NodeLocation, NodeImage
from libcloud.test.compute import TestCaseMixin
from libcloud.test import MockHttpTestCase
from libcloud.test.file_fixtures import ComputeFileFixtures


class AbiquoNodeDriverTest(unittest.TestCase, TestCaseMixin):

    """
    Abiquo Node Driver test suite
    """

    def setUp(self):
        """
        Set up the driver with the main user
        """
        AbiquoNodeDriver.connectionCls.conn_classes = (AbiquoMockHttp, None)
        self.driver = AbiquoNodeDriver('son', 'goku',
                                       'http://dummy.host.com/api')

    def test_unauthorized_controlled(self):
        """
        Test the Unauthorized Exception is Controlled.

        Test, through the 'login' method, that a '401 Unauthorized'
        raises a 'InvalidCredsError' instead of the 'MalformedUrlException'
        """
        self.assertRaises(InvalidCredsError, AbiquoNodeDriver, 'son',
                          'goten', 'http://dummy.host.com/api')

    def test_forbidden_controlled(self):
        """
        Test the Forbidden Exception is Controlled.

        Test, through the 'list_images' method, that a '403 Forbidden'
        raises an 'ForbidenError' instead of the 'MalformedUrlException'
        """
        AbiquoNodeDriver.connectionCls.conn_classes = (AbiquoMockHttp, None)
        conn = AbiquoNodeDriver('son', 'gohan', 'http://dummy.host.com/api')
        self.assertRaises(ForbiddenError, conn.list_images)

    def test_handle_other_errors_such_as_not_found(self):
        """
        Test common 'logical' exceptions are controlled.

        Test that common exception (normally 404-Not Found and 409-Conflict),
        that return an XMLResponse with the explanation of the errors are
        controlled.
        """
        self.driver = AbiquoNodeDriver('go', 'trunks',
                                       'http://dummy.host.com/api')
        self.assertRaises(LibcloudError, self.driver.list_images)

    def test_ex_create_and_delete_empty_group(self):
        """
        Test the creation and deletion of an empty group.
        """
        group = self.driver.ex_create_group('libcloud_test_group')
        group.destroy()

    def test_create_node_no_image_raise_exception(self):
        """
        Test 'create_node' without image.

        Test the 'create_node' function without 'image' parameter raises
        an Exception
        """
        self.assertRaises(LibcloudError, self.driver.create_node)

    def test_create_node_specify_location(self):
        """
        Test you can create a node specifying the location.
        """
        image = self.driver.list_images()[0]
        location = self.driver.list_locations()[0]
        self.driver.create_node(image=image, location=location)

    def test_create_node_specify_wrong_location(self):
        """
        Test you can not create a node with wrong location.
        """
        image = self.driver.list_images()[0]
        location = NodeLocation(435, 'fake-location', 'Spain', self.driver)
        self.assertRaises(LibcloudError, self.driver.create_node, image=image,
                          location=location)

    def test_create_node_specify_wrong_image(self):
        """
        Test image compatibility.

        Some locations only can handle a group of images, not all of them.
        Test you can not create a node with incompatible image-location.
        """
        # Create fake NodeImage
        image = NodeImage(3234, 'dummy-image', self.driver)
        location = self.driver.list_locations()[0]
        # With this image, it should raise an Exception
        self.assertRaises(LibcloudError, self.driver.create_node, image=image,
                          location=location)

    def test_create_node_specify_group_name(self):
        """
        Test 'create_node' into a concrete group.
        """
        image = self.driver.list_images()[0]
        self.driver.create_node(image=image, group_name='new_group_name')

    def test_create_group_location_does_not_exist(self):
        """
        Test 'create_node' with an unexistent location.

        Defines a 'fake' location and tries to create a node into it.
        """
        location = NodeLocation(435, 'fake-location', 'Spain', self.driver)
        # With this location, it should raise an Exception
        self.assertRaises(LibcloudError, self.driver.ex_create_group,
                          name='new_group_name',
                          location=location)

    def test_destroy_node_response(self):
        """
        'destroy_node' basic test.

        Override the destroy to return a different node available
        to be undeployed. (by default it returns an already undeployed node,
        for test creation).
        """
        self.driver = AbiquoNodeDriver('go', 'trunks',
                                       'http://dummy.host.com/api')
        node = self.driver.list_nodes()[0]
        ret = self.driver.destroy_node(node)
        self.assertTrue(ret)

    def test_destroy_node_response_failed(self):
        """
        'destroy_node' asynchronous error.

        Test that the driver handles correctly when, for some reason,
        the 'destroy' job fails.
        """
        self.driver = AbiquoNodeDriver('muten', 'roshi',
                                       'http://dummy.host.com/api')
        node = self.driver.list_nodes()[0]
        ret = self.driver.destroy_node(node)
        self.assertFalse(ret)

    def test_destroy_node_allocation_state(self):
        """
        Test the 'destroy_node' invalid state.

        Try to destroy a node when the node is not running.
        """
        self.driver = AbiquoNodeDriver('ve', 'geta',
                                       'http://dummy.host.com/api')
        # Override the destroy to return a different node available to be
        # undeployed
        node = self.driver.list_nodes()[0]
        # The mock class with the user:password 've:geta' returns a node that
        # is in 'ALLOCATION' state and hence, the 'destroy_node' method should
        # raise a LibcloudError
        self.assertRaises(LibcloudError, self.driver.destroy_node, node)

    def test_destroy_not_deployed_group(self):
        """
        Test 'ex_destroy_group' when group is not deployed.
        """
        location = self.driver.list_locations()[0]
        group = self.driver.ex_list_groups(location)[1]
        self.assertTrue(group.destroy())

    def test_destroy_deployed_group(self):
        """
        Test 'ex_destroy_group' when there are machines running.
        """
        location = self.driver.list_locations()[0]
        group = self.driver.ex_list_groups(location)[0]
        self.assertTrue(group.destroy())

    def test_destroy_deployed_group_failed(self):
        """
        Test 'ex_destroy_group' fails.

        Test driver handles correctly when, for some reason, the
        asynchronous job fails.
        """
        self.driver = AbiquoNodeDriver('muten', 'roshi',
                                       'http://dummy.host.com/api')
        location = self.driver.list_locations()[0]
        group = self.driver.ex_list_groups(location)[0]
        self.assertFalse(group.destroy())

    def test_destroy_group_invalid_state(self):
        """
        Test 'ex_destroy_group' invalid state.

        Test the Driver raises an exception when the group is in
        invalid temporal state.
        """
        self.driver = AbiquoNodeDriver('ve', 'geta',
                                       'http://dummy.host.com/api')
        location = self.driver.list_locations()[0]
        group = self.driver.ex_list_groups(location)[1]
        self.assertRaises(LibcloudError, group.destroy)

    def test_run_node(self):
        """
        Test 'ex_run_node' feature.
        """
        node = self.driver.list_nodes()[0]
        # Node is by default in NodeState.TERMINATED and AbiquoState ==
        # 'NOT_ALLOCATED'
        # so it is available to be runned
        self.driver.ex_run_node(node)

    def test_run_node_invalid_state(self):
        """
        Test 'ex_run_node' invalid state.

        Test the Driver raises an exception when try to run a
        node that is in invalid state to run.
        """
        self.driver = AbiquoNodeDriver('go', 'trunks',
                                       'http://dummy.host.com/api')
        node = self.driver.list_nodes()[0]
        # Node is by default in AbiquoState = 'ON' for user 'go:trunks'
        # so is not available to be runned
        self.assertRaises(LibcloudError, self.driver.ex_run_node, node)

    def test_run_node_failed(self):
        """
        Test 'ex_run_node' fails.

        Test driver handles correctly when, for some reason, the
        asynchronous job fails.
        """
        self.driver = AbiquoNodeDriver('ten', 'shin',
                                       'http://dummy.host.com/api')
        node = self.driver.list_nodes()[0]
        # Node is in the correct state, but it fails because of the
        # async task and it raises the error.
        self.assertRaises(LibcloudError, self.driver.ex_run_node, node)

    def test_get_href(self):
        xml = '''
<datacenter>
        <link href="http://10.60.12.7:80/api/admin/datacenters/2"
        type="application/vnd.abiquo.datacenter+xml" rel="edit1"/>
        <link href="http://10.60.12.7:80/ponies/bar/foo/api/admin/datacenters/3"
        type="application/vnd.abiquo.datacenter+xml" rel="edit2"/>
        <link href="http://vdcbridge.interoute.com:80/jclouds/apiouds/api/admin/enterprises/1234"
        type="application/vnd.abiquo.datacenter+xml" rel="edit3"/>
</datacenter>
'''

        elem = ET.XML(xml)

        href = get_href(element=elem, rel='edit1')
        self.assertEqual(href, '/admin/datacenters/2')
        href = get_href(element=elem, rel='edit2')
        self.assertEqual(href, '/admin/datacenters/3')
        href = get_href(element=elem, rel='edit3')
        self.assertEqual(href, '/admin/enterprises/1234')


class AbiquoMockHttp(MockHttpTestCase):

    """
    Mock the functionallity of the remote Abiquo API.
    """
    fixtures = ComputeFileFixtures('abiquo')
    fixture_tag = 'default'

    def _api_login(self, method, url, body, headers):
        if headers['Authorization'] == 'Basic c29uOmdvdGVu':
            expected_response = self.fixtures.load('unauthorized_user.html')
            expected_status = httplib.UNAUTHORIZED
        else:
            expected_response = self.fixtures.load('login.xml')
            expected_status = httplib.OK
        return (expected_status, expected_response, {}, '')

    def _api_cloud_virtualdatacenters(self, method, url, body, headers):
        return (httplib.OK, self.fixtures.load('vdcs.xml'), {}, '')

    def _api_cloud_virtualdatacenters_4(self, method, url, body, headers):
        return (httplib.OK, self.fixtures.load('vdc_4.xml'), {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances(self, method, url, body, headers):
        if method == 'POST':
            vapp_name = ET.XML(body).findtext('name')
            if vapp_name == 'libcloud_test_group':
                # we come from 'test_ex_create_and_delete_empty_group(self):'
                # method and so, we return the 'ok' return
                response = self.fixtures.load('vdc_4_vapp_creation_ok.xml')
                return (httplib.OK, response, {}, '')
            elif vapp_name == 'new_group_name':
                # we come from 'test_ex_create_and_delete_empty_group(self):'
                # method and so, we return the 'ok' return
                response = self.fixtures.load('vdc_4_vapp_creation_ok.xml')
                return (httplib.OK, response, {}, '')
        else:
            # It will be a 'GET';
            return (httplib.OK, self.fixtures.load('vdc_4_vapps.xml'), {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_5(self, method, url, body, headers):
        if method == 'GET':
            if headers['Authorization'] == 'Basic dmU6Z2V0YQ==':
                # Try to destroy a group with 'needs_sync' state
                response = self.fixtures.load('vdc_4_vapp_5_needs_sync.xml')
            else:
                # Try to destroy a group with 'undeployed' state
                response = self.fixtures.load('vdc_4_vapp_5.xml')
            return (httplib.OK, response, {}, '')
        else:
            # it will be a 'DELETE'
            return (httplib.NO_CONTENT, '', {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6(self, method, url, body, headers):
        if method == 'GET':
            # deployed vapp
            response = self.fixtures.load('vdc_4_vapp_6.xml')
            return (httplib.OK, response, {}, '')
        else:
            # it will be a 'DELETE'
            return (httplib.NO_CONTENT, '', {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_tasks_1da8c8b6_86f6_49ef_9d29_57dcc73b875a(self, method, url, body, headers):
        if headers['Authorization'] == 'Basic bXV0ZW46cm9zaGk=':
            # User 'muten:roshi' failed task
            response = self.fixtures.load(
                'vdc_4_vapp_6_undeploy_task_failed.xml')
        else:
            response = self.fixtures.load('vdc_4_vapp_6_undeploy_task.xml')
        return (httplib.OK, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_5_virtualmachines(
            self, method, url, body, headers):
        # This virtual app never have virtual machines
        if method == 'GET':
            response = self.fixtures.load('vdc_4_vapp_5_vms.xml')
            return (httplib.OK, response, {}, '')
        elif method == 'POST':
            # it must be a POST
            response = self.fixtures.load('vdc_4_vapp_6_vm_creation_ok.xml')
            return (httplib.CREATED, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines(
            self, method, url, body, headers):
        # Default-created virtual app virtual machines'
        if method == 'GET':
            if headers['Authorization'] == 'Basic dmU6Z2V0YQ==':
                response = self.fixtures.load('vdc_4_vapp_6_vms_allocated.xml')
            else:
                response = self.fixtures.load('vdc_4_vapp_6_vms.xml')
            return (httplib.OK, response, {}, '')
        else:
            # it must be a POST
            response = self.fixtures.load('vdc_4_vapp_6_vm_creation_ok.xml')
            return (httplib.CREATED, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3(self, method, url, body, headers):
        if (headers['Authorization'] == 'Basic Z286dHJ1bmtz' or
                headers['Authorization'] == 'Basic bXV0ZW46cm9zaGk='):
            # Undeploy node
            response = self.fixtures.load("vdc_4_vapp_6_vm_3_deployed.xml")
        elif headers['Authorization'] == 'Basic dmU6Z2V0YQ==':
            # Try to undeploy a node with 'allocation' state
            response = self.fixtures.load('vdc_4_vapp_6_vm_3_allocated.xml')
        else:
            # Get node
            response = self.fixtures.load('vdc_4_vapp_6_vm_3.xml')
        return (httplib.OK, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_action_deploy(self, method, url,
                                                                                            body, headers):
        response = self.fixtures.load('vdc_4_vapp_6_vm_3_deploy.xml')
        return (httplib.CREATED, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_tasks_b44fe278_6b0f_4dfb_be81_7c03006a93cb(self, method, url, body, headers):

        if headers['Authorization'] == 'Basic dGVuOnNoaW4=':
            # User 'ten:shin' failed task
            response = self.fixtures.load(
                'vdc_4_vapp_6_vm_3_deploy_task_failed.xml')
        else:
            response = self.fixtures.load('vdc_4_vapp_6_vm_3_deploy_task.xml')
        return (httplib.OK, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_action_undeploy(
            self, method, url, body, headers):
        response = self.fixtures.load('vdc_4_vapp_6_undeploy.xml')
        return (httplib.OK, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_action_reset(self, method,
                                                                                           url, body, headers):
        response = self.fixtures.load('vdc_4_vapp_6_vm_3_reset.xml')
        return (httplib.CREATED, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_tasks_a8c9818e_f389_45b7_be2c_3db3a9689940(self, method, url, body, headers):
        if headers['Authorization'] == 'Basic bXV0ZW46cm9zaGk=':
            # User 'muten:roshi' failed task
            response = self.fixtures.load(
                'vdc_4_vapp_6_undeploy_task_failed.xml')
        else:
            response = self.fixtures.load('vdc_4_vapp_6_vm_3_reset_task.xml')
        return (httplib.OK, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_action_undeploy(self, method, url,
                                                                                              body, headers):
        response = self.fixtures.load('vdc_4_vapp_6_vm_3_undeploy.xml')
        return (httplib.CREATED, response, {}, '')

    def _api_cloud_virtualdatacenters_4_virtualappliances_6_virtualmachines_3_network_nics(self, method, url,
                                                                                           body, headers):
        response = self.fixtures.load('vdc_4_vapp_6_vm_3_nics.xml')
        return (httplib.OK, response, {}, '')

    def _api_admin_datacenters(self, method, url, body, headers):
        return (httplib.OK, self.fixtures.load('dcs.xml'), {}, '')

    def _api_admin_enterprises_1(self, method, url, body, headers):
        return (httplib.OK, self.fixtures.load('ent_1.xml'), {}, '')

    def _api_admin_enterprises_1_datacenterrepositories(self, method, url, body, headers):
        # When the user is the common one for all the tests ('son, 'goku')
        # it creates this basic auth and we return the datacenters  value
        if headers['Authorization'] == 'Basic Z286dHJ1bmtz':
            expected_response = self.fixtures.load("not_found_error.xml")
            return (httplib.NOT_FOUND, expected_response, {}, '')
        elif headers['Authorization'] != 'Basic c29uOmdvaGFu':
            return (httplib.OK, self.fixtures.load('ent_1_dcreps.xml'), {}, '')
        else:
            # son:gohan user: forbidden error
            expected_response = self.fixtures.load("privilege_errors.html")
            return (httplib.FORBIDDEN, expected_response, {}, '')

    def _api_admin_enterprises_1_datacenterrepositories_2(self, method, url, body, headers):
        return (httplib.OK, self.fixtures.load('ent_1_dcrep_2.xml'), {}, '')

    def _api_admin_enterprises_1_datacenterrepositories_2_virtualmachinetemplates(self, method, url, body, headers):
        return (httplib.OK, self.fixtures.load('ent_1_dcrep_2_templates.xml'),
                {}, '')

    def _api_admin_enterprises_1_datacenterrepositories_2_virtualmachinetemplates_11(self, method, url, body, headers):
        return (
            httplib.OK, self.fixtures.load('ent_1_dcrep_2_template_11.xml'),
            {}, '')


if __name__ == '__main__':
    sys.exit(unittest.main())
