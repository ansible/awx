# Copyright 2012 OpenStack Foundation
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

from novaclient import base


class QuotaClassSet(base.Resource):

    def update(self, *args, **kwargs):
        return self.manager.update(self.id, *args, **kwargs)


class QuotaClassSetManager(base.Manager):
    resource_class = QuotaClassSet

    def get(self, class_name):
        return self._get("/os-quota-class-sets/%s" % (class_name),
                         "quota_class_set")

    def _update_body(self, **kwargs):
        return {'quota_class_set': kwargs}

    def update(self, class_name, **kwargs):
        body = self._update_body(**kwargs)

        for key in list(body['quota_class_set']):
            if body['quota_class_set'][key] is None:
                body['quota_class_set'].pop(key)

        return self._update('/os-quota-class-sets/%s' % (class_name),
                            body,
                            'quota_class_set')
