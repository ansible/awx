# Copyright (c) 2013 OpenStack Foundation
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

from cinderclient import base


class QuotaSet(base.Resource):

    @property
    def id(self):
        """Needed by base.Resource to self-refresh and be indexed."""
        return self.tenant_id

    def update(self, *args, **kwargs):
        return self.manager.update(self.tenant_id, *args, **kwargs)


class QuotaSetManager(base.Manager):
    resource_class = QuotaSet

    def get(self, tenant_id, usage=False):
        if hasattr(tenant_id, 'tenant_id'):
            tenant_id = tenant_id.tenant_id
        return self._get("/os-quota-sets/%s?usage=%s" % (tenant_id, usage),
                         "quota_set")

    def update(self, tenant_id, **updates):
        body = {'quota_set': {'tenant_id': tenant_id}}

        for update in updates:
            body['quota_set'][update] = updates[update]

        result = self._update('/os-quota-sets/%s' % (tenant_id), body)
        return self.resource_class(self, result['quota_set'], loaded=True)

    def defaults(self, tenant_id):
        return self._get('/os-quota-sets/%s/defaults' % tenant_id,
                         'quota_set')

    def delete(self, tenant_id):
        if hasattr(tenant_id, 'tenant_id'):
            tenant_id = tenant_id.tenant_id
        return self._delete("/os-quota-sets/%s" % tenant_id)
