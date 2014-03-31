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

"""
migration interface
"""

from six.moves.urllib import parse

from novaclient import base
from novaclient.openstack.common.gettextutils import _
from novaclient import utils


class Migration(base.Resource):
    def __repr__(self):
        return "<Migration: %s>" % self.id


class MigrationManager(base.ManagerWithFind):
    resource_class = Migration

    def list(self, host=None, status=None, cell_name=None):
        """
        Get a list of migrations.
        :param host: (optional) filter migrations by host name.
        :param status: (optional) filter migrations by status.
        :param cell_name: (optional) filter migrations for a cell.
        """
        opts = {}
        if host:
            opts['host'] = host
        if status:
            opts['status'] = status
        if cell_name:
            opts['cell_name'] = cell_name

        # Transform the dict to a sequence of two-element tuples in fixed
        # order, then the encoded string will be consistent in Python 2&3.
        new_opts = sorted(opts.items(), key=lambda x: x[0])

        query_string = "?%s" % parse.urlencode(new_opts) if new_opts else ""

        return self._list("/os-migrations%s" % query_string, "migrations")


@utils.arg('--host',
           dest='host',
           metavar='<host>',
           help=_('Fetch migrations for the given host.'))
@utils.arg('--status',
           dest='status',
           metavar='<status>',
           help=_('Fetch migrations for the given status.'))
@utils.arg('--cell_name',
           dest='cell_name',
           metavar='<cell_name>',
           help=_('Fetch migrations for the given cell_name.'))
def do_migration_list(cs, args):
    """Print a list of migrations."""
    _print_migrations(cs.migrations.list(args.host, args.status,
                                         args.cell_name))


def _print_migrations(migrations):
    fields = ['Source Node', 'Dest Node', 'Source Compute', 'Dest Compute',
            'Dest Host', 'Status', 'Instance UUID', 'Old Flavor',
            'New Flavor', 'Created At', 'Updated At']

    def old_flavor(migration):
        return migration.old_instance_type_id

    def new_flavor(migration):
        return migration.new_instance_type_id

    formatters = {'Old Flavor': old_flavor, 'New Flavor': new_flavor}

    utils.print_list(migrations, fields, formatters)
