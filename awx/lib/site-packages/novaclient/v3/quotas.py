# Copyright 2011 OpenStack Foundation
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

from novaclient.v1_1 import quotas


class QuotaSet(quotas.QuotaSet):
    pass


class QuotaSetManager(quotas.QuotaSetManager):
    resource_class = QuotaSet

    def get(self, tenant_id, user_id=None, detail=False):
        if detail:
            detail_string = '/detail'
        else:
            detail_string = ''

        if hasattr(tenant_id, 'tenant_id'):
            tenant_id = tenant_id.tenant_id
        if user_id:
            url = '/os-quota-sets/%s%s?user_id=%s' % (tenant_id, detail_string,
                                                      user_id)
        else:
            url = '/os-quota-sets/%s%s' % (tenant_id, detail_string)
        return self._get(url, "quota_set")

    def _update_body(self, tenant_id, **kwargs):
        return {'quota_set': kwargs}
