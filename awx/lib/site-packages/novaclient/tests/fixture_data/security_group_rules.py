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
from novaclient.tests import fakes
from novaclient.tests.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'os-security-group-rules'

    def setUp(self):
        super(Fixture, self).setUp()

        rule = {
            'id': 1,
            'parent_group_id': 1,
            'group_id': 2,
            'ip_protocol': 'TCP',
            'from_port': '22',
            'to_port': 22,
            'cidr': '10.0.0.0/8'
        }

        get_rules = {'security_group_rules': [rule]}
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_rules),
                               content_type='application/json')

        for u in (1, 11, 12):
            httpretty.register_uri(httpretty.DELETE, self.url(u), status=202)

        def post_rules(request, url, headers):
            body = jsonutils.loads(request.body.decode('utf-8'))
            assert list(body) == ['security_group_rule']
            fakes.assert_has_keys(body['security_group_rule'],
                                  required=['parent_group_id'],
                                  optional=['group_id', 'ip_protocol',
                                            'from_port', 'to_port', 'cidr'])

            return 202, headers, jsonutils.dumps({'security_group_rule': rule})

        httpretty.register_uri(httpretty.POST, self.url(),
                               body=post_rules,
                               content_type='application/json')
