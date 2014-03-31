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

from novaclient.tests.v1_1 import fakes
from novaclient.tests.v1_1 import test_certs
from novaclient.v3 import certs


class CertsTest(test_certs.CertsTest):
    def setUp(self):
        super(CertsTest, self).setUp()
        self.cs = self._get_fake_client()
        self.cert_type = self._get_cert_type()

    def _get_fake_client(self):
        return fakes.FakeClient()

    def _get_cert_type(self):
        return certs.Certificate
