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

from keystoneclient import access
from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient.tests.unit.v3 import client_fixtures
from keystoneclient.tests.unit.v3 import utils


class ServiceCatalogTest(utils.TestCase):
    def setUp(self):
        super(ServiceCatalogTest, self).setUp()
        self.AUTH_RESPONSE_BODY = client_fixtures.auth_response_body()
        self.RESPONSE = utils.TestResponse({
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })

        self.north_endpoints = {'public':
                                'http://glance.north.host/glanceapi/public',
                                'internal':
                                'http://glance.north.host/glanceapi/internal',
                                'admin':
                                'http://glance.north.host/glanceapi/admin'}

        self.south_endpoints = {'public':
                                'http://glance.south.host/glanceapi/public',
                                'internal':
                                'http://glance.south.host/glanceapi/internal',
                                'admin':
                                'http://glance.south.host/glanceapi/admin'}

    def test_building_a_service_catalog(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        self.assertEqual(sc.url_for(service_type='compute'),
                         "https://compute.north.host/novapi/public")
        self.assertEqual(sc.url_for(service_type='compute',
                                    endpoint_type='internal'),
                         "https://compute.north.host/novapi/internal")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, "region",
                          "South", service_type='compute')

    def test_service_catalog_endpoints(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='public')
        self.assertEqual(public_ep['compute'][0]['region'], 'North')
        self.assertEqual(public_ep['compute'][0]['url'],
                         "https://compute.north.host/novapi/public")

    def test_service_catalog_regions(self):
        self.AUTH_RESPONSE_BODY['token']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='public')
        self.assertEqual(url, "http://glance.north.host/glanceapi/public")

        self.AUTH_RESPONSE_BODY['token']['region_name'] = "South"
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog
        url = sc.url_for(service_type='image', endpoint_type='internal')
        self.assertEqual(url, "http://glance.south.host/glanceapi/internal")

    def test_service_catalog_empty(self):
        self.AUTH_RESPONSE_BODY['token']['catalog'] = []
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        self.assertRaises(exceptions.EmptyCatalog,
                          auth_ref.service_catalog.url_for,
                          service_type='image',
                          endpoint_type='internalURL')

    def test_service_catalog_get_endpoints_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        endpoints = sc.get_endpoints(service_type='image', region_name='North')
        self.assertEqual(len(endpoints), 1)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.north_endpoints[endpoint['interface']])

        endpoints = sc.get_endpoints(service_type='image', region_name='South')
        self.assertEqual(len(endpoints), 1)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.south_endpoints[endpoint['interface']])

        endpoints = sc.get_endpoints(service_type='compute')
        self.assertEqual(len(endpoints['compute']), 3)

        endpoints = sc.get_endpoints(service_type='compute',
                                     region_name='North')
        self.assertEqual(len(endpoints['compute']), 3)

        endpoints = sc.get_endpoints(service_type='compute',
                                     region_name='West')
        self.assertEqual(len(endpoints['compute']), 0)

    def test_service_catalog_url_for_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', region_name='North')
        self.assertEqual(url, self.north_endpoints['public'])

        url = sc.url_for(service_type='image', region_name='South')
        self.assertEqual(url, self.south_endpoints['public'])

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          service_type='image', region_name='West')

    def test_servcie_catalog_get_url_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        urls = sc.get_urls(service_type='image')
        self.assertEqual(len(urls), 2)

        urls = sc.get_urls(service_type='image', region_name='North')
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], self.north_endpoints['public'])

        urls = sc.get_urls(service_type='image', region_name='South')
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], self.south_endpoints['public'])

        urls = sc.get_urls(service_type='image', region_name='West')
        self.assertIsNone(urls)

    def test_service_catalog_param_overrides_body_region(self):
        self.AUTH_RESPONSE_BODY['token']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image')
        self.assertEqual(url, self.north_endpoints['public'])

        url = sc.url_for(service_type='image', region_name='South')
        self.assertEqual(url, self.south_endpoints['public'])

        endpoints = sc.get_endpoints(service_type='image')
        self.assertEqual(len(endpoints['image']), 3)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.north_endpoints[endpoint['interface']])

        endpoints = sc.get_endpoints(service_type='image', region_name='South')
        self.assertEqual(len(endpoints['image']), 3)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.south_endpoints[endpoint['interface']])

    def test_service_catalog_service_name(self):
        auth_ref = access.AccessInfo.factory(resp=None,
                                             body=self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_name='glance', endpoint_type='public',
                         service_type='image', region_name='North')
        self.assertEqual('http://glance.north.host/glanceapi/public', url)

        url = sc.url_for(service_name='glance', endpoint_type='public',
                         service_type='image', region_name='South')
        self.assertEqual('http://glance.south.host/glanceapi/public', url)

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          service_name='glance', service_type='compute')

        urls = sc.get_urls(service_type='image', service_name='glance',
                           endpoint_type='public')

        self.assertIn('http://glance.north.host/glanceapi/public', urls)
        self.assertIn('http://glance.south.host/glanceapi/public', urls)

        urls = sc.get_urls(service_type='image', service_name='Servers',
                           endpoint_type='public')

        self.assertIsNone(urls)

    def test_service_catalog_without_name(self):
        pr_auth_ref = access.AccessInfo.factory(
            resp=None,
            body=client_fixtures.project_scoped_token())
        pr_sc = pr_auth_ref.service_catalog

        # this will work because there are no service names on that token
        url_ref = 'http://public.com:8774/v2/225da22d3ce34b15877ea70b2a575f58'
        url = pr_sc.url_for(service_type='compute', service_name='NotExist',
                            endpoint_type='public')
        self.assertEqual(url_ref, url)

        ab_auth_ref = access.AccessInfo.factory(resp=None,
                                                body=self.AUTH_RESPONSE_BODY)
        ab_sc = ab_auth_ref.service_catalog

        # this won't work because there is a name and it's not this one
        self.assertRaises(exceptions.EndpointNotFound, ab_sc.url_for,
                          service_type='compute', service_name='NotExist',
                          endpoint_type='public')


class ServiceCatalogV3Test(ServiceCatalogTest):

    def test_building_a_service_catalog(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        self.assertEqual(sc.url_for(service_type='compute'),
                         'https://compute.north.host/novapi/public')
        self.assertEqual(sc.url_for(service_type='compute',
                                    endpoint_type='internal'),
                         'https://compute.north.host/novapi/internal')

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, 'region_id',
                          'South', service_type='compute')

    def test_service_catalog_endpoints(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='public')
        self.assertEqual(public_ep['compute'][0]['region_id'], 'North')
        self.assertEqual(public_ep['compute'][0]['url'],
                         'https://compute.north.host/novapi/public')

    def test_service_catalog_multiple_service_types(self):
        token = fixture.V3Token()
        token.set_project_scope()

        for i in range(3):
            s = token.add_service('compute')
            s.add_standard_endpoints(public='public-%d' % i,
                                     admin='admin-%d' % i,
                                     internal='internal-%d' % i,
                                     region='region-%d' % i)

        auth_ref = access.AccessInfo.factory(resp=None, body=token)

        urls = auth_ref.service_catalog.get_urls(service_type='compute',
                                                 endpoint_type='public')

        self.assertEqual(set(['public-0', 'public-1', 'public-2']), set(urls))

        urls = auth_ref.service_catalog.get_urls(service_type='compute',
                                                 endpoint_type='public',
                                                 region_name='region-1')

        self.assertEqual(('public-1', ), urls)
