# Copyright 2012 OpenStack Foundation.
# All Rights Reserved
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
#

import uuid

from mox3 import mox
import testtools

from neutronclient.common import exceptions
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.tests.unit import test_cli20
from neutronclient.v2_0 import client


class CLITestNameorID(testtools.TestCase):

    def setUp(self):
        """Prepare the test environment."""
        super(CLITestNameorID, self).setUp()
        self.mox = mox.Mox()
        self.endurl = test_cli20.ENDURL
        self.client = client.Client(token=test_cli20.TOKEN,
                                    endpoint_url=self.endurl)
        self.addCleanup(self.mox.VerifyAll)
        self.addCleanup(self.mox.UnsetStubs)

    def test_get_id_from_id(self):
        _id = str(uuid.uuid4())
        reses = {'networks': [{'id': _id, }, ], }
        resstr = self.client.serialize(reses)
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "networks_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&id=" + _id),
                self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()
        returned_id = neutronV20.find_resourceid_by_name_or_id(
            self.client, 'network', _id)
        self.assertEqual(_id, returned_id)

    def test_get_id_from_id_then_name_empty(self):
        _id = str(uuid.uuid4())
        reses = {'networks': [{'id': _id, }, ], }
        resstr = self.client.serialize(reses)
        resstr1 = self.client.serialize({'networks': []})
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "networks_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&id=" + _id),
                self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr1))
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&name=" + _id),
                self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()
        returned_id = neutronV20.find_resourceid_by_name_or_id(
            self.client, 'network', _id)
        self.assertEqual(_id, returned_id)

    def test_get_id_from_name(self):
        name = 'myname'
        _id = str(uuid.uuid4())
        reses = {'networks': [{'id': _id, }, ], }
        resstr = self.client.serialize(reses)
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "networks_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&name=" + name),
                self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()
        returned_id = neutronV20.find_resourceid_by_name_or_id(
            self.client, 'network', name)
        self.assertEqual(_id, returned_id)

    def test_get_id_from_name_multiple(self):
        name = 'myname'
        reses = {'networks': [{'id': str(uuid.uuid4())},
                              {'id': str(uuid.uuid4())}]}
        resstr = self.client.serialize(reses)
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "networks_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&name=" + name),
                self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()
        try:
            neutronV20.find_resourceid_by_name_or_id(
                self.client, 'network', name)
        except exceptions.NeutronClientNoUniqueMatch as ex:
            self.assertIn('Multiple', ex.message)

    def test_get_id_from_name_notfound(self):
        name = 'myname'
        reses = {'networks': []}
        resstr = self.client.serialize(reses)
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "networks_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&name=" + name),
                self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()
        try:
            neutronV20.find_resourceid_by_name_or_id(
                self.client, 'network', name)
        except exceptions.NeutronClientException as ex:
            self.assertIn('Unable to find', ex.message)
            self.assertEqual(404, ex.status_code)

    def test_get_id_from_name_multiple_with_project(self):
        name = 'web_server'
        project = str(uuid.uuid4())
        expect_id = str(uuid.uuid4())
        reses = {'security_groups':
                 [{'id': expect_id, 'tenant_id': project}]}
        resstr = self.client.serialize(reses)
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "security_groups_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&name=%s&tenant_id=%s" %
                                         (name, project)), self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()

        observed_id = neutronV20.find_resourceid_by_name_or_id(
            self.client, 'security_group', name, project)

        self.assertEqual(expect_id, observed_id)

    def test_get_id_from_name_multiple_with_project_not_found(self):
        name = 'web_server'
        project = str(uuid.uuid4())
        reses = {'security_groups':
                 [{'id': str(uuid.uuid4()), 'tenant_id': str(uuid.uuid4())}]}
        resstr = self.client.serialize(reses)
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        path = getattr(self.client, "security_groups_path")
        self.client.httpclient.request(
            test_cli20.MyUrlComparator(
                test_cli20.end_url(path, "fields=id&name=%s&tenant_id=%s" %
                                         (name, project)), self.client),
            'GET',
            body=None,
            headers=mox.ContainsKeyValue('X-Auth-Token', test_cli20.TOKEN)
        ).AndReturn((test_cli20.MyResp(200), resstr))
        self.mox.ReplayAll()

        try:
            neutronV20.find_resourceid_by_name_or_id(
                self.client, 'security_group', name, project)
        except exceptions.NeutronClientException as ex:
            self.assertIn('Unable to find', ex.message)
            self.assertEqual(404, ex.status_code)
