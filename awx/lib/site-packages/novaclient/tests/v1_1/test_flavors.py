# Copyright (c) 2013, OpenStack
# All Rights Reserved.
#
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

from novaclient import exceptions
from novaclient.v1_1 import flavors
from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


cs = fakes.FakeClient()


class FlavorsTest(utils.TestCase):

    def test_list_flavors(self):
        fl = cs.flavors.list()
        cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertTrue(isinstance(flavor, flavors.Flavor))

    def test_list_flavors_undetailed(self):
        fl = cs.flavors.list(detailed=False)
        cs.assert_called('GET', '/flavors')
        for flavor in fl:
            self.assertTrue(isinstance(flavor, flavors.Flavor))

    def test_list_flavors_is_public_none(self):
        fl = cs.flavors.list(is_public=None)
        cs.assert_called('GET', '/flavors/detail?is_public=None')
        for flavor in fl:
            self.assertTrue(isinstance(flavor, flavors.Flavor))

    def test_list_flavors_is_public_false(self):
        fl = cs.flavors.list(is_public=False)
        cs.assert_called('GET', '/flavors/detail?is_public=False')
        for flavor in fl:
            self.assertTrue(isinstance(flavor, flavors.Flavor))

    def test_list_flavors_is_public_true(self):
        fl = cs.flavors.list(is_public=True)
        cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertTrue(isinstance(flavor, flavors.Flavor))

    def test_get_flavor_details(self):
        f = cs.flavors.get(1)
        cs.assert_called('GET', '/flavors/1')
        self.assertTrue(isinstance(f, flavors.Flavor))
        self.assertEqual(f.ram, 256)
        self.assertEqual(f.disk, 10)
        self.assertEqual(f.ephemeral, 10)
        self.assertEqual(f.is_public, True)

    def test_get_flavor_details_alphanum_id(self):
        f = cs.flavors.get('aa1')
        cs.assert_called('GET', '/flavors/aa1')
        self.assertTrue(isinstance(f, flavors.Flavor))
        self.assertEqual(f.ram, 128)
        self.assertEqual(f.disk, 0)
        self.assertEqual(f.ephemeral, 0)
        self.assertEqual(f.is_public, True)

    def test_get_flavor_details_diablo(self):
        f = cs.flavors.get(3)
        cs.assert_called('GET', '/flavors/3')
        self.assertTrue(isinstance(f, flavors.Flavor))
        self.assertEqual(f.ram, 256)
        self.assertEqual(f.disk, 10)
        self.assertEqual(f.ephemeral, 'N/A')
        self.assertEqual(f.is_public, 'N/A')

    def test_find(self):
        f = cs.flavors.find(ram=256)
        cs.assert_called('GET', '/flavors/detail')
        self.assertEqual(f.name, '256 MB Server')

        f = cs.flavors.find(disk=0)
        self.assertEqual(f.name, '128 MB Server')

        self.assertRaises(exceptions.NotFound, cs.flavors.find, disk=12345)

    def test_create(self):
        f = cs.flavors.create("flavorcreate", 512, 1, 10, 1234, ephemeral=10,
                              is_public=False)

        body = {
            "flavor": {
                "name": "flavorcreate",
                "ram": 512,
                "vcpus": 1,
                "disk": 10,
                "OS-FLV-EXT-DATA:ephemeral": 10,
                "id": 1234,
                "swap": 0,
                "rxtx_factor": 1.0,
                "os-flavor-access:is_public": False,
            }
        }

        cs.assert_called('POST', '/flavors', body)
        self.assertTrue(isinstance(f, flavors.Flavor))

    def test_create_with_id_as_string(self):
        flavor_id = 'foobar'
        f = cs.flavors.create("flavorcreate", 512,
                              1, 10, flavor_id, ephemeral=10,
                              is_public=False)

        body = {
            "flavor": {
                "name": "flavorcreate",
                "ram": 512,
                "vcpus": 1,
                "disk": 10,
                "OS-FLV-EXT-DATA:ephemeral": 10,
                "id": flavor_id,
                "swap": 0,
                "rxtx_factor": 1.0,
                "os-flavor-access:is_public": False,
            }
        }

        cs.assert_called('POST', '/flavors', body)
        self.assertTrue(isinstance(f, flavors.Flavor))

    def test_create_ephemeral_ispublic_defaults(self):
        f = cs.flavors.create("flavorcreate", 512, 1, 10, 1234)

        body = {
            "flavor": {
                "name": "flavorcreate",
                "ram": 512,
                "vcpus": 1,
                "disk": 10,
                "OS-FLV-EXT-DATA:ephemeral": 0,
                "id": 1234,
                "swap": 0,
                "rxtx_factor": 1.0,
                "os-flavor-access:is_public": True,
            }
        }

        cs.assert_called('POST', '/flavors', body)
        self.assertTrue(isinstance(f, flavors.Flavor))

    def test_invalid_parameters_create(self):
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", "invalid", 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, "invalid", 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, "invalid", 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap="invalid",
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral="invalid", rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor="invalid", is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public='invalid')

    def test_delete(self):
        cs.flavors.delete("flavordelete")
        cs.assert_called('DELETE', '/flavors/flavordelete')

    def test_delete_with_flavor_instance(self):
        f = cs.flavors.get(2)
        cs.flavors.delete(f)
        cs.assert_called('DELETE', '/flavors/2')

    def test_delete_with_flavor_instance_method(self):
        f = cs.flavors.get(2)
        f.delete()
        cs.assert_called('DELETE', '/flavors/2')

    def test_set_keys(self):
        f = cs.flavors.get(1)
        f.set_keys({'k1': 'v1'})
        cs.assert_called('POST', '/flavors/1/os-extra_specs',
                         {"extra_specs": {'k1': 'v1'}})

    def test_unset_keys(self):
        f = cs.flavors.get(1)
        f.unset_keys(['k1'])
        cs.assert_called('DELETE', '/flavors/1/os-extra_specs/k1')
