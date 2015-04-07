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

import uuid

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import endpoints


class EndpointTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(EndpointTests, self).setUp()
        self.key = 'endpoint'
        self.collection_key = 'endpoints'
        self.model = endpoints.Endpoint
        self.manager = self.client.endpoints

    def new_ref(self, **kwargs):
        kwargs = super(EndpointTests, self).new_ref(**kwargs)
        kwargs.setdefault('interface', 'public')
        kwargs.setdefault('region', uuid.uuid4().hex)
        kwargs.setdefault('service_id', uuid.uuid4().hex)
        kwargs.setdefault('url', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        return kwargs

    def test_create_public_interface(self):
        ref = self.new_ref(interface='public')
        self.test_create(ref)

    def test_create_admin_interface(self):
        ref = self.new_ref(interface='admin')
        self.test_create(ref)

    def test_create_internal_interface(self):
        ref = self.new_ref(interface='internal')
        self.test_create(ref)

    def test_create_invalid_interface(self):
        ref = self.new_ref(interface=uuid.uuid4().hex)
        self.assertRaises(exceptions.ValidationError, self.manager.create,
                          **utils.parameterize(ref))

    def test_update_public_interface(self):
        ref = self.new_ref(interface='public')
        self.test_update(ref)

    def test_update_admin_interface(self):
        ref = self.new_ref(interface='admin')
        self.test_update(ref)

    def test_update_internal_interface(self):
        ref = self.new_ref(interface='internal')
        self.test_update(ref)

    def test_update_invalid_interface(self):
        ref = self.new_ref(interface=uuid.uuid4().hex)
        ref['endpoint'] = "fake_endpoint"
        self.assertRaises(exceptions.ValidationError, self.manager.update,
                          **utils.parameterize(ref))

    def test_list_public_interface(self):
        interface = 'public'
        expected_path = 'v3/%s?interface=%s' % (self.collection_key, interface)
        self.test_list(expected_path=expected_path, interface=interface)

    def test_list_admin_interface(self):
        interface = 'admin'
        expected_path = 'v3/%s?interface=%s' % (self.collection_key, interface)
        self.test_list(expected_path=expected_path, interface=interface)

    def test_list_internal_interface(self):
        interface = 'admin'
        expected_path = 'v3/%s?interface=%s' % (self.collection_key, interface)
        self.test_list(expected_path=expected_path, interface=interface)

    def test_list_invalid_interface(self):
        interface = uuid.uuid4().hex
        expected_path = 'v3/%s?interface=%s' % (self.collection_key, interface)
        self.assertRaises(exceptions.ValidationError, self.manager.list,
                          expected_path=expected_path, interface=interface)
