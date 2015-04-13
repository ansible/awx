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

from novaclient.tests.unit.fixture_data import certs as data
from novaclient.tests.unit.fixture_data import client
from novaclient.tests.unit import utils
from novaclient.v2 import certs


class CertsTest(utils.FixturedTestCase):

    data_fixture_class = data.Fixture
    cert_type = certs.Certificate

    scenarios = [('original', {'client_fixture_class': client.V1}),
                 ('session', {'client_fixture_class': client.SessionV1})]

    def test_create_cert(self):
        cert = self.cs.certs.create()
        self.assert_called('POST', '/os-certificates')
        self.assertIsInstance(cert, self.cert_type)

    def test_get_root_cert(self):
        cert = self.cs.certs.get()
        self.assert_called('GET', '/os-certificates/root')
        self.assertIsInstance(cert, self.cert_type)
