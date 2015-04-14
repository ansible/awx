# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cinderclient import exceptions
from cinderclient import service_catalog
from cinderclient.tests import utils


# Taken directly from keystone/content/common/samples/auth.json
# Do not edit this structure. Instead, grab the latest from there.

SERVICE_CATALOG = {
    "access": {
        "token": {
            "id": "ab48a9efdfedb23ty3494",
            "expires": "2010-11-01T03:32:15-05:00",
            "tenant": {
                "id": "345",
                "name": "My Project"
            }
        },
        "user": {
            "id": "123",
            "name": "jqsmith",
            "roles": [
                {
                    "id": "234",
                    "name": "compute:admin",
                },
                {
                    "id": "235",
                    "name": "object-store:admin",
                    "tenantId": "1",
                }
            ],
            "roles_links": [],
        },
        "serviceCatalog": [
            {
                "name": "Cloud Servers",
                "type": "compute",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://compute1.host/v1/1234",
                        "internalURL": "https://compute1.host/v1/1234",
                        "region": "North",
                        "versionId": "1.0",
                        "versionInfo": "https://compute1.host/v1/",
                        "versionList": "https://compute1.host/"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://compute1.host/v1/3456",
                        "internalURL": "https://compute1.host/v1/3456",
                        "region": "North",
                        "versionId": "1.1",
                        "versionInfo": "https://compute1.host/v1/",
                        "versionList": "https://compute1.host/"
                    },
                ],
                "endpoints_links": [],
            },
            {
                "name": "Cinder Volume Service",
                "type": "volume",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://volume1.host/v1/1234",
                        "internalURL": "https://volume1.host/v1/1234",
                        "region": "South",
                        "versionId": "1.0",
                        "versionInfo": "uri",
                        "versionList": "uri"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://volume1.host/v1/3456",
                        "internalURL": "https://volume1.host/v1/3456",
                        "region": "South",
                        "versionId": "1.1",
                        "versionInfo": "https://volume1.host/v1/",
                        "versionList": "https://volume1.host/"
                    },
                ],
                "endpoints_links": [
                    {
                        "rel": "next",
                        "href": "https://identity1.host/v2.0/endpoints"
                    },
                ],
            },
            {
                "name": "Cinder Volume Service V2",
                "type": "volumev2",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://volume1.host/v2/1234",
                        "internalURL": "https://volume1.host/v2/1234",
                        "region": "South",
                        "versionId": "2.0",
                        "versionInfo": "uri",
                        "versionList": "uri"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://volume1.host/v2/3456",
                        "internalURL": "https://volume1.host/v2/3456",
                        "region": "South",
                        "versionId": "1.1",
                        "versionInfo": "https://volume1.host/v2/",
                        "versionList": "https://volume1.host/"
                    },
                ],
                "endpoints_links": [
                    {
                        "rel": "next",
                        "href": "https://identity1.host/v2.0/endpoints"
                    },
                ],
            },
        ],
        "serviceCatalog_links": [
            {
                "rel": "next",
                "href": "https://identity.host/v2.0/endpoints?session=2hfh8Ar",
            },
        ],
    },
}

SERVICE_COMPATIBILITY_CATALOG = {
    "access": {
        "token": {
            "id": "ab48a9efdfedb23ty3494",
            "expires": "2010-11-01T03:32:15-05:00",
            "tenant": {
                "id": "345",
                "name": "My Project"
            }
        },
        "user": {
            "id": "123",
            "name": "jqsmith",
            "roles": [
                {
                    "id": "234",
                    "name": "compute:admin",
                },
                {
                    "id": "235",
                    "name": "object-store:admin",
                    "tenantId": "1",
                }
            ],
            "roles_links": [],
        },
        "serviceCatalog": [
            {
                "name": "Cloud Servers",
                "type": "compute",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://compute1.host/v1/1234",
                        "internalURL": "https://compute1.host/v1/1234",
                        "region": "North",
                        "versionId": "1.0",
                        "versionInfo": "https://compute1.host/v1/",
                        "versionList": "https://compute1.host/"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://compute1.host/v1/3456",
                        "internalURL": "https://compute1.host/v1/3456",
                        "region": "North",
                        "versionId": "1.1",
                        "versionInfo": "https://compute1.host/v1/",
                        "versionList": "https://compute1.host/"
                    },
                ],
                "endpoints_links": [],
            },
            {
                "name": "Cinder Volume Service V2",
                "type": "volume",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://volume1.host/v2/1234",
                        "internalURL": "https://volume1.host/v2/1234",
                        "region": "South",
                        "versionId": "2.0",
                        "versionInfo": "uri",
                        "versionList": "uri"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://volume1.host/v2/3456",
                        "internalURL": "https://volume1.host/v2/3456",
                        "region": "South",
                        "versionId": "1.1",
                        "versionInfo": "https://volume1.host/v2/",
                        "versionList": "https://volume1.host/"
                    },
                ],
                "endpoints_links": [
                    {
                        "rel": "next",
                        "href": "https://identity1.host/v2.0/endpoints"
                    },
                ],
            },
        ],
        "serviceCatalog_links": [
            {
                "rel": "next",
                "href": "https://identity.host/v2.0/endpoints?session=2hfh8Ar",
            },
        ],
    },
}


class ServiceCatalogTest(utils.TestCase):
    def test_building_a_service_catalog(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG)

        self.assertRaises(exceptions.AmbiguousEndpoints, sc.url_for,
                          service_type='compute')
        self.assertEqual("https://compute1.host/v1/1234",
                         sc.url_for('tenantId', '1', service_type='compute'))
        self.assertEqual("https://compute1.host/v1/3456",
                         sc.url_for('tenantId', '2', service_type='compute'))

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          "region", "South", service_type='compute')

    def test_alternate_service_type(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG)

        self.assertRaises(exceptions.AmbiguousEndpoints, sc.url_for,
                          service_type='volume')
        self.assertEqual("https://volume1.host/v1/1234",
                         sc.url_for('tenantId', '1', service_type='volume'))
        self.assertEqual("https://volume1.host/v1/3456",
                         sc.url_for('tenantId', '2', service_type='volume'))

        self.assertEqual("https://volume1.host/v2/3456",
                         sc.url_for('tenantId', '2', service_type='volumev2'))
        self.assertEqual("https://volume1.host/v2/3456",
                         sc.url_for('tenantId', '2', service_type='volumev2'))

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          "region", "North", service_type='volume')

    def test_compatibility_service_type(self):
        sc = service_catalog.ServiceCatalog(SERVICE_COMPATIBILITY_CATALOG)

        self.assertEqual("https://volume1.host/v2/1234",
                         sc.url_for('tenantId', '1', service_type='volume'))
        self.assertEqual("https://volume1.host/v2/3456",
                         sc.url_for('tenantId', '2', service_type='volume'))
