# Copyright 2013 Rackspace Hosting
# All Rights Reserved.
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
from novaclient.tests.unit import utils
from novaclient.tests.unit.v2.contrib import fakes
from novaclient.v2.contrib import cells


extensions = [
    extension.Extension(cells.__name__.split(".")[-1],
                        cells),
]
cs = fakes.FakeClient(extensions=extensions)


class CellsExtensionTests(utils.TestCase):
    def test_get_cells(self):
        cell_name = 'child_cell'
        cs.cells.get(cell_name)
        cs.assert_called('GET', '/os-cells/%s' % cell_name)

    def test_get_capacities_for_a_given_cell(self):
        cell_name = 'child_cell'
        cs.cells.capacities(cell_name)
        cs.assert_called('GET', '/os-cells/%s/capacities' % cell_name)

    def test_get_capacities_for_all_cells(self):
        cs.cells.capacities()
        cs.assert_called('GET', '/os-cells/capacities')
