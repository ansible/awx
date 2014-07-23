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

from libcloud.utils.py3 import method_type
from libcloud.utils.py3 import httplib
from libcloud.compute.providers import DEPRECATED_RACKSPACE_PROVIDERS
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.rackspace import RackspaceFirstGenNodeDriver
from libcloud.compute.drivers.rackspace import RackspaceNodeDriver
from libcloud.test.compute.test_openstack import OpenStack_1_0_Tests
from libcloud.test.compute.test_openstack import OpenStack_1_1_Tests, \
    OpenStack_1_1_MockHttp
from libcloud.pricing import clear_pricing_data

from libcloud.test.secrets import RACKSPACE_NOVA_PARAMS
from libcloud.test.secrets import RACKSPACE_PARAMS


class RackspaceusFirstGenUsTests(OpenStack_1_0_Tests):
    should_list_locations = True
    should_have_pricing = True

    driver_klass = RackspaceFirstGenNodeDriver
    driver_type = RackspaceFirstGenNodeDriver
    driver_args = RACKSPACE_PARAMS
    driver_kwargs = {'region': 'us'}

    def test_error_is_thrown_on_accessing_old_constant(self):
        for provider in DEPRECATED_RACKSPACE_PROVIDERS:
            try:
                get_driver(provider)
            except Exception:
                e = sys.exc_info()[1]
                self.assertTrue(str(e).find('has been removed') != -1)
            else:
                self.fail('Exception was not thrown')

    def test_list_sizes_pricing(self):
        sizes = self.driver.list_sizes()

        for size in sizes:
            self.assertTrue(size.price > 0)


class RackspaceusFirstGenUkTests(OpenStack_1_0_Tests):
    should_list_locations = True
    should_have_pricing = True

    driver_klass = RackspaceFirstGenNodeDriver
    driver_type = RackspaceFirstGenNodeDriver
    driver_args = RACKSPACE_PARAMS
    driver_kwargs = {'region': 'uk'}

    def test_list_sizes_pricing(self):
        sizes = self.driver.list_sizes()

        for size in sizes:
            self.assertTrue(size.price > 0)


class RackspaceNovaMockHttp(OpenStack_1_1_MockHttp):

    def __init__(self, *args, **kwargs):
        super(RackspaceNovaMockHttp, self).__init__(*args, **kwargs)

        methods1 = OpenStack_1_1_MockHttp.__dict__

        names1 = [m for m in methods1 if m.find('_v1_1') == 0]

        for name in names1:
            method = methods1[name]
            new_name = name.replace('_v1_1_slug_', '_v2_1337_')
            setattr(self, new_name, method_type(method, self,
                                                RackspaceNovaMockHttp))

    def _v2_1337_os_networksv2(self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('_os_networks.json')
            return (httplib.OK, body, self.json_content_headers,
                    httplib.responses[httplib.OK])
        elif method == 'POST':
            body = self.fixtures.load('_os_networks_POST.json')
            return (httplib.ACCEPTED, body, self.json_content_headers,
                    httplib.responses[httplib.OK])
        raise NotImplementedError()

    def _v2_1337_os_networksv2_f13e5051_feea_416b_827a_1a0acc2dad14(self,
                                                                    method,
                                                                    url, body,
                                                                    headers):
        if method == 'DELETE':
            body = ''
            return (httplib.ACCEPTED, body, self.json_content_headers,
                    httplib.responses[httplib.OK])
        raise NotImplementedError()


class RackspaceNovaLonMockHttp(RackspaceNovaMockHttp):

    def _v2_0_tokens(self, method, url, body, headers):
        body = self.auth_fixtures.load('_v2_0__auth_lon.json')
        return (httplib.OK, body, self.json_content_headers,
                httplib.responses[httplib.OK])


class BaseRackspaceNovaTestCase(object):
    conn_classes = (RackspaceNovaMockHttp, RackspaceNovaMockHttp)
    auth_url = 'https://auth.api.example.com'

    def create_driver(self):
        return self.driver_type(*self.driver_args, **self.driver_kwargs)

    def setUp(self):
        self.driver_klass.connectionCls.conn_classes = self.conn_classes
        self.driver_klass.connectionCls.auth_url = self.auth_url
        self.conn_classes[0].type = None
        self.conn_classes[1].type = None
        self.driver = self.create_driver()
        # normally authentication happens lazily, but we force it here
        self.driver.connection._populate_hosts_and_request_paths()
        clear_pricing_data()
        self.node = self.driver.list_nodes()[1]

    def test_service_catalog_contais_right_endpoint(self):
        self.assertEqual(self.driver.connection.get_endpoint(),
                         self.expected_endpoint)

    def test_list_sizes_pricing(self):
        sizes = self.driver.list_sizes()

        for size in sizes:
            if size.ram > 256:
                self.assertTrue(size.price > 0)


class RackspaceNovaDfwTests(BaseRackspaceNovaTestCase, OpenStack_1_1_Tests):

    driver_klass = RackspaceNodeDriver
    driver_type = RackspaceNodeDriver
    driver_args = RACKSPACE_NOVA_PARAMS
    driver_kwargs = {'region': 'dfw'}

    expected_endpoint = 'https://dfw.servers.api.rackspacecloud.com/v2/1337'


class RackspaceNovaOrdTests(BaseRackspaceNovaTestCase, OpenStack_1_1_Tests):

    driver_klass = RackspaceNodeDriver
    driver_type = RackspaceNodeDriver
    driver_args = RACKSPACE_NOVA_PARAMS
    driver_kwargs = {'region': 'ord'}

    expected_endpoint = 'https://ord.servers.api.rackspacecloud.com/v2/1337'


class RackspaceNovaIadTests(BaseRackspaceNovaTestCase, OpenStack_1_1_Tests):

    driver_klass = RackspaceNodeDriver
    driver_type = RackspaceNodeDriver
    driver_args = RACKSPACE_NOVA_PARAMS
    driver_kwargs = {'region': 'iad'}

    expected_endpoint = 'https://iad.servers.api.rackspacecloud.com/v2/1337'


class RackspaceNovaLonTests(BaseRackspaceNovaTestCase, OpenStack_1_1_Tests):

    driver_klass = RackspaceNodeDriver
    driver_type = RackspaceNodeDriver
    driver_args = RACKSPACE_NOVA_PARAMS
    driver_kwargs = {'region': 'lon'}

    conn_classes = (RackspaceNovaLonMockHttp, RackspaceNovaLonMockHttp)
    auth_url = 'https://lon.auth.api.example.com'

    expected_endpoint = 'https://lon.servers.api.rackspacecloud.com/v2/1337'


class RackspaceNovaSydTests(BaseRackspaceNovaTestCase, OpenStack_1_1_Tests):

    driver_klass = RackspaceNodeDriver
    driver_type = RackspaceNodeDriver
    driver_args = RACKSPACE_NOVA_PARAMS
    driver_kwargs = {'region': 'syd'}

    expected_endpoint = 'https://syd.servers.api.rackspacecloud.com/v2/1337'


class RackspaceNovaHkgTests(BaseRackspaceNovaTestCase, OpenStack_1_1_Tests):

    driver_klass = RackspaceNodeDriver
    driver_type = RackspaceNodeDriver
    driver_args = RACKSPACE_NOVA_PARAMS
    driver_kwargs = {'region': 'hkg'}

    expected_endpoint = 'https://hkg.servers.api.rackspacecloud.com/v2/1337'

if __name__ == '__main__':
    sys.exit(unittest.main())
