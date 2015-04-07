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

from keystoneclient import base
from keystoneclient.tests.unit import utils
from keystoneclient.v2_0 import client
from keystoneclient.v2_0 import roles


class HumanReadable(base.Resource):
    HUMAN_ID = True


class BaseTest(utils.TestCase):

    def test_resource_repr(self):
        r = base.Resource(None, dict(foo="bar", baz="spam"))
        self.assertEqual(repr(r), "<Resource baz=spam, foo=bar>")

    def test_getid(self):
        self.assertEqual(base.getid(4), 4)

        class TmpObject(object):
            id = 4
        self.assertEqual(base.getid(TmpObject), 4)

    def test_resource_lazy_getattr(self):
        self.client = client.Client(username=self.TEST_USER,
                                    token=self.TEST_TOKEN,
                                    tenant_name=self.TEST_TENANT_NAME,
                                    auth_url='http://127.0.0.1:5000',
                                    endpoint='http://127.0.0.1:5000')

        self.client._adapter.get = self.mox.CreateMockAnything()
        self.client._adapter.get('/OS-KSADM/roles/1').AndRaise(AttributeError)
        self.mox.ReplayAll()

        f = roles.Role(self.client.roles, {'id': 1, 'name': 'Member'})
        self.assertEqual(f.name, 'Member')

        # Missing stuff still fails after a second get
        self.assertRaises(AttributeError, getattr, f, 'blahblah')

    def test_eq(self):
        # Two resources of the same type with the same id: equal
        r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertEqual(r1, r2)

        # Two resoruces of different types: never equal
        r1 = base.Resource(None, {'id': 1})
        r2 = roles.Role(None, {'id': 1})
        self.assertNotEqual(r1, r2)

        # Two resources with no ID: equal if their info is equal
        r1 = base.Resource(None, {'name': 'joe', 'age': 12})
        r2 = base.Resource(None, {'name': 'joe', 'age': 12})
        self.assertEqual(r1, r2)

        r1 = base.Resource(None, {'id': 1})
        self.assertNotEqual(r1, object())
        self.assertNotEqual(r1, {'id': 1})

    def test_human_id(self):
        r = base.Resource(None, {"name": "1 of !"})
        self.assertIsNone(r.human_id)
        r = HumanReadable(None, {"name": "1 of !"})
        self.assertEqual(r.human_id, "1-of")


class ManagerTest(utils.TestCase):
    body = {"hello": {"hi": 1}}
    url = "/test-url"

    def setUp(self):
        super(ManagerTest, self).setUp()
        self.client = client.Client(username=self.TEST_USER,
                                    token=self.TEST_TOKEN,
                                    tenant_name=self.TEST_TENANT_NAME,
                                    auth_url='http://127.0.0.1:5000',
                                    endpoint='http://127.0.0.1:5000')
        self.mgr = base.Manager(self.client)
        self.mgr.resource_class = base.Resource

    def test_api(self):
        self.assertEqual(self.mgr.api, self.client)

    def test_get(self):
        self.client.get = self.mox.CreateMockAnything()
        self.client.get(self.url).AndReturn((None, self.body))
        self.mox.ReplayAll()

        rsrc = self.mgr._get(self.url, "hello")
        self.assertEqual(rsrc.hi, 1)

    def test_post(self):
        self.client.post = self.mox.CreateMockAnything()
        self.client.post(self.url, body=self.body).AndReturn((None, self.body))
        self.client.post(self.url, body=self.body).AndReturn((None, self.body))
        self.mox.ReplayAll()

        rsrc = self.mgr._post(self.url, self.body, "hello")
        self.assertEqual(rsrc.hi, 1)

        rsrc = self.mgr._post(self.url, self.body, "hello", return_raw=True)
        self.assertEqual(rsrc["hi"], 1)

    def test_put(self):
        self.client.put = self.mox.CreateMockAnything()
        self.client.put(self.url, body=self.body).AndReturn((None, self.body))
        self.client.put(self.url, body=self.body).AndReturn((None, self.body))
        self.mox.ReplayAll()

        rsrc = self.mgr._put(self.url, self.body, "hello")
        self.assertEqual(rsrc.hi, 1)

        rsrc = self.mgr._put(self.url, self.body)
        self.assertEqual(rsrc.hello["hi"], 1)

    def test_patch(self):
        self.client.patch = self.mox.CreateMockAnything()
        self.client.patch(self.url, body=self.body).AndReturn(
            (None, self.body))
        self.client.patch(self.url, body=self.body).AndReturn(
            (None, self.body))
        self.mox.ReplayAll()

        rsrc = self.mgr._patch(self.url, self.body, "hello")
        self.assertEqual(rsrc.hi, 1)

        rsrc = self.mgr._patch(self.url, self.body)
        self.assertEqual(rsrc.hello["hi"], 1)

    def test_update(self):
        self.client.patch = self.mox.CreateMockAnything()
        self.client.put = self.mox.CreateMockAnything()
        self.client.patch(
            self.url, body=self.body, management=False).AndReturn((None,
                                                                   self.body))
        self.client.put(self.url, body=None, management=True).AndReturn(
            (None, self.body))
        self.mox.ReplayAll()

        rsrc = self.mgr._update(
            self.url, body=self.body, response_key="hello", method="PATCH",
            management=False)
        self.assertEqual(rsrc.hi, 1)

        rsrc = self.mgr._update(
            self.url, body=None, response_key="hello", method="PUT",
            management=True)
        self.assertEqual(rsrc.hi, 1)
