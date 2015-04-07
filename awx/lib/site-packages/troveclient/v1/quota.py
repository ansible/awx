# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from troveclient import base
from troveclient import common


class Quotas(base.ManagerWithFind):
    """Manage :class:`Quota` information."""

    resource_class = base.Resource

    def show(self, tenant_id):
        """Get a list of all quotas for a tenant id."""

        url = "/mgmt/quotas/%s" % tenant_id
        resp, body = self.api.client.get(url)
        common.check_for_exceptions(resp, body, url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        if 'quotas' not in body:
            raise Exception("Missing key value 'quotas' in response body.")
        return body['quotas']

    def update(self, id, quotas):
        """Set limits for quotas."""
        url = "/mgmt/quotas/%s" % id
        body = {"quotas": quotas}
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        if 'quotas' not in body:
            raise Exception("Missing key value 'quotas' in response body.")
        return body['quotas']

    # Appease the abc gods
    def list(self):
        pass
