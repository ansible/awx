# Copyright 2012 OpenStack Foundation
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

from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import flavor_access


cs = fakes.FakeClient()


class FlavorAccessTest(utils.TestCase):

    def test_list_access_by_flavor_private(self):
        kwargs = {'flavor': cs.flavors.get(2)}
        r = cs.flavor_access.list(**kwargs)
        cs.assert_called('GET', '/flavors/2/os-flavor-access')
        [self.assertIsInstance(a, flavor_access.FlavorAccess) for a in r]

    def test_add_tenant_access(self):
        flavor = cs.flavors.get(2)
        tenant = 'proj2'
        r = cs.flavor_access.add_tenant_access(flavor, tenant)

        body = {
            "addTenantAccess": {
                "tenant": "proj2"
            }
        }

        cs.assert_called('POST', '/flavors/2/action', body)
        [self.assertIsInstance(a, flavor_access.FlavorAccess) for a in r]

    def test_remove_tenant_access(self):
        flavor = cs.flavors.get(2)
        tenant = 'proj2'
        r = cs.flavor_access.remove_tenant_access(flavor, tenant)

        body = {
            "removeTenantAccess": {
                "tenant": "proj2"
            }
        }

        cs.assert_called('POST', '/flavors/2/action', body)
        [self.assertIsInstance(a, flavor_access.FlavorAccess) for a in r]

    def test_repr_flavor_access(self):
        flavor = cs.flavors.get(2)
        tenant = 'proj3'
        r = cs.flavor_access.add_tenant_access(flavor, tenant)

        def get_expected(flavor_access):
            return ("<FlavorAccess flavor id: %s, tenant id: %s>" %
                    (flavor_access.flavor_id, flavor_access.tenant_id))

        for a in r:
            self.assertEqual(get_expected(a), repr(a))
