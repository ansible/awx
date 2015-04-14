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

from keystoneclient import access
from keystoneclient import exceptions
from keystoneclient import fixture
from keystoneclient.tests.unit.v2_0 import client_fixtures
from keystoneclient.tests.unit.v2_0 import utils


class ServiceCatalogTest(utils.TestCase):
    def setUp(self):
        super(ServiceCatalogTest, self).setUp()
        self.AUTH_RESPONSE_BODY = client_fixtures.auth_response_body()

    def test_building_a_service_catalog(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        self.assertEqual(sc.url_for(service_type='compute'),
                         "https://compute.north.host/v1/1234")
        self.assertEqual(sc.url_for('tenantId', '1', service_type='compute'),
                         "https://compute.north.host/v1/1234")
        self.assertEqual(sc.url_for('tenantId', '2', service_type='compute'),
                         "https://compute.north.host/v1.1/3456")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, "region",
                          "South", service_type='compute')

    def test_service_catalog_endpoints(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog
        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='publicURL')
        self.assertEqual(public_ep['compute'][1]['tenantId'], '2')
        self.assertEqual(public_ep['compute'][1]['versionId'], '1.1')
        self.assertEqual(public_ep['compute'][1]['internalURL'],
                         "https://compute.north.host/v1.1/3456")

    def test_service_catalog_regions(self):
        self.AUTH_RESPONSE_BODY['access']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='publicURL')
        self.assertEqual(url, "https://image.north.host/v1/")

        self.AUTH_RESPONSE_BODY['access']['region_name'] = "South"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='internalURL')
        self.assertEqual(url, "https://image-internal.south.host/v1/")

    def test_service_catalog_empty(self):
        self.AUTH_RESPONSE_BODY['access']['serviceCatalog'] = []
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        self.assertRaises(exceptions.EmptyCatalog,
                          auth_ref.service_catalog.url_for,
                          service_type='image',
                          endpoint_type='internalURL')

    def test_service_catalog_get_endpoints_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        endpoints = sc.get_endpoints(service_type='image', region_name='North')
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints['image'][0]['publicURL'],
                         'https://image.north.host/v1/')

        endpoints = sc.get_endpoints(service_type='image', region_name='South')
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints['image'][0]['publicURL'],
                         'https://image.south.host/v1/')

        endpoints = sc.get_endpoints(service_type='compute')
        self.assertEqual(len(endpoints['compute']), 2)

        endpoints = sc.get_endpoints(service_type='compute',
                                     region_name='North')
        self.assertEqual(len(endpoints['compute']), 2)

        endpoints = sc.get_endpoints(service_type='compute',
                                     region_name='West')
        self.assertEqual(len(endpoints['compute']), 0)

    def test_service_catalog_url_for_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', region_name='North')
        self.assertEqual(url, 'https://image.north.host/v1/')

        url = sc.url_for(service_type='image', region_name='South')
        self.assertEqual(url, 'https://image.south.host/v1/')

        url = sc.url_for(service_type='compute',
                         region_name='North',
                         attr='versionId',
                         filter_value='1.1')
        self.assertEqual(url, 'https://compute.north.host/v1.1/3456')

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          service_type='image', region_name='West')

    def test_servcie_catalog_get_url_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        urls = sc.get_urls(service_type='image')
        self.assertEqual(len(urls), 2)

        urls = sc.get_urls(service_type='image', region_name='North')
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], 'https://image.north.host/v1/')

        urls = sc.get_urls(service_type='image', region_name='South')
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], 'https://image.south.host/v1/')

        urls = sc.get_urls(service_type='image', region_name='West')
        self.assertIsNone(urls)

    def test_service_catalog_param_overrides_body_region(self):
        self.AUTH_RESPONSE_BODY['access']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image')
        self.assertEqual(url, 'https://image.north.host/v1/')

        url = sc.url_for(service_type='image', region_name='South')
        self.assertEqual(url, 'https://image.south.host/v1/')

        endpoints = sc.get_endpoints(service_type='image')
        self.assertEqual(len(endpoints['image']), 1)
        self.assertEqual(endpoints['image'][0]['publicURL'],
                         'https://image.north.host/v1/')

        endpoints = sc.get_endpoints(service_type='image', region_name='South')
        self.assertEqual(len(endpoints['image']), 1)
        self.assertEqual(endpoints['image'][0]['publicURL'],
                         'https://image.south.host/v1/')

    def test_service_catalog_service_name(self):
        auth_ref = access.AccessInfo.factory(resp=None,
                                             body=self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_name='Image Servers', endpoint_type='public',
                         service_type='image', region_name='North')
        self.assertEqual('https://image.north.host/v1/', url)

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          service_name='Image Servers', service_type='compute')

        urls = sc.get_urls(service_type='image', service_name='Image Servers',
                           endpoint_type='public')

        self.assertIn('https://image.north.host/v1/', urls)
        self.assertIn('https://image.south.host/v1/', urls)

        urls = sc.get_urls(service_type='image', service_name='Servers',
                           endpoint_type='public')

        self.assertIsNone(urls)

    def test_service_catalog_multiple_service_types(self):
        token = fixture.V2Token()
        token.set_scope()

        for i in range(3):
            s = token.add_service('compute')
            s.add_endpoint(public='public-%d' % i,
                           admin='admin-%d' % i,
                           internal='internal-%d' % i,
                           region='region-%d' % i)

        auth_ref = access.AccessInfo.factory(resp=None, body=token)

        urls = auth_ref.service_catalog.get_urls(service_type='compute',
                                                 endpoint_type='publicURL')

        self.assertEqual(set(['public-0', 'public-1', 'public-2']), set(urls))

        urls = auth_ref.service_catalog.get_urls(service_type='compute',
                                                 endpoint_type='publicURL',
                                                 region_name='region-1')

        self.assertEqual(('public-1', ), urls)
