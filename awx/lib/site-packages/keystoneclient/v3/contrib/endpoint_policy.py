# Copyright 2014 IBM Corp.
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

from keystoneclient import base
from keystoneclient.i18n import _
from keystoneclient.v3 import endpoints
from keystoneclient.v3 import policies


class EndpointPolicyManager(base.Manager):
    """Manager class for manipulating endpoint-policy associations."""

    OS_EP_POLICY_EXT = 'OS-ENDPOINT-POLICY'

    def _act_on_policy_association_for_endpoint(
            self, policy, endpoint, action):
        if not (policy and endpoint):
            raise ValueError(_('policy and endpoint are required'))

        policy_id = base.getid(policy)
        endpoint_id = base.getid(endpoint)
        url = ('/policies/%(policy_id)s/%(ext_name)s'
               '/endpoints/%(endpoint_id)s') % {
                   'policy_id': policy_id,
                   'ext_name': self.OS_EP_POLICY_EXT,
                   'endpoint_id': endpoint_id}
        return action(url=url)

    def create_policy_association_for_endpoint(self, policy, endpoint):
        """Create an association between a policy and an endpoint."""
        self._act_on_policy_association_for_endpoint(
            policy, endpoint, self._put)

    def check_policy_association_for_endpoint(self, policy, endpoint):
        """Check an association between a policy and an endpoint."""
        self._act_on_policy_association_for_endpoint(
            policy, endpoint, self._head)

    def delete_policy_association_for_endpoint(self, policy, endpoint):
        """Delete an association between a policy and an endpoint."""
        self._act_on_policy_association_for_endpoint(
            policy, endpoint, self._delete)

    def _act_on_policy_association_for_service(self, policy, service, action):
        if not (policy and service):
            raise ValueError(_('policy and service are required'))

        policy_id = base.getid(policy)
        service_id = base.getid(service)
        url = ('/policies/%(policy_id)s/%(ext_name)s'
               '/services/%(service_id)s') % {
                   'policy_id': policy_id,
                   'ext_name': self.OS_EP_POLICY_EXT,
                   'service_id': service_id}
        return action(url=url)

    def create_policy_association_for_service(self, policy, service):
        """Create an association between a policy and a service."""
        self._act_on_policy_association_for_service(
            policy, service, self._put)

    def check_policy_association_for_service(self, policy, service):
        """Check an association between a policy and a service."""
        self._act_on_policy_association_for_service(
            policy, service, self._head)

    def delete_policy_association_for_service(self, policy, service):
        """Delete an association between a policy and a service."""
        self._act_on_policy_association_for_service(
            policy, service, self._delete)

    def _act_on_policy_association_for_region_and_service(
            self, policy, region, service, action):
        if not (policy and region and service):
            raise ValueError(_('policy, region and service are required'))

        policy_id = base.getid(policy)
        region_id = base.getid(region)
        service_id = base.getid(service)
        url = ('/policies/%(policy_id)s/%(ext_name)s'
               '/services/%(service_id)s/regions/%(region_id)s') % {
                   'policy_id': policy_id,
                   'ext_name': self.OS_EP_POLICY_EXT,
                   'service_id': service_id,
                   'region_id': region_id}
        return action(url=url)

    def create_policy_association_for_region_and_service(
            self, policy, region, service):
        """Create an association between a policy and a service in a region."""
        self._act_on_policy_association_for_region_and_service(
            policy, region, service, self._put)

    def check_policy_association_for_region_and_service(
            self, policy, region, service):
        """Check an association between a policy and a service in a region."""
        self._act_on_policy_association_for_region_and_service(
            policy, region, service, self._head)

    def delete_policy_association_for_region_and_service(
            self, policy, region, service):
        """Delete an association between a policy and a service in a region."""
        self._act_on_policy_association_for_region_and_service(
            policy, region, service, self._delete)

    def get_policy_for_endpoint(self, endpoint):
        """Get the effective policy for an endpoint.

        :param endpoint: endpoint object or ID

        :returns: policies.Policy object

        """
        if not endpoint:
            raise ValueError(_('endpoint is required'))

        endpoint_id = base.getid(endpoint)
        url = ('/endpoints/%(endpoint_id)s/%(ext_name)s/policy') % {
            'endpoint_id': endpoint_id,
            'ext_name': self.OS_EP_POLICY_EXT}

        _resp, body = self.client.get(url)
        return policies.Policy(
            self, body[policies.PolicyManager.key], loaded=True)

    def list_endpoints_for_policy(self, policy):
        """List endpoints with the effective association to a policy.

        :param policy: policy object or ID

        :returns: list of endpoints that are associated with the policy

        """
        if not policy:
            raise ValueError(_('policy is required'))

        policy_id = base.getid(policy)
        url = ('/policies/%(policy_id)s/%(ext_name)s/endpoints') % {
            'policy_id': policy_id,
            'ext_name': self.OS_EP_POLICY_EXT}
        return self._list(
            url,
            endpoints.EndpointManager.collection_key,
            obj_class=endpoints.EndpointManager.resource_class)
