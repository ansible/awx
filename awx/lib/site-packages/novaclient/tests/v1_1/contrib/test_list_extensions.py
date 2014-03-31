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

from novaclient import extension
from novaclient.v1_1.contrib import list_extensions

from novaclient.tests import utils
from novaclient.tests.v1_1 import fakes


extensions = [
    extension.Extension(list_extensions.__name__.split(".")[-1],
                        list_extensions),
]
cs = fakes.FakeClient(extensions=extensions)


class ListExtensionsTests(utils.TestCase):
    def test_list_extensions(self):
        all_exts = cs.list_extensions.show_all()
        cs.assert_called('GET', '/extensions')
        self.assertTrue(len(all_exts) > 0)
        for r in all_exts:
            self.assertTrue(len(r.summary) > 0)
