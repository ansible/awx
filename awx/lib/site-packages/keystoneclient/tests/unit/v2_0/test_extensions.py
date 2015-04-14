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

from keystoneclient.tests.unit.v2_0 import utils
from keystoneclient.v2_0 import extensions


class ExtensionTests(utils.TestCase):
    def setUp(self):
        super(ExtensionTests, self).setUp()
        self.TEST_EXTENSIONS = {
            'extensions': {
                "values": [
                    {
                        'name': 'OpenStack Keystone User CRUD',
                        'namespace': 'http://docs.openstack.org/'
                        'identity/api/ext/OS-KSCRUD/v1.0',
                        'updated': '2013-07-07T12:00:0-00:00',
                        'alias': 'OS-KSCRUD',
                        'description':
                        'OpenStack extensions to Keystone v2.0 API'
                        ' enabling User Operations.',
                        'links':
                        '[{"href":'
                        '"https://github.com/openstack/identity-api", "type":'
                        ' "text/html", "rel": "describedby"}]',
                    },
                    {
                        'name': 'OpenStack EC2 API',
                        'namespace': 'http://docs.openstack.org/'
                        'identity/api/ext/OS-EC2/v1.0',
                        'updated': '2013-09-07T12:00:0-00:00',
                        'alias': 'OS-EC2',
                        'description': 'OpenStack EC2 Credentials backend.',
                        'links': '[{"href":'
                        '"https://github.com/openstack/identity-api", "type":'
                        ' "text/html", "rel": "describedby"}]',
                    }
                ]
            }
        }

    def test_list(self):
        self.stub_url('GET', ['extensions'], json=self.TEST_EXTENSIONS)
        extensions_list = self.client.extensions.list()
        self.assertEqual(2, len(extensions_list))
        for extension in extensions_list:
            self.assertIsInstance(extension, extensions.Extension)
            self.assertIsNotNone(extension.alias)
            self.assertIsNotNone(extension.description)
            self.assertIsNotNone(extension.links)
            self.assertIsNotNone(extension.name)
            self.assertIsNotNone(extension.namespace)
            self.assertIsNotNone(extension.updated)
