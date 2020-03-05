from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import munch

from mock import patch

from ansible_collections.openstack.cloud.plugins.modules import os_routers_info
from ansible_collections.openstack.cloud.tests.unit.modules.utils import set_module_args, ModuleTestCase, AnsibleExitJson


def openstack_cloud_from_module(module, **kwargs):
    return FakeSDK(), FakeCloud()


class FakeSDK(object):
    class exceptions:
        class OpenStackCloudException(Exception):
            pass


class FakeCloud(object):

    def search_routers(self, name_or_id=None, filters=None):
        test_routers = [
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2019-12-19T20:16:18Z",
                "description": "",
                "distributed": False,
                "external_gateway_info": None,
                "flavor_id": None,
                "ha": False,
                "id": "d3f70ce4-7ab1-46a7-9bec-498c9d8a2483",
                "name": "router1",
                "project_id": "f48189aaee42429e8ed396e8b3f6a018",
                "revision_number": 14,
                "routes": [],
                "status": "ACTIVE",
                "tags": [],
                "tenant_id": "f48189aaee42429e8ed396e8b3f6a018",
                "updated_at": "2020-01-27T21:20:09Z"
            },
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2019-12-19T20:16:18Z",
                "description": "",
                "distributed": False,
                "external_gateway_info": {
                    "enable_snat": True,
                    "external_fixed_ips": [
                        {
                            "ip_address": "172.24.4.163",
                            "subnet_id": "b42b8057-5b3b-4aa3-949a-eaaee2032462"
                        },
                    ],
                    "network_id": "fd6cc0f1-ed6f-426e-bb7b-a942b12633ad"
                },
                "flavor_id": None,
                "ha": False,
                "id": "b869307c-a1f9-4956-a993-8a90fc7cc01d",
                "name": "router2",
                "project_id": "f48189aaee42429e8ed396e8b3f6a018",
                "revision_number": 6,
                "routes": [],
                "status": "ACTIVE",
                "tags": [],
                "tenant_id": "f48189aaee42429e8ed396e8b3f6a018",
                "updated_at": "2019-12-19T20:18:46Z"
            },
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2020-01-24T20:19:35Z",
                "description": "",
                "distributed": False,
                "external_gateway_info": {
                    "enable_snat": True,
                    "external_fixed_ips": [
                        {
                            "ip_address": "172.24.4.234",
                            "subnet_id": "b42b8057-5b3b-4aa3-949a-eaaee2032462"
                        },
                    ],
                    "network_id": "fd6cc0f1-ed6f-426e-bb7b-a942b12633ad"
                },
                "flavor_id": None,
                "ha": False,
                "id": "98bce30e-c912-4490-85eb-b22d650721e6",
                "name": "router3",
                "project_id": "f48189aaee42429e8ed396e8b3f6a018",
                "revision_number": 4,
                "routes": [],
                "status": "ACTIVE",
                "tags": [],
                "tenant_id": "f48189aaee42429e8ed396e8b3f6a018",
                "updated_at": "2020-01-26T10:21:31Z"
            },
        ]

        if name_or_id is not None:
            return [munch.Munch(router) for router in test_routers if router["name"] == name_or_id]
        else:
            return [munch.Munch(router) for router in test_routers]

    def list_router_interfaces(self, router):
        test_ports = [
            {
                "device_id": "d3f70ce4-7ab1-46a7-9bec-498c9d8a2483",
                "device_owner": "network:router_interface",
                "fixed_ips": [
                    {
                        "ip_address": "192.168.1.254",
                        "subnet_id": "0624c75f-0574-41b5-a8d1-92e6e3a9e51d"
                    }
                ],
                "id": "92eeeca3-225d-46b8-a857-ede6c4f05484",
            },
            {
                "device_id": "b869307c-a1f9-4956-a993-8a90fc7cc01d",
                "device_owner": "network:router_gateway",
                "fixed_ips": [
                    {
                        "ip_address": "172.24.4.10",
                        "subnet_id": "b42b8057-5b3b-4aa3-949a-eaaee2032462"
                    },
                ],
                "id": "ab45060c-98fd-42a3-a1aa-8d5a03554bef",
            },
            {
                "device_id": "98bce30e-c912-4490-85eb-b22d650721e6",
                "device_owner": "network:router_interface",
                "fixed_ips": [
                    {
                        "ip_address": "192.168.1.1",
                        "subnet_id": "0624c75f-0574-41b5-a8d1-92e6e3a9e51d"
                    }
                ],
                "id": "c9fb53f1-d43e-4588-a223-0e8bf8a79715",
            },
            {
                "device_id": "98bce30e-c912-4490-85eb-b22d650721e6",
                "device_owner": "network:router_gateway",
                "fixed_ips": [
                    {
                        "ip_address": "172.24.4.234",
                        "subnet_id": "b42b8057-5b3b-4aa3-949a-eaaee2032462"
                    },
                ],
                "id": "0271878e-4be8-433c-acdc-52823b41bcbf",
            },
        ]
        return [munch.Munch(port) for port in test_ports if port["device_id"] == router.id]


class TestRoutersInfo(ModuleTestCase):
    '''This class calls the main function of the
    os_routers_info module.
    '''
    def setUp(self):
        super(TestRoutersInfo, self).setUp()
        self.module = os_routers_info

    def module_main(self, exit_exc):
        with self.assertRaises(exit_exc) as exc:
            self.module.main()
        return exc.exception.args[0]

    @patch('ansible_collections.openstack.cloud.plugins.modules.os_routers_info.openstack_cloud_from_module', side_effect=openstack_cloud_from_module)
    def test_main_with_router_interface(self, *args):

        set_module_args({'name': 'router1'})
        result = self.module_main(AnsibleExitJson)
        self.assertIs(type(result.get('openstack_routers')[0].get('interfaces_info')), list)
        self.assertEqual(len(result.get('openstack_routers')[0].get('interfaces_info')), 1)
        self.assertEqual(result.get('openstack_routers')[0].get('interfaces_info')[0].get('port_id'), '92eeeca3-225d-46b8-a857-ede6c4f05484')
        self.assertEqual(result.get('openstack_routers')[0].get('interfaces_info')[0].get('ip_address'), '192.168.1.254')
        self.assertEqual(result.get('openstack_routers')[0].get('interfaces_info')[0].get('subnet_id'), '0624c75f-0574-41b5-a8d1-92e6e3a9e51d')

    @patch('ansible_collections.openstack.cloud.plugins.modules.os_routers_info.openstack_cloud_from_module', side_effect=openstack_cloud_from_module)
    def test_main_with_router_gateway(self, *args):

        set_module_args({'name': 'router2'})
        result = self.module_main(AnsibleExitJson)
        self.assertIs(type(result.get('openstack_routers')[0].get('interfaces_info')), list)
        self.assertEqual(len(result.get('openstack_routers')[0].get('interfaces_info')), 0)

    @patch('ansible_collections.openstack.cloud.plugins.modules.os_routers_info.openstack_cloud_from_module', side_effect=openstack_cloud_from_module)
    def test_main_with_router_interface_and_router_gateway(self, *args):

        set_module_args({'name': 'router3'})
        result = self.module_main(AnsibleExitJson)
        self.assertIs(type(result.get('openstack_routers')[0].get('interfaces_info')), list)
        self.assertEqual(len(result.get('openstack_routers')[0].get('interfaces_info')), 1)
        self.assertEqual(result.get('openstack_routers')[0].get('interfaces_info')[0].get('port_id'), 'c9fb53f1-d43e-4588-a223-0e8bf8a79715')
        self.assertEqual(result.get('openstack_routers')[0].get('interfaces_info')[0].get('ip_address'), '192.168.1.1')
        self.assertEqual(result.get('openstack_routers')[0].get('interfaces_info')[0].get('subnet_id'), '0624c75f-0574-41b5-a8d1-92e6e3a9e51d')
