from novaclient import exceptions
from novaclient import service_catalog
from novaclient.tests import utils


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
                        # Tenant 1, no region, v1.0
                        "tenantId": "1",
                        "publicURL": "https://compute1.host/v1/1",
                        "internalURL": "https://compute1.host/v1/1",
                        "versionId": "1.0",
                        "versionInfo": "https://compute1.host/v1.0/",
                        "versionList": "https://compute1.host/"
                    },
                    {
                        # Tenant 2, with region, v1.1
                        "tenantId": "2",
                        "publicURL": "https://compute1.host/v1.1/2",
                        "internalURL": "https://compute1.host/v1.1/2",
                        "region": "North",
                        "versionId": "1.1",
                        "versionInfo": "https://compute1.host/v1.1/",
                        "versionList": "https://compute1.host/"
                    },
                    {
                        # Tenant 1, with region, v2.0
                        "tenantId": "1",
                        "publicURL": "https://compute1.host/v2/1",
                        "internalURL": "https://compute1.host/v2/1",
                        "region": "North",
                        "versionId": "2",
                        "versionInfo": "https://compute1.host/v2/",
                        "versionList": "https://compute1.host/"
                    },
                ],
                "endpoints_links": [],
            },
            {
                "name": "Nova Volumes",
                "type": "volume",
                "endpoints": [
                    {
                        "tenantId": "1",
                        "publicURL": "https://volume1.host/v1/1",
                        "internalURL": "https://volume1.host/v1/1",
                        "region": "South",
                        "versionId": "1.0",
                        "versionInfo": "uri",
                        "versionList": "uri"
                    },
                    {
                        "tenantId": "2",
                        "publicURL": "https://volume1.host/v1.1/2",
                        "internalURL": "https://volume1.host/v1.1/2",
                        "region": "South",
                        "versionId": "1.1",
                        "versionInfo": "https://volume1.host/v1.1/",
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
        self.assertEqual(sc.url_for('tenantId', '1', service_type='compute'),
                            "https://compute1.host/v2/1")
        self.assertEqual(sc.url_for('tenantId', '2', service_type='compute'),
                            "https://compute1.host/v1.1/2")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          "region", "South", service_type='compute')

    def test_building_a_service_catalog_insensitive_case(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG)
        # Matching south (and catalog has South).
        self.assertRaises(exceptions.AmbiguousEndpoints, sc.url_for,
                          'region', 'south', service_type='volume')

    def test_alternate_service_type(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG)

        self.assertRaises(exceptions.AmbiguousEndpoints, sc.url_for,
                          service_type='volume')
        self.assertEqual(sc.url_for('tenantId', '1', service_type='volume'),
                            "https://volume1.host/v1/1")
        self.assertEqual(sc.url_for('tenantId', '2', service_type='volume'),
                            "https://volume1.host/v1.1/2")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          "region", "North", service_type='volume')
