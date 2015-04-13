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

from novaclient import base
from novaclient import exceptions
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2 import flavors


cs = fakes.FakeClient()


class BaseTest(utils.TestCase):

    def test_resource_repr(self):
        r = base.Resource(None, dict(foo="bar", baz="spam"))
        self.assertEqual("<Resource baz=spam, foo=bar>", repr(r))

    def test_getid(self):
        self.assertEqual(4, base.getid(4))

        class TmpObject(object):
            id = 4
        self.assertEqual(4, base.getid(TmpObject))

    def test_resource_lazy_getattr(self):
        f = flavors.Flavor(cs.flavors, {'id': 1})
        self.assertEqual('256 mb server', f.name)
        cs.assert_called('GET', '/flavors/1')

        # Missing stuff still fails after a second get
        self.assertRaises(AttributeError, getattr, f, 'blahblah')

    def test_eq(self):
        # Two resources of the same type with the same id: equal
        r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertEqual(r1, r2)

        # Two resoruces of different types: never equal
        r1 = base.Resource(None, {'id': 1})
        r2 = flavors.Flavor(None, {'id': 1})
        self.assertNotEqual(r1, r2)

        # Two resources with no ID: equal if their info is equal
        r1 = base.Resource(None, {'name': 'joe', 'age': 12})
        r2 = base.Resource(None, {'name': 'joe', 'age': 12})
        self.assertEqual(r1, r2)

    def test_findall_invalid_attribute(self):
        # Make sure findall with an invalid attribute doesn't cause errors.
        # The following should not raise an exception.
        cs.flavors.findall(vegetable='carrot')

        # However, find() should raise an error
        self.assertRaises(exceptions.NotFound,
                          cs.flavors.find,
                          vegetable='carrot')
