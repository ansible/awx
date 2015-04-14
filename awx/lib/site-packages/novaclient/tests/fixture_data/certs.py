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

from novaclient.tests.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'os-certificates'

    def get_os_certificates_root(self, **kw):
        return (
            200,
            {},
            {'certificate': {'private_key': None, 'data': 'foo'}}
        )

    def post_os_certificates(self, **kw):
        return (
            200,
            {},
            {'certificate': {'private_key': 'foo', 'data': 'bar'}}
        )

    def setUp(self):
        super(Fixture, self).setUp()

        get_os_certificate = {
            'certificate': {
                'private_key': None,
                'data': 'foo'
            }
        }
        self.requests.register_uri('GET', self.url('root'),
                                   json=get_os_certificate,
                                   headers=self.json_headers)

        post_os_certificates = {
            'certificate': {
                'private_key': 'foo',
                'data': 'bar'
             }
        }
        self.requests.register_uri('POST', self.url(),
                                   json=post_os_certificates,
                                   headers=self.json_headers)
