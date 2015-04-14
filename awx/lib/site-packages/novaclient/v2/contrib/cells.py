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

from novaclient import base
from novaclient.i18n import _
from novaclient.openstack.common import cliutils
from novaclient import utils


class Cell(base.Resource):
    def __repr__(self):
        return "<Cell: %s>" % self.name


class CellsManager(base.Manager):
    resource_class = Cell

    def get(self, cell_name):
        """
        Get a cell.

        :param cell_name: Name of the :class:`Cell` to get.
        :rtype: :class:`Cell`
        """
        return self._get("/os-cells/%s" % cell_name, "cell")

    def capacities(self, cell_name=None):
        """
        Get capacities for a cell.

        :param cell_name: Name of the :class:`Cell` to get capacities for.
        :rtype: :class:`Cell`
        """
        path = ["%s/capacities" % cell_name, "capacities"][cell_name is None]
        return self._get("/os-cells/%s" % path, "cell")


@cliutils.arg(
    'cell',
    metavar='<cell-name>',
    help=_('Name of the cell.'))
def do_cell_show(cs, args):
    """Show details of a given cell."""
    cell = cs.cells.get(args.cell)
    utils.print_dict(cell._info)


@cliutils.arg(
    '--cell',
    metavar='<cell-name>',
    help=_("Name of the cell to get the capacities."),
    default=None)
def do_cell_capacities(cs, args):
    """Get cell capacities for all cells or a given cell."""
    cell = cs.cells.capacities(args.cell)
    print(_("Ram Available: %s MB") % cell.capacities['ram_free']['total_mb'])
    utils.print_dict(cell.capacities['ram_free']['units_by_mb'],
                     dict_property='Ram(MB)', dict_value="Units")
    print(_("\nDisk Available: %s MB") %
          cell.capacities['disk_free']['total_mb'])
    utils.print_dict(cell.capacities['disk_free']['units_by_mb'],
                     dict_property='Disk(MB)', dict_value="Units")
