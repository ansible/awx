# Copyright 2013 OpenStack Foundation
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

import warlock

from glanceclient.common import utils
from glanceclient.v2 import schemas


MEMBER_STATUS_VALUES = ('accepted', 'rejected', 'pending')


class Controller(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('member')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def list(self, image_id):
        url = '/v2/images/%s/members' % image_id
        resp, body = self.http_client.get(url)
        for member in body['members']:
            yield self.model(member)

    def delete(self, image_id, member_id):
        self.http_client.delete('/v2/images/%s/members/%s' %
                                (image_id, member_id))

    def update(self, image_id, member_id, member_status):
        url = '/v2/images/%s/members/%s' % (image_id, member_id)
        body = {'status': member_status}
        resp, updated_member = self.http_client.put(url, data=body)
        return self.model(updated_member)

    def create(self, image_id, member_id):
        url = '/v2/images/%s/members' % image_id
        body = {'member': member_id}
        resp, created_member = self.http_client.post(url, data=body)
        return self.model(created_member)
