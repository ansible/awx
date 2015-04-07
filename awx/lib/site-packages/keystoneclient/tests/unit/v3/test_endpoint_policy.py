# Copyright 2014 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient.tests.unit.v3 import test_endpoint_filter
from keystoneclient.tests.unit.v3 import utils


class EndpointPolicyTests(utils.TestCase,
                          test_endpoint_filter.EndpointTestUtils):
    """Test policy-endpoint associations (a.k.a. EndpointPolicy Extension)."""

    def setUp(self):
        super(EndpointPolicyTests, self).setUp()
        self.manager = self.client.endpoint_policy

    def new_policy_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('blob', uuid.uuid4().hex)
        return kwargs

    def new_region_ref(self, **kwargs):
        kwargs = self.new_ref(**kwargs)
        return kwargs

    def new_service_ref(self, **kwargs):
        kwargs = self.new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        return kwargs

    def _crud_policy_association_for_endpoint_via_id(
            self, http_action, manager_action):
        policy_id = uuid.uuid4().hex
        endpoint_id = uuid.uuid4().hex

        self.stub_url(http_action,
                      ['policies', policy_id, self.manager.OS_EP_POLICY_EXT,
                       'endpoints', endpoint_id],
                      status_code=204)
        manager_action(policy=policy_id, endpoint=endpoint_id)

    def _crud_policy_association_for_endpoint_via_obj(
            self, http_action, manager_action):
        policy_ref = self.new_policy_ref()
        endpoint_ref = self.new_endpoint_ref()
        policy = self.client.policies.resource_class(
            self.client.policies, policy_ref, loaded=True)
        endpoint = self.client.endpoints.resource_class(
            self.client.endpoints, endpoint_ref, loaded=True)

        self.stub_url(http_action,
                      ['policies', policy_ref['id'],
                       self.manager.OS_EP_POLICY_EXT,
                       'endpoints', endpoint_ref['id']],
                      status_code=204)
        manager_action(policy=policy, endpoint=endpoint)

    def test_create_policy_association_for_endpoint_via_id(self):
        self._crud_policy_association_for_endpoint_via_id(
            'PUT', self.manager.create_policy_association_for_endpoint)

    def test_create_policy_association_for_endpoint_via_obj(self):
        self._crud_policy_association_for_endpoint_via_obj(
            'PUT', self.manager.create_policy_association_for_endpoint)

    def test_check_policy_association_for_endpoint_via_id(self):
        self._crud_policy_association_for_endpoint_via_id(
            'HEAD', self.manager.check_policy_association_for_endpoint)

    def test_check_policy_association_for_endpoint_via_obj(self):
        self._crud_policy_association_for_endpoint_via_obj(
            'HEAD', self.manager.check_policy_association_for_endpoint)

    def test_delete_policy_association_for_endpoint_via_id(self):
        self._crud_policy_association_for_endpoint_via_id(
            'DELETE', self.manager.delete_policy_association_for_endpoint)

    def test_delete_policy_association_for_endpoint_via_obj(self):
        self._crud_policy_association_for_endpoint_via_obj(
            'DELETE', self.manager.delete_policy_association_for_endpoint)

    def _crud_policy_association_for_service_via_id(
            self, http_action, manager_action):
        policy_id = uuid.uuid4().hex
        service_id = uuid.uuid4().hex

        self.stub_url(http_action,
                      ['policies', policy_id, self.manager.OS_EP_POLICY_EXT,
                       'services', service_id],
                      status_code=204)
        manager_action(policy=policy_id, service=service_id)

    def _crud_policy_association_for_service_via_obj(
            self, http_action, manager_action):
        policy_ref = self.new_policy_ref()
        service_ref = self.new_service_ref()
        policy = self.client.policies.resource_class(
            self.client.policies, policy_ref, loaded=True)
        service = self.client.services.resource_class(
            self.client.services, service_ref, loaded=True)

        self.stub_url(http_action,
                      ['policies', policy_ref['id'],
                       self.manager.OS_EP_POLICY_EXT,
                       'services', service_ref['id']],
                      status_code=204)
        manager_action(policy=policy, service=service)

    def test_create_policy_association_for_service_via_id(self):
        self._crud_policy_association_for_service_via_id(
            'PUT', self.manager.create_policy_association_for_service)

    def test_create_policy_association_for_service_via_obj(self):
        self._crud_policy_association_for_service_via_obj(
            'PUT', self.manager.create_policy_association_for_service)

    def test_check_policy_association_for_service_via_id(self):
        self._crud_policy_association_for_service_via_id(
            'HEAD', self.manager.check_policy_association_for_service)

    def test_check_policy_association_for_service_via_obj(self):
        self._crud_policy_association_for_service_via_obj(
            'HEAD', self.manager.check_policy_association_for_service)

    def test_delete_policy_association_for_service_via_id(self):
        self._crud_policy_association_for_service_via_id(
            'DELETE', self.manager.delete_policy_association_for_service)

    def test_delete_policy_association_for_service_via_obj(self):
        self._crud_policy_association_for_service_via_obj(
            'DELETE', self.manager.delete_policy_association_for_service)

    def _crud_policy_association_for_region_and_service_via_id(
            self, http_action, manager_action):
        policy_id = uuid.uuid4().hex
        region_id = uuid.uuid4().hex
        service_id = uuid.uuid4().hex

        self.stub_url(http_action,
                      ['policies', policy_id, self.manager.OS_EP_POLICY_EXT,
                       'services', service_id, 'regions', region_id],
                      status_code=204)
        manager_action(policy=policy_id, region=region_id, service=service_id)

    def _crud_policy_association_for_region_and_service_via_obj(
            self, http_action, manager_action):
        policy_ref = self.new_policy_ref()
        region_ref = self.new_region_ref()
        service_ref = self.new_service_ref()
        policy = self.client.policies.resource_class(
            self.client.policies, policy_ref, loaded=True)
        region = self.client.regions.resource_class(
            self.client.regions, region_ref, loaded=True)
        service = self.client.services.resource_class(
            self.client.services, service_ref, loaded=True)

        self.stub_url(http_action,
                      ['policies', policy_ref['id'],
                       self.manager.OS_EP_POLICY_EXT,
                       'services', service_ref['id'],
                       'regions', region_ref['id']],
                      status_code=204)
        manager_action(policy=policy, region=region, service=service)

    def test_create_policy_association_for_region_and_service_via_id(self):
        self._crud_policy_association_for_region_and_service_via_id(
            'PUT',
            self.manager.create_policy_association_for_region_and_service)

    def test_create_policy_association_for_region_and_service_via_obj(self):
        self._crud_policy_association_for_region_and_service_via_obj(
            'PUT',
            self.manager.create_policy_association_for_region_and_service)

    def test_check_policy_association_for_region_and_service_via_id(self):
        self._crud_policy_association_for_region_and_service_via_id(
            'HEAD',
            self.manager.check_policy_association_for_region_and_service)

    def test_check_policy_association_for_region_and_service_via_obj(self):
        self._crud_policy_association_for_region_and_service_via_obj(
            'HEAD',
            self.manager.check_policy_association_for_region_and_service)

    def test_delete_policy_association_for_region_and_service_via_id(self):
        self._crud_policy_association_for_region_and_service_via_id(
            'DELETE',
            self.manager.delete_policy_association_for_region_and_service)

    def test_delete_policy_association_for_region_and_service_via_obj(self):
        self._crud_policy_association_for_region_and_service_via_obj(
            'DELETE',
            self.manager.delete_policy_association_for_region_and_service)

    def test_get_policy_for_endpoint(self):
        endpoint_id = uuid.uuid4().hex
        expected_policy = self.new_policy_ref()

        self.stub_url('GET',
                      ['endpoints', endpoint_id, self.manager.OS_EP_POLICY_EXT,
                       'policy'],
                      json={'policy': expected_policy},
                      status_code=200)

        policy_resp = self.manager.get_policy_for_endpoint(
            endpoint=endpoint_id)

        self.assertEqual(expected_policy['id'], policy_resp.id)
        self.assertEqual(expected_policy['blob'], policy_resp.blob)
        self.assertEqual(expected_policy['type'], policy_resp.type)

    def test_list_endpoints_for_policy(self):
        policy_id = uuid.uuid4().hex
        endpoints = {'endpoints': [self.new_endpoint_ref(),
                                   self.new_endpoint_ref()]}
        self.stub_url('GET',
                      ['policies', policy_id, self.manager.OS_EP_POLICY_EXT,
                       'endpoints'],
                      json=endpoints,
                      status_code=200)

        endpoints_resp = self.manager.list_endpoints_for_policy(
            policy=policy_id)

        expected_endpoint_ids = [
            endpoint['id'] for endpoint in endpoints['endpoints']]
        actual_endpoint_ids = [endpoint.id for endpoint in endpoints_resp]
        self.assertEqual(expected_endpoint_ids, actual_endpoint_ids)
