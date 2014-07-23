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

from __future__ import with_statement

import os
import sys
import unittest
import datetime

try:
    import simplejson as json
except ImportError:
    import json

from mock import Mock

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import method_type
from libcloud.utils.py3 import u

from libcloud.common.types import InvalidCredsError, MalformedResponseError, \
    LibcloudError
from libcloud.common.openstack import OpenStackBaseConnection
from libcloud.common.openstack import OpenStackAuthConnection
from libcloud.common.openstack import AUTH_TOKEN_EXPIRES_GRACE_SECONDS
from libcloud.compute.types import Provider, KeyPairDoesNotExistError
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.openstack import (
    OpenStack_1_0_NodeDriver, OpenStack_1_0_Response,
    OpenStack_1_1_NodeDriver, OpenStackSecurityGroup,
    OpenStackSecurityGroupRule, OpenStack_1_1_FloatingIpPool,
    OpenStack_1_1_FloatingIpAddress, OpenStackKeyPair
)
from libcloud.compute.base import Node, NodeImage, NodeSize
from libcloud.pricing import set_pricing, clear_pricing_data

from libcloud.test import MockResponse, MockHttpTestCase, XML_HEADERS
from libcloud.test.file_fixtures import ComputeFileFixtures, OpenStackFixtures
from libcloud.test.compute import TestCaseMixin

from libcloud.test.secrets import OPENSTACK_PARAMS

BASE_DIR = os.path.abspath(os.path.split(__file__)[0])


class OpenStack_1_0_ResponseTestCase(unittest.TestCase):
    XML = """<?xml version="1.0" encoding="UTF-8"?><root/>"""

    def test_simple_xml_content_type_handling(self):
        http_response = MockResponse(
            200, OpenStack_1_0_ResponseTestCase.XML, headers={'content-type': 'application/xml'})
        body = OpenStack_1_0_Response(http_response, None).parse_body()

        self.assertTrue(hasattr(body, 'tag'), "Body should be parsed as XML")

    def test_extended_xml_content_type_handling(self):
        http_response = MockResponse(200,
                                     OpenStack_1_0_ResponseTestCase.XML,
                                     headers={'content-type': 'application/xml; charset=UTF-8'})
        body = OpenStack_1_0_Response(http_response, None).parse_body()

        self.assertTrue(hasattr(body, 'tag'), "Body should be parsed as XML")

    def test_non_xml_content_type_handling(self):
        RESPONSE_BODY = "Accepted"

        http_response = MockResponse(
            202, RESPONSE_BODY, headers={'content-type': 'text/html'})
        body = OpenStack_1_0_Response(http_response, None).parse_body()

        self.assertEqual(
            body, RESPONSE_BODY, "Non-XML body should be returned as is")


class OpenStackServiceCatalogTests(unittest.TestCase):
    # TODO refactor and move into libcloud/test/common

    def setUp(self):
        OpenStackBaseConnection.conn_classes = (OpenStackMockHttp,
                                                OpenStackMockHttp)

    def test_connection_get_service_catalog(self):
        connection = OpenStackBaseConnection(*OPENSTACK_PARAMS)
        connection.auth_url = "https://auth.api.example.com"
        connection._ex_force_base_url = "https://www.foo.com"
        connection.driver = OpenStack_1_0_NodeDriver(*OPENSTACK_PARAMS)

        result = connection.get_service_catalog()
        catalog = result.get_catalog()
        endpoints = result.get_endpoints('cloudFilesCDN', 'cloudFilesCDN')
        public_urls = result.get_public_urls('cloudFilesCDN', 'cloudFilesCDN')

        expected_urls = [
            'https://cdn2.clouddrive.com/v1/MossoCloudFS',
            'https://cdn2.clouddrive.com/v1/MossoCloudFS'
        ]

        self.assertTrue('cloudFilesCDN' in catalog)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(public_urls, expected_urls)


class OpenStackAuthConnectionTests(unittest.TestCase):
    # TODO refactor and move into libcloud/test/common

    def setUp(self):
        OpenStackBaseConnection.auth_url = None
        OpenStackBaseConnection.conn_classes = (OpenStackMockHttp,
                                                OpenStackMockHttp)

    def test_auth_url_is_correctly_assembled(self):
        tuples = [
            ('1.0', OpenStackMockHttp),
            ('1.1', OpenStackMockHttp),
            ('2.0', OpenStack_2_0_MockHttp),
            ('2.0_apikey', OpenStack_2_0_MockHttp),
            ('2.0_password', OpenStack_2_0_MockHttp)
        ]

        APPEND = 0
        NOTAPPEND = 1

        auth_urls = [
            ('https://auth.api.example.com', APPEND, ''),
            ('https://auth.api.example.com/', NOTAPPEND, '/'),
            ('https://auth.api.example.com/foo/bar', NOTAPPEND, '/foo/bar'),
            ('https://auth.api.example.com/foo/bar/', NOTAPPEND, '/foo/bar/')
        ]

        actions = {
            '1.0': '/v1.0',
            '1.1': '/v1.1/auth',
            '2.0': '/v2.0/tokens',
            '2.0_apikey': '/v2.0/tokens',
            '2.0_password': '/v2.0/tokens'
        }

        user_id = OPENSTACK_PARAMS[0]
        key = OPENSTACK_PARAMS[1]

        for (auth_version, mock_http_class) in tuples:
            for (url, should_append_default_path, expected_path) in auth_urls:
                connection = \
                    self._get_mock_connection(mock_http_class=mock_http_class,
                                              auth_url=url)

                auth_url = connection.auth_url

                osa = OpenStackAuthConnection(connection,
                                              auth_url,
                                              auth_version,
                                              user_id, key)

                try:
                    osa = osa.authenticate()
                except:
                    pass

                if (should_append_default_path == APPEND):
                    expected_path = actions[auth_version]

                self.assertEqual(osa.action, expected_path)

    def test_basic_authentication(self):
        tuples = [
            ('1.0', OpenStackMockHttp),
            ('1.1', OpenStackMockHttp),
            ('2.0', OpenStack_2_0_MockHttp),
            ('2.0_apikey', OpenStack_2_0_MockHttp),
            ('2.0_password', OpenStack_2_0_MockHttp)
        ]

        user_id = OPENSTACK_PARAMS[0]
        key = OPENSTACK_PARAMS[1]

        for (auth_version, mock_http_class) in tuples:
            connection = \
                self._get_mock_connection(mock_http_class=mock_http_class)
            auth_url = connection.auth_url

            osa = OpenStackAuthConnection(connection, auth_url, auth_version,
                                          user_id, key)

            self.assertEqual(osa.urls, {})
            self.assertEqual(osa.auth_token, None)
            self.assertEqual(osa.auth_user_info, None)
            osa = osa.authenticate()

            self.assertTrue(len(osa.urls) >= 1)
            self.assertTrue(osa.auth_token is not None)

            if auth_version in ['1.1', '2.0', '2.0_apikey', '2.0_password']:
                self.assertTrue(osa.auth_token_expires is not None)

            if auth_version in ['2.0', '2.0_apikey', '2.0_password']:
                self.assertTrue(osa.auth_user_info is not None)

    def test_token_expiration_and_force_reauthentication(self):
        user_id = OPENSTACK_PARAMS[0]
        key = OPENSTACK_PARAMS[1]

        connection = self._get_mock_connection(OpenStack_2_0_MockHttp)
        auth_url = connection.auth_url
        auth_version = '2.0'

        yesterday = datetime.datetime.today() - datetime.timedelta(1)
        tomorrow = datetime.datetime.today() + datetime.timedelta(1)

        osa = OpenStackAuthConnection(connection, auth_url, auth_version,
                                      user_id, key)

        mocked_auth_method = Mock(wraps=osa.authenticate_2_0_with_body)
        osa.authenticate_2_0_with_body = mocked_auth_method

        # Force re-auth, expired token
        osa.auth_token = None
        osa.auth_token_expires = yesterday
        count = 5

        for i in range(0, count):
            osa.authenticate(force=True)

        self.assertEqual(mocked_auth_method.call_count, count)

        # No force reauth, expired token
        osa.auth_token = None
        osa.auth_token_expires = yesterday

        mocked_auth_method.call_count = 0
        self.assertEqual(mocked_auth_method.call_count, 0)

        for i in range(0, count):
            osa.authenticate(force=False)

        self.assertEqual(mocked_auth_method.call_count, 1)

        # No force reauth, valid / non-expired token
        osa.auth_token = None

        mocked_auth_method.call_count = 0
        self.assertEqual(mocked_auth_method.call_count, 0)

        for i in range(0, count):
            osa.authenticate(force=False)

            if i == 0:
                osa.auth_token_expires = tomorrow

        self.assertEqual(mocked_auth_method.call_count, 1)

        # No force reauth, valid / non-expired token which is about to expire in
        # less than AUTH_TOKEN_EXPIRES_GRACE_SECONDS
        soon = datetime.datetime.utcnow() + \
            datetime.timedelta(seconds=AUTH_TOKEN_EXPIRES_GRACE_SECONDS - 1)
        osa.auth_token = None

        mocked_auth_method.call_count = 0
        self.assertEqual(mocked_auth_method.call_count, 0)

        for i in range(0, count):
            if i == 0:
                osa.auth_token_expires = soon

            osa.authenticate(force=False)

        self.assertEqual(mocked_auth_method.call_count, 1)

    def _get_mock_connection(self, mock_http_class, auth_url=None):
        OpenStackBaseConnection.conn_classes = (mock_http_class,
                                                mock_http_class)

        if auth_url is None:
            auth_url = "https://auth.api.example.com"

        OpenStackBaseConnection.auth_url = auth_url
        connection = OpenStackBaseConnection(*OPENSTACK_PARAMS)

        connection._ex_force_base_url = "https://www.foo.com"
        connection.driver = OpenStack_1_0_NodeDriver(*OPENSTACK_PARAMS)

        return connection


class OpenStack_1_0_Tests(unittest.TestCase, TestCaseMixin):
    should_list_locations = False
    should_list_volumes = False

    driver_klass = OpenStack_1_0_NodeDriver
    driver_args = OPENSTACK_PARAMS
    driver_kwargs = {}
    # driver_kwargs = {'ex_force_auth_version': '1.0'}

    @classmethod
    def create_driver(self):
        if self is not OpenStack_1_0_FactoryMethodTests:
            self.driver_type = self.driver_klass
        return self.driver_type(*self.driver_args, **self.driver_kwargs)

    def setUp(self):
        # monkeypatch get_endpoint because the base openstack driver doesn't actually
        # work with old devstack but this class/tests are still used by the rackspace
        # driver
        def get_endpoint(*args, **kwargs):
            return "https://servers.api.rackspacecloud.com/v1.0/slug"
        self.driver_klass.connectionCls.get_endpoint = get_endpoint

        self.driver_klass.connectionCls.conn_classes = (OpenStackMockHttp,
                                                        OpenStackMockHttp)
        self.driver_klass.connectionCls.auth_url = "https://auth.api.example.com"

        OpenStackMockHttp.type = None

        self.driver = self.create_driver()
        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()
        clear_pricing_data()

    def test_populate_hosts_and_requests_path(self):
        tomorrow = datetime.datetime.today() + datetime.timedelta(1)
        cls = self.driver_klass.connectionCls

        count = 5

        # Test authentication and token re-use
        con = cls('username', 'key')
        osa = con._osa

        mocked_auth_method = Mock()
        osa.authenticate = mocked_auth_method

        # Valid token returned on first call, should be reused.
        for i in range(0, count):
            con._populate_hosts_and_request_paths()

            if i == 0:
                osa.auth_token = '1234'
                osa.auth_token_expires = tomorrow

        self.assertEqual(mocked_auth_method.call_count, 1)

        osa.auth_token = None
        osa.auth_token_expires = None

        # ex_force_auth_token provided, authenticate should never be called
        con = cls('username', 'key', ex_force_base_url='http://ponies',
                  ex_force_auth_token='1234')
        osa = con._osa

        mocked_auth_method = Mock()
        osa.authenticate = mocked_auth_method

        for i in range(0, count):
            con._populate_hosts_and_request_paths()

        self.assertEqual(mocked_auth_method.call_count, 0)

    def test_auth_token_is_set(self):
        self.driver.connection._populate_hosts_and_request_paths()
        self.assertEqual(
            self.driver.connection.auth_token, "aaaaaaaaaaaa-bbb-cccccccccccccc")

    def test_auth_token_expires_is_set(self):
        self.driver.connection._populate_hosts_and_request_paths()

        expires = self.driver.connection.auth_token_expires
        self.assertEqual(expires.isoformat(), "2031-11-23T21:00:14-06:00")

    def test_auth(self):
        if self.driver.connection._auth_version == '2.0':
            return

        OpenStackMockHttp.type = 'UNAUTHORIZED'
        try:
            self.driver = self.create_driver()
            self.driver.list_nodes()
        except InvalidCredsError:
            e = sys.exc_info()[1]
            self.assertEqual(True, isinstance(e, InvalidCredsError))
        else:
            self.fail('test should have thrown')

    def test_auth_missing_key(self):
        if self.driver.connection._auth_version == '2.0':
            return

        OpenStackMockHttp.type = 'UNAUTHORIZED_MISSING_KEY'
        try:
            self.driver = self.create_driver()
            self.driver.list_nodes()
        except MalformedResponseError:
            e = sys.exc_info()[1]
            self.assertEqual(True, isinstance(e, MalformedResponseError))
        else:
            self.fail('test should have thrown')

    def test_auth_server_error(self):
        if self.driver.connection._auth_version == '2.0':
            return

        OpenStackMockHttp.type = 'INTERNAL_SERVER_ERROR'
        try:
            self.driver = self.create_driver()
            self.driver.list_nodes()
        except MalformedResponseError:
            e = sys.exc_info()[1]
            self.assertEqual(True, isinstance(e, MalformedResponseError))
        else:
            self.fail('test should have thrown')

    def test_error_parsing_when_body_is_missing_message(self):
        OpenStackMockHttp.type = 'NO_MESSAGE_IN_ERROR_BODY'
        try:
            self.driver.list_images()
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(True, isinstance(e, Exception))
        else:
            self.fail('test should have thrown')

    def test_list_locations(self):
        locations = self.driver.list_locations()
        self.assertEqual(len(locations), 1)

    def test_list_nodes(self):
        OpenStackMockHttp.type = 'EMPTY'
        ret = self.driver.list_nodes()
        self.assertEqual(len(ret), 0)
        OpenStackMockHttp.type = None
        ret = self.driver.list_nodes()
        self.assertEqual(len(ret), 1)
        node = ret[0]
        self.assertEqual('67.23.21.33', node.public_ips[0])
        self.assertTrue('10.176.168.218' in node.private_ips)
        self.assertEqual(node.extra.get('flavorId'), '1')
        self.assertEqual(node.extra.get('imageId'), '11')
        self.assertEqual(type(node.extra.get('metadata')), type(dict()))
        OpenStackMockHttp.type = 'METADATA'
        ret = self.driver.list_nodes()
        self.assertEqual(len(ret), 1)
        node = ret[0]
        self.assertEqual(type(node.extra.get('metadata')), type(dict()))
        self.assertEqual(node.extra.get('metadata').get('somekey'),
                         'somevalue')
        OpenStackMockHttp.type = None

    def test_list_images(self):
        ret = self.driver.list_images()
        expected = {10: {'serverId': None,
                         'status': 'ACTIVE',
                         'created': '2009-07-20T09:14:37-05:00',
                         'updated': '2009-07-20T09:14:37-05:00',
                         'progress': None,
                         'minDisk': None,
                         'minRam': None},
                    11: {'serverId': '91221',
                         'status': 'ACTIVE',
                         'created': '2009-11-29T20:22:09-06:00',
                         'updated': '2009-11-29T20:24:08-06:00',
                         'progress': '100',
                         'minDisk': '5',
                         'minRam': '256'}}
        for ret_idx, extra in list(expected.items()):
            for key, value in list(extra.items()):
                self.assertEqual(ret[ret_idx].extra[key], value)

    def test_create_node(self):
        image = NodeImage(id=11, name='Ubuntu 8.10 (intrepid)',
                          driver=self.driver)
        size = NodeSize(1, '256 slice', None, None, None, None,
                        driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size)
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra.get('password'), 'racktestvJq7d3')

    def test_create_node_without_adminPass(self):
        OpenStackMockHttp.type = 'NO_ADMIN_PASS'
        image = NodeImage(id=11, name='Ubuntu 8.10 (intrepid)',
                          driver=self.driver)
        size = NodeSize(1, '256 slice', None, None, None, None,
                        driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size)
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra.get('password'), None)

    def test_create_node_ex_shared_ip_group(self):
        OpenStackMockHttp.type = 'EX_SHARED_IP_GROUP'
        image = NodeImage(id=11, name='Ubuntu 8.10 (intrepid)',
                          driver=self.driver)
        size = NodeSize(1, '256 slice', None, None, None, None,
                        driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size,
                                       ex_shared_ip_group_id='12345')
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra.get('password'), 'racktestvJq7d3')

    def test_create_node_with_metadata(self):
        OpenStackMockHttp.type = 'METADATA'
        image = NodeImage(id=11, name='Ubuntu 8.10 (intrepid)',
                          driver=self.driver)
        size = NodeSize(1, '256 slice', None, None, None, None,
                        driver=self.driver)
        metadata = {'a': 'b', 'c': 'd'}
        files = {'/file1': 'content1', '/file2': 'content2'}
        node = self.driver.create_node(name='racktest', image=image, size=size,
                                       metadata=metadata, files=files)
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra.get('password'), 'racktestvJq7d3')
        self.assertEqual(node.extra.get('metadata'), metadata)

    def test_reboot_node(self):
        node = Node(id=72258, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        ret = node.reboot()
        self.assertTrue(ret is True)

    def test_destroy_node(self):
        node = Node(id=72258, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        ret = node.destroy()
        self.assertTrue(ret is True)

    def test_ex_limits(self):
        limits = self.driver.ex_limits()
        self.assertTrue("rate" in limits)
        self.assertTrue("absolute" in limits)

    def test_create_image(self):
        node = Node(id=444222, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        image = self.driver.create_image(node, "imgtest")
        self.assertEqual(image.name, "imgtest")
        self.assertEqual(image.id, "12345")

    def test_delete_image(self):
        image = NodeImage(id=333111, name='Ubuntu 8.10 (intrepid)',
                          driver=self.driver)
        ret = self.driver.delete_image(image)
        self.assertTrue(ret)

    def test_ex_list_ip_addresses(self):
        ret = self.driver.ex_list_ip_addresses(node_id=72258)
        self.assertEqual(2, len(ret.public_addresses))
        self.assertTrue('67.23.10.131' in ret.public_addresses)
        self.assertTrue('67.23.10.132' in ret.public_addresses)
        self.assertEqual(1, len(ret.private_addresses))
        self.assertTrue('10.176.42.16' in ret.private_addresses)

    def test_ex_list_ip_groups(self):
        ret = self.driver.ex_list_ip_groups()
        self.assertEqual(2, len(ret))
        self.assertEqual('1234', ret[0].id)
        self.assertEqual('Shared IP Group 1', ret[0].name)
        self.assertEqual('5678', ret[1].id)
        self.assertEqual('Shared IP Group 2', ret[1].name)
        self.assertTrue(ret[0].servers is None)

    def test_ex_list_ip_groups_detail(self):
        ret = self.driver.ex_list_ip_groups(details=True)

        self.assertEqual(2, len(ret))

        self.assertEqual('1234', ret[0].id)
        self.assertEqual('Shared IP Group 1', ret[0].name)
        self.assertEqual(2, len(ret[0].servers))
        self.assertEqual('422', ret[0].servers[0])
        self.assertEqual('3445', ret[0].servers[1])

        self.assertEqual('5678', ret[1].id)
        self.assertEqual('Shared IP Group 2', ret[1].name)
        self.assertEqual(3, len(ret[1].servers))
        self.assertEqual('23203', ret[1].servers[0])
        self.assertEqual('2456', ret[1].servers[1])
        self.assertEqual('9891', ret[1].servers[2])

    def test_ex_create_ip_group(self):
        ret = self.driver.ex_create_ip_group('Shared IP Group 1', '5467')
        self.assertEqual('1234', ret.id)
        self.assertEqual('Shared IP Group 1', ret.name)
        self.assertEqual(1, len(ret.servers))
        self.assertEqual('422', ret.servers[0])

    def test_ex_delete_ip_group(self):
        ret = self.driver.ex_delete_ip_group('5467')
        self.assertEqual(True, ret)

    def test_ex_share_ip(self):
        ret = self.driver.ex_share_ip('1234', '3445', '67.23.21.133')
        self.assertEqual(True, ret)

    def test_ex_unshare_ip(self):
        ret = self.driver.ex_unshare_ip('3445', '67.23.21.133')
        self.assertEqual(True, ret)

    def test_ex_resize(self):
        node = Node(id=444222, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        size = NodeSize(1, '256 slice', None, None, None, None,
                        driver=self.driver)
        self.assertTrue(self.driver.ex_resize(node=node, size=size))

    def test_ex_confirm_resize(self):
        node = Node(id=444222, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        self.assertTrue(self.driver.ex_confirm_resize(node=node))

    def test_ex_revert_resize(self):
        node = Node(id=444222, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        self.assertTrue(self.driver.ex_revert_resize(node=node))

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 7, 'Wrong sizes count')

        for size in sizes:
            self.assertTrue(isinstance(size.price, float),
                            'Wrong size price type')

            if self.driver.api_name == 'openstack':
                self.assertEqual(size.price, 0,
                                 'Size price should be zero by default')

    def test_list_sizes_with_specified_pricing(self):
        if self.driver.api_name != 'openstack':
            return

        pricing = dict((str(i), i) for i in range(1, 8))

        set_pricing(driver_type='compute', driver_name='openstack',
                    pricing=pricing)

        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 7, 'Wrong sizes count')

        for size in sizes:
            self.assertTrue(isinstance(size.price, float),
                            'Wrong size price type')
            self.assertEqual(float(size.price), float(pricing[size.id]))


class OpenStack_1_0_FactoryMethodTests(OpenStack_1_0_Tests):
    should_list_locations = False
    should_list_volumes = False

    driver_klass = OpenStack_1_0_NodeDriver
    driver_type = get_driver(Provider.OPENSTACK)
    driver_args = OPENSTACK_PARAMS + ('1.0',)

    def test_factory_method_invalid_version(self):
        try:
            self.driver_type(*(OPENSTACK_PARAMS + ('15.5',)))
        except NotImplementedError:
            pass
        else:
            self.fail('Exception was not thrown')


class OpenStackMockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('openstack')
    auth_fixtures = OpenStackFixtures()
    json_content_headers = {'content-type': 'application/json; charset=UTF-8'}

    # fake auth token response
    def _v1_0(self, method, url, body, headers):
        headers = {
            'x-server-management-url': 'https://servers.api.rackspacecloud.com/v1.0/slug',
            'x-auth-token': 'FE011C19-CF86-4F87-BE5D-9229145D7A06',
            'x-cdn-management-url': 'https://cdn.clouddrive.com/v1/MossoCloudFS_FE011C19-CF86-4F87-BE5D-9229145D7A06',
            'x-storage-token': 'FE011C19-CF86-4F87-BE5D-9229145D7A06',
            'x-storage-url': 'https://storage4.clouddrive.com/v1/MossoCloudFS_FE011C19-CF86-4F87-BE5D-9229145D7A06'}
        return (httplib.NO_CONTENT, "", headers, httplib.responses[httplib.NO_CONTENT])

    def _v1_0_UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED, "", {}, httplib.responses[httplib.UNAUTHORIZED])

    def _v1_0_INTERNAL_SERVER_ERROR(self, method, url, body, headers):
        return (httplib.INTERNAL_SERVER_ERROR, "<h1>500: Internal Server Error</h1>", {},
                httplib.responses[httplib.INTERNAL_SERVER_ERROR])

    def _v1_0_slug_images_detail_NO_MESSAGE_IN_ERROR_BODY(self, method, url, body, headers):
        body = self.fixtures.load('300_multiple_choices.json')
        return (httplib.MULTIPLE_CHOICES, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_0_UNAUTHORIZED_MISSING_KEY(self, method, url, body, headers):
        headers = {
            'x-server-management-url': 'https://servers.api.rackspacecloud.com/v1.0/slug',
            'x-auth-tokenx': 'FE011C19-CF86-4F87-BE5D-9229145D7A06',
            'x-cdn-management-url': 'https://cdn.clouddrive.com/v1/MossoCloudFS_FE011C19-CF86-4F87-BE5D-9229145D7A06'}
        return (httplib.NO_CONTENT, "", headers, httplib.responses[httplib.NO_CONTENT])

    def _v2_0_tokens(self, method, url, body, headers):
        body = self.auth_fixtures.load('_v2_0__auth.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_0_slug_servers_detail_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers_detail_empty.xml')
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_servers_detail(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers_detail.xml')
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_servers_detail_METADATA(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers_detail_metadata.xml')
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_images_333111(self, method, url, body, headers):
        if method != "DELETE":
            raise NotImplementedError()
        # this is currently used for deletion of an image
        # as such it should not accept GET/POST
        return(httplib.NO_CONTENT, "", "", httplib.responses[httplib.NO_CONTENT])

    def _v1_0_slug_images(self, method, url, body, headers):
        if method != "POST":
            raise NotImplementedError()
        # this is currently used for creation of new image with
        # POST request, don't handle GET to avoid possible confusion
        body = self.fixtures.load('v1_slug_images_post.xml')
        return (httplib.ACCEPTED, body, XML_HEADERS, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_images_detail(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_images_detail.xml')
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_servers(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers.xml')
        return (httplib.ACCEPTED, body, XML_HEADERS, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_NO_ADMIN_PASS(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers_no_admin_pass.xml')
        return (httplib.ACCEPTED, body, XML_HEADERS, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_EX_SHARED_IP_GROUP(self, method, url, body, headers):
        # test_create_node_ex_shared_ip_group
        # Verify that the body contains sharedIpGroupId XML element
        body = u(body)
        self.assertTrue(body.find('sharedIpGroupId="12345"') != -1)
        body = self.fixtures.load('v1_slug_servers.xml')
        return (httplib.ACCEPTED, body, XML_HEADERS, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_METADATA(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers_metadata.xml')
        return (httplib.ACCEPTED, body, XML_HEADERS, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_72258_action(self, method, url, body, headers):
        if method != "POST" or body[:8] != "<reboot ":
            raise NotImplementedError()
        # only used by reboot() right now, but we will need to parse body
        # someday !!!!
        return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_limits(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_limits.xml')
        return (httplib.ACCEPTED, body, XML_HEADERS, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_72258(self, method, url, body, headers):
        if method != "DELETE":
            raise NotImplementedError()
        # only used by destroy node()
        return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_72258_ips(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_servers_ips.xml')
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_shared_ip_groups_5467(self, method, url, body, headers):
        if method != 'DELETE':
            raise NotImplementedError()
        return (httplib.NO_CONTENT, "", {}, httplib.responses[httplib.NO_CONTENT])

    def _v1_0_slug_shared_ip_groups(self, method, url, body, headers):

        fixture = 'v1_slug_shared_ip_group.xml' if method == 'POST' else 'v1_slug_shared_ip_groups.xml'
        body = self.fixtures.load(fixture)
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_shared_ip_groups_detail(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_shared_ip_groups_detail.xml')
        return (httplib.OK, body, XML_HEADERS, httplib.responses[httplib.OK])

    def _v1_0_slug_servers_3445_ips_public_67_23_21_133(self, method, url, body, headers):
        return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

    def _v1_0_slug_servers_444222_action(self, method, url, body, headers):
        body = u(body)
        if body.find('resize') != -1:
            # test_ex_resize_server
            return (httplib.ACCEPTED, "", headers, httplib.responses[httplib.NO_CONTENT])
        elif body.find('confirmResize') != -1:
            # test_ex_confirm_resize
            return (httplib.NO_CONTENT, "", headers, httplib.responses[httplib.NO_CONTENT])
        elif body.find('revertResize') != -1:
            # test_ex_revert_resize
            return (httplib.NO_CONTENT, "", headers, httplib.responses[httplib.NO_CONTENT])

    def _v1_0_slug_flavors_detail(self, method, url, body, headers):
        body = self.fixtures.load('v1_slug_flavors_detail.xml')
        headers = {
            'date': 'Tue, 14 Jun 2011 09:43:55 GMT', 'content-length': '529'}
        headers.update(XML_HEADERS)
        return (httplib.OK, body, headers, httplib.responses[httplib.OK])

    def _v1_1_auth(self, method, url, body, headers):
        body = self.auth_fixtures.load('_v1_1__auth.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_auth_UNAUTHORIZED(self, method, url, body, headers):
        body = self.auth_fixtures.load('_v1_1__auth_unauthorized.json')
        return (httplib.UNAUTHORIZED, body, self.json_content_headers, httplib.responses[httplib.UNAUTHORIZED])

    def _v1_1_auth_UNAUTHORIZED_MISSING_KEY(self, method, url, body, headers):
        body = self.auth_fixtures.load('_v1_1__auth_mssing_token.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_auth_INTERNAL_SERVER_ERROR(self, method, url, body, headers):
        return (httplib.INTERNAL_SERVER_ERROR, "<h1>500: Internal Server Error</h1>",  {'content-type': 'text/html'},
                httplib.responses[httplib.INTERNAL_SERVER_ERROR])


class OpenStack_1_1_Tests(unittest.TestCase, TestCaseMixin):
    should_list_locations = False
    should_list_volumes = True

    driver_klass = OpenStack_1_1_NodeDriver
    driver_type = OpenStack_1_1_NodeDriver
    driver_args = OPENSTACK_PARAMS
    driver_kwargs = {'ex_force_auth_version': '2.0'}

    @classmethod
    def create_driver(self):
        if self is not OpenStack_1_1_FactoryMethodTests:
            self.driver_type = self.driver_klass
        return self.driver_type(*self.driver_args, **self.driver_kwargs)

    def setUp(self):
        self.driver_klass.connectionCls.conn_classes = (
            OpenStack_2_0_MockHttp, OpenStack_2_0_MockHttp)
        self.driver_klass.connectionCls.auth_url = "https://auth.api.example.com"

        OpenStackMockHttp.type = None
        OpenStack_1_1_MockHttp.type = None
        OpenStack_2_0_MockHttp.type = None

        self.driver = self.create_driver()

        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()
        clear_pricing_data()
        self.node = self.driver.list_nodes()[1]

    def _force_reauthentication(self):
        """
        Trash current auth token so driver will be forced to re-authentication
        on next request.
        """
        self.driver.connection._ex_force_base_url = 'http://ex_force_base_url.com:666/forced_url'
        self.driver.connection.auth_token = None
        self.driver.connection.auth_token_expires = None
        self.driver.connection._osa.auth_token = None
        self.driver.connection._osa.auth_token_expires = None

    def test_auth_token_is_set(self):
        self._force_reauthentication()
        self.driver.connection._populate_hosts_and_request_paths()

        self.assertEqual(
            self.driver.connection.auth_token, "aaaaaaaaaaaa-bbb-cccccccccccccc")

    def test_auth_token_expires_is_set(self):
        self._force_reauthentication()
        self.driver.connection._populate_hosts_and_request_paths()

        expires = self.driver.connection.auth_token_expires
        self.assertEqual(expires.isoformat(), "2031-11-23T21:00:14-06:00")

    def test_ex_force_base_url(self):
        # change base url and trash the current auth token so we can
        # re-authenticate
        self.driver.connection._ex_force_base_url = 'http://ex_force_base_url.com:666/forced_url'
        self.driver.connection.auth_token = None
        self.driver.connection._populate_hosts_and_request_paths()

        # assert that we use the base url and not the auth url
        self.assertEqual(self.driver.connection.host, 'ex_force_base_url.com')
        self.assertEqual(self.driver.connection.port, '666')
        self.assertEqual(self.driver.connection.request_path, '/forced_url')

    def test_get_endpoint_populates_host_port_and_request_path(self):
        # simulate a subclass overriding this method
        self.driver.connection.get_endpoint = lambda: 'http://endpoint_auth_url.com:1555/service_url'
        self.driver.connection.auth_token = None
        self.driver.connection._ex_force_base_url = None
        self.driver.connection._populate_hosts_and_request_paths()

        # assert that we use the result of get endpoint
        self.assertEqual(self.driver.connection.host, 'endpoint_auth_url.com')
        self.assertEqual(self.driver.connection.port, '1555')
        self.assertEqual(self.driver.connection.request_path, '/service_url')

    def test_set_auth_token_populates_host_port_and_request_path(self):
        # change base url and trash the current auth token so we can
        # re-authenticate
        self.driver.connection._ex_force_base_url = 'http://some_other_ex_force_base_url.com:1222/some-service'
        self.driver.connection.auth_token = "preset-auth-token"
        self.driver.connection._populate_hosts_and_request_paths()

        # assert that we use the base url and not the auth url
        self.assertEqual(
            self.driver.connection.host, 'some_other_ex_force_base_url.com')
        self.assertEqual(self.driver.connection.port, '1222')
        self.assertEqual(self.driver.connection.request_path, '/some-service')

    def test_auth_token_without_base_url_raises_exception(self):
        kwargs = {
            'ex_force_auth_version': '2.0',
            'ex_force_auth_token': 'preset-auth-token'
        }
        try:
            self.driver_type(*self.driver_args, **kwargs)
            self.fail('Expected failure setting auth token without base url')
        except LibcloudError:
            pass
        else:
            self.fail('Expected failure setting auth token without base url')

    def test_ex_force_auth_token_passed_to_connection(self):
        base_url = 'https://servers.api.rackspacecloud.com/v1.1/slug'
        kwargs = {
            'ex_force_auth_version': '2.0',
            'ex_force_auth_token': 'preset-auth-token',
            'ex_force_base_url': base_url
        }

        driver = self.driver_type(*self.driver_args, **kwargs)
        driver.list_nodes()

        self.assertEqual(kwargs['ex_force_auth_token'],
                         driver.connection.auth_token)
        self.assertEqual('servers.api.rackspacecloud.com',
                         driver.connection.host)
        self.assertEqual('/v1.1/slug', driver.connection.request_path)
        self.assertEqual(443, driver.connection.port)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertEqual(len(nodes), 2)
        node = nodes[0]

        self.assertEqual('12065', node.id)
        # test public IPv4
        self.assertTrue('12.16.18.28' in node.public_ips)
        self.assertTrue('50.57.94.35' in node.public_ips)
        # test public IPv6
        self.assertTrue(
            '2001:4801:7808:52:16:3eff:fe47:788a' in node.public_ips)
        # test private IPv4
        self.assertTrue('10.182.64.34' in node.private_ips)
        # test private IPv6
        self.assertTrue(
            'fec0:4801:7808:52:16:3eff:fe60:187d' in node.private_ips)

        self.assertEqual(node.extra.get('flavorId'), '2')
        self.assertEqual(node.extra.get('imageId'), '7')
        self.assertEqual(node.extra.get('metadata'), {})
        self.assertEqual(node.extra['updated'], '2011-10-11T00:50:04Z')
        self.assertEqual(node.extra['created'], '2011-10-11T00:51:39Z')

    def test_list_nodes_no_image_id_attribute(self):
        # Regression test for LIBCLOD-455
        self.driver_klass.connectionCls.conn_classes[0].type = 'ERROR_STATE_NO_IMAGE_ID'
        self.driver_klass.connectionCls.conn_classes[1].type = 'ERROR_STATE_NO_IMAGE_ID'

        nodes = self.driver.list_nodes()
        self.assertEqual(nodes[0].extra['imageId'], None)

    def test_list_volumes(self):
        volumes = self.driver.list_volumes()
        self.assertEqual(len(volumes), 2)
        volume = volumes[0]

        self.assertEqual('cd76a3a1-c4ce-40f6-9b9f-07a61508938d', volume.id)
        self.assertEqual('test_volume_2', volume.name)
        self.assertEqual(2, volume.size)

        self.assertEqual(volume.extra['description'], '')
        self.assertEqual(volume.extra['attachments'][0][
                         'id'], 'cd76a3a1-c4ce-40f6-9b9f-07a61508938d')

        volume = volumes[1]
        self.assertEqual('cfcec3bc-b736-4db5-9535-4c24112691b5', volume.id)
        self.assertEqual('test_volume', volume.name)
        self.assertEqual(50, volume.size)

        self.assertEqual(volume.extra['description'], 'some description')
        self.assertEqual(volume.extra['attachments'], [])

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 8, 'Wrong sizes count')

        for size in sizes:
            self.assertTrue(isinstance(size.price, float),
                            'Wrong size price type')

        self.assertEqual(sizes[0].vcpus, 8)

    def test_list_sizes_with_specified_pricing(self):

        pricing = dict((str(i), i * 5.0) for i in range(1, 9))

        set_pricing(driver_type='compute',
                    driver_name=self.driver.api_name, pricing=pricing)

        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 8, 'Wrong sizes count')

        for size in sizes:
            self.assertTrue(isinstance(size.price, float),
                            'Wrong size price type')

            self.assertEqual(size.price, pricing[size.id],
                             'Size price should match')

    def test_list_images(self):
        images = self.driver.list_images()
        self.assertEqual(len(images), 13, 'Wrong images count')

        image = images[0]
        self.assertEqual(image.id, '13')
        self.assertEqual(image.name, 'Windows 2008 SP2 x86 (B24)')
        self.assertEqual(image.extra['updated'], '2011-08-06T18:14:02Z')
        self.assertEqual(image.extra['created'], '2011-08-06T18:13:11Z')
        self.assertEqual(image.extra['status'], 'ACTIVE')
        self.assertEqual(image.extra['metadata']['os_type'], 'windows')
        self.assertEqual(
            image.extra['serverId'], '52415800-8b69-11e0-9b19-734f335aa7b3')
        self.assertEqual(image.extra['minDisk'], 0)
        self.assertEqual(image.extra['minRam'], 0)

    def test_create_node(self):
        image = NodeImage(
            id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size)
        self.assertEqual(node.id, '26f7fbee-8ce1-4c28-887a-bfe8e4bb10fe')
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra['password'], 'racktestvJq7d3')
        self.assertEqual(node.extra['metadata']['My Server Name'], 'Apache1')

    def test_create_node_with_ex_keyname_and_ex_userdata(self):
        image = NodeImage(
            id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size,
                                       ex_keyname='devstack',
                                       ex_userdata='sample data')
        self.assertEqual(node.id, '26f7fbee-8ce1-4c28-887a-bfe8e4bb10fe')
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra['password'], 'racktestvJq7d3')
        self.assertEqual(node.extra['metadata']['My Server Name'], 'Apache1')
        self.assertEqual(node.extra['key_name'], 'devstack')

    def test_create_node_with_availability_zone(self):
        image = NodeImage(
            id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size,
                                       availability_zone='testaz')
        self.assertEqual(node.id, '26f7fbee-8ce1-4c28-887a-bfe8e4bb10fe')
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra['password'], 'racktestvJq7d3')
        self.assertEqual(node.extra['metadata']['My Server Name'], 'Apache1')
        self.assertEqual(node.extra['availability_zone'], 'testaz')

    def test_create_node_with_ex_disk_config(self):
        OpenStack_1_1_MockHttp.type = 'EX_DISK_CONFIG'
        image = NodeImage(
            id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size,
                                       ex_disk_config='AUTO')
        self.assertEqual(node.id, '26f7fbee-8ce1-4c28-887a-bfe8e4bb10fe')
        self.assertEqual(node.name, 'racktest')
        self.assertEqual(node.extra['disk_config'], 'AUTO')

    def test_destroy_node(self):
        self.assertTrue(self.node.destroy())

    def test_reboot_node(self):
        self.assertTrue(self.node.reboot())

    def test_create_volume(self):
        self.assertEqual(self.driver.create_volume(1, 'test'), True)

    def test_destroy_volume(self):
        volume = self.driver.ex_get_volume(
            'cd76a3a1-c4ce-40f6-9b9f-07a61508938d')
        self.assertEqual(self.driver.destroy_volume(volume), True)

    def test_attach_volume(self):
        node = self.driver.list_nodes()[0]
        volume = self.driver.ex_get_volume(
            'cd76a3a1-c4ce-40f6-9b9f-07a61508938d')
        self.assertEqual(
            self.driver.attach_volume(node, volume, '/dev/sdb'), True)

    def test_detach_volume(self):
        node = self.driver.list_nodes()[0]
        volume = self.driver.ex_get_volume(
            'cd76a3a1-c4ce-40f6-9b9f-07a61508938d')
        self.assertEqual(
            self.driver.attach_volume(node, volume, '/dev/sdb'), True)
        self.assertEqual(self.driver.detach_volume(volume), True)

    def test_ex_set_password(self):
        self.assertTrue(self.driver.ex_set_password(self.node, 'New1&53jPass'))

    def test_ex_rebuild(self):
        image = NodeImage(id=11, name='Ubuntu 8.10 (intrepid)',
                          driver=self.driver)
        success = self.driver.ex_rebuild(self.node, image=image)
        self.assertTrue(success)

    def test_ex_rebuild_with_ex_disk_config(self):
        image = NodeImage(id=58, name='Ubuntu 10.10 (intrepid)',
                          driver=self.driver)
        node = Node(id=12066, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        success = self.driver.ex_rebuild(node, image=image,
                                         ex_disk_config='MANUAL')
        self.assertTrue(success)

    def test_ex_resize(self):
        size = NodeSize(1, '256 slice', None, None, None, None,
                        driver=self.driver)
        try:
            self.driver.ex_resize(self.node, size)
        except Exception:
            e = sys.exc_info()[1]
            self.fail('An error was raised: ' + repr(e))

    def test_ex_confirm_resize(self):
        try:
            self.driver.ex_confirm_resize(self.node)
        except Exception:
            e = sys.exc_info()[1]
            self.fail('An error was raised: ' + repr(e))

    def test_ex_revert_resize(self):
        try:
            self.driver.ex_revert_resize(self.node)
        except Exception:
            e = sys.exc_info()[1]
            self.fail('An error was raised: ' + repr(e))

    def test_create_image(self):
        image = self.driver.create_image(self.node, 'new_image')
        self.assertEqual(image.name, 'new_image')
        self.assertEqual(image.id, '4949f9ee-2421-4c81-8b49-13119446008b')

    def test_ex_set_server_name(self):
        old_node = Node(
            id='12064', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        new_node = self.driver.ex_set_server_name(old_node, 'Bob')
        self.assertEqual('Bob', new_node.name)

    def test_ex_set_metadata(self):
        old_node = Node(
            id='12063', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        metadata = {'Image Version': '2.1', 'Server Label': 'Web Head 1'}
        returned_metadata = self.driver.ex_set_metadata(old_node, metadata)
        self.assertEqual(metadata, returned_metadata)

    def test_ex_get_metadata(self):
        node = Node(
            id='12063', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )

        metadata = {'Image Version': '2.1', 'Server Label': 'Web Head 1'}
        returned_metadata = self.driver.ex_get_metadata(node)
        self.assertEqual(metadata, returned_metadata)

    def test_ex_update_node(self):
        old_node = Node(
            id='12064',
            name=None, state=None, public_ips=None, private_ips=None, driver=self.driver,
        )

        new_node = self.driver.ex_update_node(old_node, name='Bob')

        self.assertTrue(new_node)
        self.assertEqual('Bob', new_node.name)
        self.assertEqual('50.57.94.30', new_node.public_ips[0])

    def test_ex_get_node_details(self):
        node_id = '12064'
        node = self.driver.ex_get_node_details(node_id)
        self.assertEqual(node.id, '12064')
        self.assertEqual(node.name, 'lc-test')

    def test_ex_get_size(self):
        size_id = '7'
        size = self.driver.ex_get_size(size_id)
        self.assertEqual(size.id, size_id)
        self.assertEqual(size.name, '15.5GB slice')

    def test_get_image(self):
        image_id = '13'
        image = self.driver.get_image(image_id)
        self.assertEqual(image.id, image_id)
        self.assertEqual(image.name, 'Windows 2008 SP2 x86 (B24)')
        self.assertEqual(image.extra['serverId'], None)
        self.assertEqual(image.extra['minDisk'], "5")
        self.assertEqual(image.extra['minRam'], "256")

    def test_delete_image(self):
        image = NodeImage(
            id='26365521-8c62-11f9-2c33-283d153ecc3a', name='My Backup', driver=self.driver)
        result = self.driver.delete_image(image)
        self.assertTrue(result)

    def test_extract_image_id_from_url(self):
        url = 'http://127.0.0.1/v1.1/68/images/1d4a8ea9-aae7-4242-a42d-5ff4702f2f14'
        url_two = 'http://127.0.0.1/v1.1/68/images/13'
        image_id = self.driver._extract_image_id_from_url(url)
        image_id_two = self.driver._extract_image_id_from_url(url_two)
        self.assertEqual(image_id, '1d4a8ea9-aae7-4242-a42d-5ff4702f2f14')
        self.assertEqual(image_id_two, '13')

    def test_ex_rescue_with_password(self):
        node = Node(id=12064, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        n = self.driver.ex_rescue(node, 'foo')
        self.assertEqual(n.extra['password'], 'foo')

    def test_ex_rescue_no_password(self):
        node = Node(id=12064, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        n = self.driver.ex_rescue(node)
        self.assertEqual(n.extra['password'], 'foo')

    def test_ex_unrescue(self):
        node = Node(id=12064, name=None, state=None, public_ips=None,
                    private_ips=None, driver=self.driver)
        result = self.driver.ex_unrescue(node)
        self.assertTrue(result)

    def test_ex_get_node_security_groups(self):
        node = Node(id='1c01300f-ef97-4937-8f03-ac676d6234be', name=None,
                    state=None, public_ips=None, private_ips=None, driver=self.driver)
        security_groups = self.driver.ex_get_node_security_groups(node)
        self.assertEqual(
            len(security_groups), 2, 'Wrong security groups count')

        security_group = security_groups[1]
        self.assertEqual(security_group.id, 4)
        self.assertEqual(security_group.tenant_id, '68')
        self.assertEqual(security_group.name, 'ftp')
        self.assertEqual(
            security_group.description, 'FTP Client-Server - Open 20-21 ports')
        self.assertEqual(security_group.rules[0].id, 1)
        self.assertEqual(security_group.rules[0].parent_group_id, 4)
        self.assertEqual(security_group.rules[0].ip_protocol, "tcp")
        self.assertEqual(security_group.rules[0].from_port, 20)
        self.assertEqual(security_group.rules[0].to_port, 21)
        self.assertEqual(security_group.rules[0].ip_range, '0.0.0.0/0')

    def test_ex_list_security_groups(self):
        security_groups = self.driver.ex_list_security_groups()
        self.assertEqual(
            len(security_groups), 2, 'Wrong security groups count')

        security_group = security_groups[1]
        self.assertEqual(security_group.id, 4)
        self.assertEqual(security_group.tenant_id, '68')
        self.assertEqual(security_group.name, 'ftp')
        self.assertEqual(
            security_group.description, 'FTP Client-Server - Open 20-21 ports')
        self.assertEqual(security_group.rules[0].id, 1)
        self.assertEqual(security_group.rules[0].parent_group_id, 4)
        self.assertEqual(security_group.rules[0].ip_protocol, "tcp")
        self.assertEqual(security_group.rules[0].from_port, 20)
        self.assertEqual(security_group.rules[0].to_port, 21)
        self.assertEqual(security_group.rules[0].ip_range, '0.0.0.0/0')

    def test_ex_create_security_group(self):
        name = 'test'
        description = 'Test Security Group'
        security_group = self.driver.ex_create_security_group(
            name, description)

        self.assertEqual(security_group.id, 6)
        self.assertEqual(security_group.tenant_id, '68')
        self.assertEqual(security_group.name, name)
        self.assertEqual(security_group.description, description)
        self.assertEqual(len(security_group.rules), 0)

    def test_ex_delete_security_group(self):
        security_group = OpenStackSecurityGroup(
            id=6, tenant_id=None, name=None, description=None, driver=self.driver)
        result = self.driver.ex_delete_security_group(security_group)
        self.assertTrue(result)

    def test_ex_create_security_group_rule(self):
        security_group = OpenStackSecurityGroup(
            id=6, tenant_id=None, name=None, description=None, driver=self.driver)
        security_group_rule = self.driver.ex_create_security_group_rule(
            security_group, 'tcp', 14, 16, '0.0.0.0/0')

        self.assertEqual(security_group_rule.id, 2)
        self.assertEqual(security_group_rule.parent_group_id, 6)
        self.assertEqual(security_group_rule.ip_protocol, 'tcp')
        self.assertEqual(security_group_rule.from_port, 14)
        self.assertEqual(security_group_rule.to_port, 16)
        self.assertEqual(security_group_rule.ip_range, '0.0.0.0/0')
        self.assertEqual(security_group_rule.tenant_id, None)

    def test_ex_delete_security_group_rule(self):
        security_group_rule = OpenStackSecurityGroupRule(
            id=2, parent_group_id=None, ip_protocol=None, from_port=None, to_port=None, driver=self.driver)
        result = self.driver.ex_delete_security_group_rule(security_group_rule)
        self.assertTrue(result)

    def test_list_key_pairs(self):
        keypairs = self.driver.list_key_pairs()
        self.assertEqual(len(keypairs), 2, 'Wrong keypairs count')
        keypair = keypairs[1]
        self.assertEqual(keypair.name, 'key2')
        self.assertEqual(
            keypair.fingerprint, '5d:66:33:ae:99:0f:fb:cb:86:f2:bc:ae:53:99:b6:ed')
        self.assertTrue(len(keypair.public_key) > 10)
        self.assertEqual(keypair.private_key, None)

    def test_get_key_pair(self):
        key_pair = self.driver.get_key_pair(name='test-key-pair')

        self.assertEqual(key_pair.name, 'test-key-pair')

    def test_get_key_pair_doesnt_exist(self):
        self.assertRaises(KeyPairDoesNotExistError,
                          self.driver.get_key_pair,
                          name='doesnt-exist')

    def test_create_key_pair(self):
        name = 'key0'
        keypair = self.driver.create_key_pair(name=name)
        self.assertEqual(keypair.name, name)

        self.assertEqual(keypair.fingerprint,
                         '80:f8:03:a7:8e:c1:c3:b1:7e:c5:8c:50:04:5e:1c:5b')
        self.assertTrue(len(keypair.public_key) > 10)
        self.assertTrue(len(keypair.private_key) > 10)

    def test_import_key_pair_from_file(self):
        name = 'key3'
        path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'misc', 'dummy_rsa.pub')
        pub_key = open(path, 'r').read()
        keypair = self.driver.import_key_pair_from_file(name=name,
                                                        key_file_path=path)
        self.assertEqual(keypair.name, name)
        self.assertEqual(
            keypair.fingerprint, '97:10:a6:e7:92:65:7e:69:fe:e6:81:8f:39:3c:8f:5a')
        self.assertEqual(keypair.public_key, pub_key)
        self.assertEqual(keypair.private_key, None)

    def test_import_key_pair_from_string(self):
        name = 'key3'
        path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'misc', 'dummy_rsa.pub')
        pub_key = open(path, 'r').read()
        keypair = self.driver.import_key_pair_from_string(name=name,
                                                          key_material=pub_key)
        self.assertEqual(keypair.name, name)
        self.assertEqual(
            keypair.fingerprint, '97:10:a6:e7:92:65:7e:69:fe:e6:81:8f:39:3c:8f:5a')
        self.assertEqual(keypair.public_key, pub_key)
        self.assertEqual(keypair.private_key, None)

    def test_delete_key_pair(self):
        keypair = OpenStackKeyPair(
            name='key1', fingerprint=None, public_key=None, driver=self.driver)
        result = self.driver.delete_key_pair(key_pair=keypair)
        self.assertTrue(result)

    def test_ex_list_floating_ip_pools(self):
        ret = self.driver.ex_list_floating_ip_pools()
        self.assertEqual(ret[0].name, 'public')
        self.assertEqual(ret[1].name, 'foobar')

    def test_ex_attach_floating_ip_to_node(self):
        image = NodeImage(
            id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size)
        node.id = 4242
        ip = '42.42.42.42'

        self.assertTrue(self.driver.ex_attach_floating_ip_to_node(node, ip))

    def test_detach_floating_ip_from_node(self):
        image = NodeImage(
            id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(
            1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='racktest', image=image, size=size)
        node.id = 4242
        ip = '42.42.42.42'

        self.assertTrue(self.driver.ex_detach_floating_ip_from_node(node, ip))

    def test_OpenStack_1_1_FloatingIpPool_list_floating_ips(self):
        pool = OpenStack_1_1_FloatingIpPool('foo', self.driver.connection)
        ret = pool.list_floating_ips()

        self.assertEqual(ret[0].id, '09ea1784-2f81-46dc-8c91-244b4df75bde')
        self.assertEqual(ret[0].pool, pool)
        self.assertEqual(ret[0].ip_address, '10.3.1.42')
        self.assertEqual(ret[0].node_id, None)
        self.assertEqual(ret[1].id, '04c5336a-0629-4694-ba30-04b0bdfa88a4')
        self.assertEqual(ret[1].pool, pool)
        self.assertEqual(ret[1].ip_address, '10.3.1.1')
        self.assertEqual(
            ret[1].node_id, 'fcfc96da-19e2-40fd-8497-f29da1b21143')

    def test_OpenStack_1_1_FloatingIpPool_get_floating_ip(self):
        pool = OpenStack_1_1_FloatingIpPool('foo', self.driver.connection)
        ret = pool.get_floating_ip('10.3.1.42')

        self.assertEqual(ret.id, '09ea1784-2f81-46dc-8c91-244b4df75bde')
        self.assertEqual(ret.pool, pool)
        self.assertEqual(ret.ip_address, '10.3.1.42')
        self.assertEqual(ret.node_id, None)

    def test_OpenStack_1_1_FloatingIpPool_create_floating_ip(self):
        pool = OpenStack_1_1_FloatingIpPool('foo', self.driver.connection)
        ret = pool.create_floating_ip()

        self.assertEqual(ret.id, '09ea1784-2f81-46dc-8c91-244b4df75bde')
        self.assertEqual(ret.pool, pool)
        self.assertEqual(ret.ip_address, '10.3.1.42')
        self.assertEqual(ret.node_id, None)

    def test_OpenStack_1_1_FloatingIpPool_delete_floating_ip(self):
        pool = OpenStack_1_1_FloatingIpPool('foo', self.driver.connection)
        ip = OpenStack_1_1_FloatingIpAddress('foo-bar-id', '42.42.42.42', pool)

        self.assertTrue(pool.delete_floating_ip(ip))

    def test_OpenStack_1_1_FloatingIpAddress_delete(self):
        pool = OpenStack_1_1_FloatingIpPool('foo', self.driver.connection)
        pool.delete_floating_ip = Mock()
        ip = OpenStack_1_1_FloatingIpAddress('foo-bar-id', '42.42.42.42', pool)

        ip.pool.delete_floating_ip()

        self.assertEqual(pool.delete_floating_ip.call_count, 1)

    def test_ex_list_network(self):
        networks = self.driver.ex_list_networks()
        network = networks[0]

        self.assertEqual(len(networks), 3)
        self.assertEqual(network.name, 'test1')
        self.assertEqual(network.cidr, '127.0.0.0/24')

    def test_ex_create_network(self):
        network = self.driver.ex_create_network(name='test1',
                                                cidr='127.0.0.0/24')
        self.assertEqual(network.name, 'test1')
        self.assertEqual(network.cidr, '127.0.0.0/24')

    def test_ex_delete_network(self):
        network = self.driver.ex_list_networks()[0]
        self.assertTrue(self.driver.ex_delete_network(network=network))

    def test_ex_get_metadata_for_node(self):
        image = NodeImage(id=11, name='Ubuntu 8.10 (intrepid)', driver=self.driver)
        size = NodeSize(1, '256 slice', None, None, None, None, driver=self.driver)
        node = self.driver.create_node(name='foo',
                                       image=image,
                                       size=size)

        metadata = self.driver.ex_get_metadata_for_node(node)
        self.assertEqual(metadata['My Server Name'], 'Apache1')
        self.assertEqual(len(metadata), 1)

    def test_ex_pause_node(self):
        node = Node(
            id='12063', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        ret = self.driver.ex_pause_node(node)
        self.assertTrue(ret is True)

    def test_ex_unpause_node(self):
        node = Node(
            id='12063', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        ret = self.driver.ex_unpause_node(node)
        self.assertTrue(ret is True)

    def test_ex_suspend_node(self):
        node = Node(
            id='12063', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        ret = self.driver.ex_suspend_node(node)
        self.assertTrue(ret is True)

    def test_ex_resume_node(self):
        node = Node(
            id='12063', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        ret = self.driver.ex_resume_node(node)
        self.assertTrue(ret is True)

    def test_ex_get_console_output(self):
        node = Node(
            id='12086', name=None, state=None,
            public_ips=None, private_ips=None, driver=self.driver,
        )
        resp = self.driver.ex_get_console_output(node)
        expected_output = 'FAKE CONSOLE OUTPUT\nANOTHER\nLAST LINE'
        self.assertEqual(resp['output'], expected_output)

    def test_ex_list_snapshots(self):
        if self.driver_type.type == 'rackspace':
            self.conn_classes[0].type = 'RACKSPACE'
            self.conn_classes[1].type = 'RACKSPACE'

        snapshots = self.driver.ex_list_snapshots()
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(snapshots[0].extra['name'], 'snap-001')

    def test_ex_create_snapshot(self):
        volume = self.driver.list_volumes()[0]
        if self.driver_type.type == 'rackspace':
            self.conn_classes[0].type = 'RACKSPACE'
            self.conn_classes[1].type = 'RACKSPACE'

        ret = self.driver.ex_create_snapshot(volume,
                                             'Test Volume',
                                             'This is a test')
        self.assertEqual(ret.id, '3fbbcccf-d058-4502-8844-6feeffdf4cb5')

    def test_ex_delete_snapshot(self):
        if self.driver_type.type == 'rackspace':
            self.conn_classes[0].type = 'RACKSPACE'
            self.conn_classes[1].type = 'RACKSPACE'

        snapshot = self.driver.ex_list_snapshots()[0]
        ret = self.driver.ex_delete_snapshot(snapshot)
        self.assertTrue(ret)


class OpenStack_1_1_FactoryMethodTests(OpenStack_1_1_Tests):
    should_list_locations = False
    should_list_volumes = True

    driver_klass = OpenStack_1_1_NodeDriver
    driver_type = get_driver(Provider.OPENSTACK)
    driver_args = OPENSTACK_PARAMS + ('1.1',)
    driver_kwargs = {'ex_force_auth_version': '2.0'}


class OpenStack_1_1_MockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('openstack_v1.1')
    auth_fixtures = OpenStackFixtures()
    json_content_headers = {'content-type': 'application/json; charset=UTF-8'}

    def _v2_0_tokens(self, method, url, body, headers):
        body = self.auth_fixtures.load('_v2_0__auth.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_0(self, method, url, body, headers):
        headers = {
            'x-auth-token': 'FE011C19-CF86-4F87-BE5D-9229145D7A06',
            'x-server-management-url': 'https://api.example.com/v1.1/slug',
        }
        return (httplib.NO_CONTENT, "", headers, httplib.responses[httplib.NO_CONTENT])

    def _v1_1_slug_servers_detail(self, method, url, body, headers):
        body = self.fixtures.load('_servers_detail.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_detail_ERROR_STATE_NO_IMAGE_ID(self, method, url, body, headers):
        body = self.fixtures.load('_servers_detail_ERROR_STATE.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_flavors_detail(self, method, url, body, headers):
        body = self.fixtures.load('_flavors_detail.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_images_detail(self, method, url, body, headers):
        body = self.fixtures.load('_images_detail.json')
        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers(self, method, url, body, headers):
        if method == "POST":
            body = self.fixtures.load('_servers_create.json')
        elif method == "GET":
            body = self.fixtures.load('_servers.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_26f7fbee_8ce1_4c28_887a_bfe8e4bb10fe(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                '_servers_26f7fbee_8ce1_4c28_887a_bfe8e4bb10fe.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_12065_action(self, method, url, body, headers):
        if method != "POST":
            self.fail('HTTP method other than POST to action URL')

        return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

    def _v1_1_slug_servers_12064_action(self, method, url, body, headers):
        if method != "POST":
            self.fail('HTTP method other than POST to action URL')
        if "createImage" in json.loads(body):
            return (httplib.ACCEPTED, "",
                    {"location": "http://127.0.0.1/v1.1/68/images/4949f9ee-2421-4c81-8b49-13119446008b"},
                    httplib.responses[httplib.ACCEPTED])
        elif "rescue" in json.loads(body):
            return (httplib.OK, '{"adminPass": "foo"}', {},
                    httplib.responses[httplib.OK])

        return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

    def _v1_1_slug_servers_12066_action(self, method, url, body, headers):
        if method != "POST":
            self.fail('HTTP method other than POST to action URL')
        if "rebuild" not in json.loads(body):
            self.fail("Did not get expected action (rebuild) in action URL")

        self.assertTrue('\"OS-DCF:diskConfig\": \"MANUAL\"' in body,
                        msg="Manual disk configuration option was not specified in rebuild body: " + body)

        return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])

    def _v1_1_slug_servers_12065(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        else:
            raise NotImplementedError()

    def _v1_1_slug_servers_12064(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_servers_12064.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        elif method == "PUT":
            body = self.fixtures.load('_servers_12064_updated_name_bob.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        elif method == "DELETE":
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        else:
            raise NotImplementedError()

    def _v1_1_slug_servers_12062(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_servers_12064.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_12063_metadata(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_servers_12063_metadata_two_keys.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        elif method == "PUT":
            body = self.fixtures.load('_servers_12063_metadata_two_keys.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_EX_DISK_CONFIG(self, method, url, body, headers):
        if method == "POST":
            body = u(body)
            self.assertTrue(body.find('\"OS-DCF:diskConfig\": \"AUTO\"'))
            body = self.fixtures.load('_servers_create_disk_config.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_flavors_7(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_flavors_7.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_images_13(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_images_13.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_images_26365521_8c62_11f9_2c33_283d153ecc3a(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.NO_CONTENT, "", {}, httplib.responses[httplib.NO_CONTENT])
        else:
            raise NotImplementedError()

    def _v1_1_slug_images_4949f9ee_2421_4c81_8b49_13119446008b(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                '_images_4949f9ee_2421_4c81_8b49_13119446008b.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_servers_1c01300f_ef97_4937_8f03_ac676d6234be_os_security_groups(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                '_servers_1c01300f-ef97-4937-8f03-ac676d6234be_os-security-groups.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_security_groups(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_os_security_groups.json')
        elif method == "POST":
            body = self.fixtures.load('_os_security_groups_create.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_security_groups_6(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.NO_CONTENT, "", {}, httplib.responses[httplib.NO_CONTENT])
        else:
            raise NotImplementedError()

    def _v1_1_slug_os_security_group_rules(self, method, url, body, headers):
        if method == "POST":
            body = self.fixtures.load('_os_security_group_rules_create.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_security_group_rules_2(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.NO_CONTENT, "", {}, httplib.responses[httplib.NO_CONTENT])
        else:
            raise NotImplementedError()

    def _v1_1_slug_os_keypairs(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_os_keypairs.json')
        elif method == "POST":
            if 'public_key' in body:
                body = self.fixtures.load('_os_keypairs_create_import.json')
            else:
                body = self.fixtures.load('_os_keypairs_create.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_keypairs_test_key_pair(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('_os_keypairs_get_one.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_keypairs_doesnt_exist(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('_os_keypairs_not_found.json')
        else:
            raise NotImplementedError()

        return (httplib.NOT_FOUND, body, self.json_content_headers,
                httplib.responses[httplib.NOT_FOUND])

    def _v1_1_slug_os_keypairs_key1(self, method, url, body, headers):
        if method == "DELETE":
            return (httplib.ACCEPTED, "", {}, httplib.responses[httplib.ACCEPTED])
        else:
            raise NotImplementedError()

    def _v1_1_slug_os_volumes(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_os_volumes.json')
        elif method == "POST":
            body = self.fixtures.load('_os_volumes_create.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_volumes_cd76a3a1_c4ce_40f6_9b9f_07a61508938d(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load(
                '_os_volumes_cd76a3a1_c4ce_40f6_9b9f_07a61508938d.json')
        elif method == "DELETE":
            body = ''
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_12065_os_volume_attachments(self, method, url, body, headers):
        if method == "POST":
            body = self.fixtures.load(
                '_servers_12065_os_volume_attachments.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_12065_os_volume_attachments_cd76a3a1_c4ce_40f6_9b9f_07a61508938d(self, method, url, body,
                                                                                            headers):
        if method == "DELETE":
            body = ''
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_floating_ip_pools(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_floating_ip_pools.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_os_floating_ips_foo_bar_id(self, method, url, body, headers):
        if method == "DELETE":
            body = ''
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_os_floating_ips(self, method, url, body, headers):
        if method == "GET":
            body = self.fixtures.load('_floating_ips.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        elif method == "POST":
            body = self.fixtures.load('_floating_ip.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_servers_4242_action(self, method, url, body, headers):
        if method == "POST":
            body = ''
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_networks(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('_os_networks.json')
            return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])
        elif method == 'POST':
            body = self.fixtures.load('_os_networks_POST.json')
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        raise NotImplementedError()

    def _v1_1_slug_os_networks_f13e5051_feea_416b_827a_1a0acc2dad14(self, method, url, body, headers):
        if method == 'DELETE':
            body = ''
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        raise NotImplementedError()

    def _v1_1_slug_servers_72258_action(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('_servers_suspend.json')
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_12063_action(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('_servers_unpause.json')
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_servers_12086_action(self, method, url, body, headers):
        if method == 'POST':
            body = self.fixtures.load('_servers_12086_console_output.json')
            return (httplib.ACCEPTED, body, self.json_content_headers, httplib.responses[httplib.OK])
        else:
            raise NotImplementedError()

    def _v1_1_slug_os_snapshots(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('_os_snapshots.json')
        elif method == 'POST':
            body = self.fixtures.load('_os_snapshots_create.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_snapshots_RACKSPACE(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('_os_snapshots_rackspace.json')
        elif method == 'POST':
            body = self.fixtures.load('_os_snapshots_create_rackspace.json')
        else:
            raise NotImplementedError()

        return (httplib.OK, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_snapshots_3fbbcccf_d058_4502_8844_6feeffdf4cb5(self, method, url, body, headers):
        if method == 'DELETE':
            body = ''
            status_code = httplib.NO_CONTENT
        else:
            raise NotImplementedError()

        return (status_code, body, self.json_content_headers, httplib.responses[httplib.OK])

    def _v1_1_slug_os_snapshots_3fbbcccf_d058_4502_8844_6feeffdf4cb5_RACKSPACE(self, method, url, body, headers):
        if method == 'DELETE':
            body = ''
            status_code = httplib.NO_CONTENT
        else:
            raise NotImplementedError()

        return (status_code, body, self.json_content_headers, httplib.responses[httplib.OK])


# This exists because the nova compute url in devstack has v2 in there but the v1.1 fixtures
# work fine.


class OpenStack_2_0_MockHttp(OpenStack_1_1_MockHttp):

    def __init__(self, *args, **kwargs):
        super(OpenStack_2_0_MockHttp, self).__init__(*args, **kwargs)

        methods1 = OpenStack_1_1_MockHttp.__dict__

        names1 = [m for m in methods1 if m.find('_v1_1') == 0]

        for name in names1:
            method = methods1[name]
            new_name = name.replace('_v1_1_slug_', '_v2_1337_')
            setattr(self, new_name, method_type(method, self,
                                                OpenStack_2_0_MockHttp))


class OpenStack_1_1_Auth_2_0_Tests(OpenStack_1_1_Tests):
    driver_args = OPENSTACK_PARAMS + ('1.1',)
    driver_kwargs = {'ex_force_auth_version': '2.0'}

    def setUp(self):
        self.driver_klass.connectionCls.conn_classes = \
            (OpenStack_2_0_MockHttp, OpenStack_2_0_MockHttp)
        self.driver_klass.connectionCls.auth_url = "https://auth.api.example.com"
        OpenStackMockHttp.type = None
        OpenStack_1_1_MockHttp.type = None
        OpenStack_2_0_MockHttp.type = None
        self.driver = self.create_driver()
        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()
        clear_pricing_data()
        self.node = self.driver.list_nodes()[1]

    def test_auth_user_info_is_set(self):
        self.driver.connection._populate_hosts_and_request_paths()
        self.assertEqual(self.driver.connection.auth_user_info, {
            'id': '7',
            'name': 'testuser',
            'roles': [{'description': 'Default Role.',
                       'id': 'identity:default',
                       'name': 'identity:default'}]})


if __name__ == '__main__':
    sys.exit(unittest.main())
