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

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes
from novaclient.v1_1 import cloudpipe


cs = fakes.FakeClient()


class CloudpipeTest(utils.TestCase):

    def test_list_cloudpipes(self):
        cp = cs.cloudpipe.list()
        cs.assert_called('GET', '/os-cloudpipe')
        [self.assertIsInstance(c, cloudpipe.Cloudpipe) for c in cp]

    def test_create(self):
        project = "test"
        cp = cs.cloudpipe.create(project)
        body = {'cloudpipe': {'project_id': project}}
        cs.assert_called('POST', '/os-cloudpipe', body)
        self.assertIsInstance(cp, str)

    def test_update(self):
        cs.cloudpipe.update("192.168.1.1", 2345)
        body = {'configure_project': {'vpn_ip': "192.168.1.1",
                                      'vpn_port': 2345}}
        cs.assert_called('PUT', '/os-cloudpipe/configure-project', body)
