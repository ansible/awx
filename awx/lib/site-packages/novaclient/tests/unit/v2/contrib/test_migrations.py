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
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2 import fakes
from novaclient.v2.contrib import migrations

extensions = [
    extension.Extension(migrations.__name__.split(".")[-1],
                        migrations),
]
cs = fakes.FakeClient(extensions=extensions)


class MigrationsTest(utils.TestCase):

    def test_list_migrations(self):
        ml = cs.migrations.list()
        cs.assert_called('GET', '/os-migrations')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)

    def test_list_migrations_with_filters(self):
        ml = cs.migrations.list('host1', 'finished', 'child1')

        cs.assert_called('GET',
                         '/os-migrations?cell_name=child1&host=host1'
                         '&status=finished')
        for m in ml:
            self.assertIsInstance(m, migrations.Migration)
