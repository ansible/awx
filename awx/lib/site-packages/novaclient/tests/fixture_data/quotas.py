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

import httpretty

from novaclient.openstack.common import jsonutils
from novaclient.tests.fixture_data import base


class V1(base.Fixture):

    base_url = 'os-quota-sets'

    def setUp(self):
        super(V1, self).setUp()

        uuid = '97f4c221-bff4-4578-b030-0df4ef119353'
        uuid2 = '97f4c221bff44578b0300df4ef119353'
        test_json = jsonutils.dumps({'quota_set': self.test_quota('test')})

        for u in ('test', 'tenant-id', 'tenant-id/defaults',
                  '%s/defaults' % uuid2):
            httpretty.register_uri(httpretty.GET, self.url(u),
                                   body=test_json,
                                   content_type='application/json')

        quota_json = jsonutils.dumps({'quota_set': self.test_quota(uuid)})
        httpretty.register_uri(httpretty.PUT, self.url(uuid),
                               body=quota_json,
                               content_type='application/json')
        httpretty.register_uri(httpretty.GET, self.url(uuid),
                               body=quota_json,
                               content_type='application/json')

        quota_json2 = jsonutils.dumps({'quota_set': self.test_quota(uuid2)})
        httpretty.register_uri(httpretty.PUT, self.url(uuid2),
                               body=quota_json2,
                               content_type='application/json')
        httpretty.register_uri(httpretty.GET, self.url(uuid2),
                               body=quota_json2,
                               content_type='application/json')

        for u in ('test', uuid2):
            httpretty.register_uri(httpretty.DELETE, self.url(u), status=202)

    def test_quota(self, tenant_id='test'):
        return {
            'tenant_id': tenant_id,
            'metadata_items': [],
            'injected_file_content_bytes': 1,
            'injected_file_path_bytes': 1,
            'ram': 1,
            'floating_ips': 1,
            'instances': 1,
            'injected_files': 1,
            'cores': 1,
            'keypairs': 1,
            'security_groups': 1,
            'security_group_rules': 1
        }


class V3(V1):

    def setUp(self):
        super(V3, self).setUp()

        get_detail = {
            'quota_set': {
                'cores': {'reserved': 0, 'in_use': 0, 'limit': 10},
                'instances': {'reserved': 0, 'in_use': 4, 'limit': 50},
                'ram': {'reserved': 0, 'in_use': 1024, 'limit': 51200}
            }
        }

        httpretty.register_uri(httpretty.GET, self.url('test', 'detail'),
                               body=jsonutils.dumps(get_detail),
                               content_type='application/json')
