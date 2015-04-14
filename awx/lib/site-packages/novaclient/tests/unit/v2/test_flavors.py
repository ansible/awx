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

import mock

from novaclient import exceptions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import flavors


class FlavorsTest(utils.TestCase):
    def setUp(self):
        super(FlavorsTest, self).setUp()
        self.cs = self._get_fake_client()
        self.flavor_type = self._get_flavor_type()

    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_flavor_type(self):
        return flavors.Flavor

    def test_list_flavors(self):
        fl = self.cs.flavors.list()
        self.cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_undetailed(self):
        fl = self.cs.flavors.list(detailed=False)
        self.cs.assert_called('GET', '/flavors')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_is_public_none(self):
        fl = self.cs.flavors.list(is_public=None)
        self.cs.assert_called('GET', '/flavors/detail?is_public=None')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_is_public_false(self):
        fl = self.cs.flavors.list(is_public=False)
        self.cs.assert_called('GET', '/flavors/detail?is_public=False')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_list_flavors_is_public_true(self):
        fl = self.cs.flavors.list(is_public=True)
        self.cs.assert_called('GET', '/flavors/detail')
        for flavor in fl:
            self.assertIsInstance(flavor, self.flavor_type)

    def test_get_flavor_details(self):
        f = self.cs.flavors.get(1)
        self.cs.assert_called('GET', '/flavors/1')
        self.assertIsInstance(f, self.flavor_type)
        self.assertEqual(256, f.ram)
        self.assertEqual(10, f.disk)
        self.assertEqual(10, f.ephemeral)
        self.assertEqual(True, f.is_public)

    def test_get_flavor_details_alphanum_id(self):
        f = self.cs.flavors.get('aa1')
        self.cs.assert_called('GET', '/flavors/aa1')
        self.assertIsInstance(f, self.flavor_type)
        self.assertEqual(128, f.ram)
        self.assertEqual(0, f.disk)
        self.assertEqual(0, f.ephemeral)
        self.assertEqual(True, f.is_public)

    def test_get_flavor_details_diablo(self):
        f = self.cs.flavors.get(3)
        self.cs.assert_called('GET', '/flavors/3')
        self.assertIsInstance(f, self.flavor_type)
        self.assertEqual(256, f.ram)
        self.assertEqual(10, f.disk)
        self.assertEqual('N/A', f.ephemeral)
        self.assertEqual('N/A', f.is_public)

    def test_find(self):
        f = self.cs.flavors.find(ram=256)
        self.cs.assert_called('GET', '/flavors/detail')
        self.assertEqual('256 MB Server', f.name)

        f = self.cs.flavors.find(disk=0)
        self.assertEqual('128 MB Server', f.name)

        self.assertRaises(exceptions.NotFound, self.cs.flavors.find,
                          disk=12345)

    def _create_body(self, name, ram, vcpus, disk, ephemeral, id, swap,
                     rxtx_factor, is_public):
        return {
            "flavor": {
                "name": name,
                "ram": ram,
                "vcpus": vcpus,
                "disk": disk,
                "OS-FLV-EXT-DATA:ephemeral": ephemeral,
                "id": id,
                "swap": swap,
                "rxtx_factor": rxtx_factor,
                "os-flavor-access:is_public": is_public,
            }
        }

    def test_create(self):
        f = self.cs.flavors.create("flavorcreate", 512, 1, 10, 1234,
                                   ephemeral=10, is_public=False)

        body = self._create_body("flavorcreate", 512, 1, 10, 10, 1234, 0, 1.0,
                                 False)

        self.cs.assert_called('POST', '/flavors', body)
        self.assertIsInstance(f, self.flavor_type)

    def test_create_with_id_as_string(self):
        flavor_id = 'foobar'
        f = self.cs.flavors.create("flavorcreate", 512,
                                   1, 10, flavor_id, ephemeral=10,
                                   is_public=False)

        body = self._create_body("flavorcreate", 512, 1, 10, 10, flavor_id, 0,
                                 1.0, False)

        self.cs.assert_called('POST', '/flavors', body)
        self.assertIsInstance(f, self.flavor_type)

    def test_create_ephemeral_ispublic_defaults(self):
        f = self.cs.flavors.create("flavorcreate", 512, 1, 10, 1234)

        body = self._create_body("flavorcreate", 512, 1, 10, 0, 1234, 0,
                                 1.0, True)

        self.cs.assert_called('POST', '/flavors', body)
        self.assertIsInstance(f, self.flavor_type)

    def test_invalid_parameters_create(self):
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", "invalid", 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, "invalid", 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, "invalid", 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap="invalid",
                          ephemeral=0, rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral="invalid", rxtx_factor=1.0, is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor="invalid", is_public=True)
        self.assertRaises(exceptions.CommandError, self.cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1.0, is_public='invalid')

    def test_delete(self):
        self.cs.flavors.delete("flavordelete")
        self.cs.assert_called('DELETE', '/flavors/flavordelete')

    def test_delete_with_flavor_instance(self):
        f = self.cs.flavors.get(2)
        self.cs.flavors.delete(f)
        self.cs.assert_called('DELETE', '/flavors/2')

    def test_delete_with_flavor_instance_method(self):
        f = self.cs.flavors.get(2)
        f.delete()
        self.cs.assert_called('DELETE', '/flavors/2')

    def test_set_keys(self):
        f = self.cs.flavors.get(1)
        f.set_keys({'k1': 'v1'})
        self.cs.assert_called('POST', '/flavors/1/os-extra_specs',
                              {"extra_specs": {'k1': 'v1'}})

    def test_set_with_valid_keys(self):
        valid_keys = ['key4', 'month.price', 'I-Am:AK-ey.44-',
                      'key with spaces and _']

        f = self.cs.flavors.get(4)
        for key in valid_keys:
            f.set_keys({key: 'v4'})
            self.cs.assert_called('POST', '/flavors/4/os-extra_specs',
                                  {"extra_specs": {key: 'v4'}})

    def test_set_with_invalid_keys(self):
        invalid_keys = ['/1', '?1', '%1', '<', '>']

        f = self.cs.flavors.get(1)
        for key in invalid_keys:
            self.assertRaises(exceptions.CommandError, f.set_keys, {key: 'v1'})

    @mock.patch.object(flavors.FlavorManager, '_delete')
    def test_unset_keys(self, mock_delete):
        f = self.cs.flavors.get(1)
        keys = ['k1', 'k2']
        f.unset_keys(keys)
        mock_delete.assert_has_calls([
            mock.call("/flavors/1/os-extra_specs/k1"),
            mock.call("/flavors/1/os-extra_specs/k2")
        ])
