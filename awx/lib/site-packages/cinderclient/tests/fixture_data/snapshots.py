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

import json

from cinderclient.tests.fixture_data import base


def _stub_snapshot(**kwargs):
    snapshot = {
        "created_at": "2012-08-28T16:30:31.000000",
        "display_description": None,
        "display_name": None,
        "id": '11111111-1111-1111-1111-111111111111',
        "size": 1,
        "status": "available",
        "volume_id": '00000000-0000-0000-0000-000000000000',
    }
    snapshot.update(kwargs)
    return snapshot


class Fixture(base.Fixture):

    base_url = 'snapshots'

    def setUp(self):
        super(Fixture, self).setUp()

        snapshot_1234 = _stub_snapshot(id='1234')
        self.requests.register_uri('GET', self.url('1234'),
                                   json={'snapshot': snapshot_1234})

        def action_1234(request, context):
            return ''
            body = json.loads(request.body.decode('utf-8'))
            assert len(list(body)) == 1
            action = list(body)[0]
            if action == 'os-reset_status':
                assert 'status' in body['os-reset_status']
            elif action == 'os-update_snapshot_status':
                assert 'status' in body['os-update_snapshot_status']
            else:
                raise AssertionError("Unexpected action: %s" % action)
            return ''
        self.requests.register_uri('POST', self.url('1234', 'action'),
                                   text=action_1234, status_code=202)
