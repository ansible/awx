# Copyright (c) 2013, OpenStack
# Copyright 2013 IBM Corp.
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

from novaclient.tests.v1_1 import test_flavors
from novaclient.tests.v3 import fakes
from novaclient.v3 import flavors


class FlavorsTest(test_flavors.FlavorsTest):
    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_flavor_type(self):
        return flavors.Flavor

    def _create_body(self, name, ram, vcpus, disk, ephemeral, id, swap,
                     rxtx_factor, is_public):
        return {
            "flavor": {
                "name": name,
                "ram": ram,
                "vcpus": vcpus,
                "disk": disk,
                "ephemeral": ephemeral,
                "id": id,
                "swap": swap,
                "os-flavor-rxtx:rxtx_factor": rxtx_factor,
                "flavor-access:is_public": is_public,
            }
        }

    def test_set_keys(self):
        f = self.cs.flavors.get(1)
        f.set_keys({'k1': 'v1'})
        self.cs.assert_called('POST', '/flavors/1/flavor-extra-specs',
                         {"extra_specs": {'k1': 'v1'}})

    def test_set_with_valid_keys(self):
        valid_keys = ['key4', 'month.price', 'I-Am:AK-ey.44-',
                      'key with spaces and _']

        f = self.cs.flavors.get(4)
        for key in valid_keys:
            f.set_keys({key: 'v4'})
            self.cs.assert_called('POST', '/flavors/4/flavor-extra-specs',
                                  {"extra_specs": {key: 'v4'}})

    @mock.patch.object(flavors.FlavorManager, '_delete')
    def test_unset_keys(self, mock_delete):
        f = self.cs.flavors.get(1)
        keys = ['k1', 'k2']
        f.unset_keys(keys)
        mock_delete.assert_has_calls([
            mock.call("/flavors/1/flavor-extra-specs/k1"),
            mock.call("/flavors/1/flavor-extra-specs/k2")
        ])

    def test_get_flavor_details_diablo(self):
        # Don't need for V3 API to work against diablo
        pass
