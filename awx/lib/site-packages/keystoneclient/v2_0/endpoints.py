# Copyright 2012 Canonical Ltd.
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

from keystoneclient import base


class Endpoint(base.Resource):
    """Represents a Keystone endpoint."""
    def __repr__(self):
        return "<Endpoint %s>" % self._info


class EndpointManager(base.ManagerWithFind):
    """Manager class for manipulating Keystone endpoints."""

    resource_class = Endpoint

    def list(self):
        """List all available endpoints."""
        return self._list('/endpoints', 'endpoints')

    def create(self, region, service_id, publicurl, adminurl=None,
               internalurl=None):
        """Create a new endpoint."""
        body = {'endpoint': {'region': region,
                             'service_id': service_id,
                             'publicurl': publicurl,
                             'adminurl': adminurl,
                             'internalurl': internalurl}}
        return self._create('/endpoints', body, 'endpoint')

    def delete(self, id):
        """Delete an endpoint."""
        return self._delete('/endpoints/%s' % id)
