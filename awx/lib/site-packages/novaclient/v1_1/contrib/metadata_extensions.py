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

from novaclient.openstack.common.gettextutils import _
from novaclient import utils
from novaclient.v1_1 import shell


@utils.arg('host',
           metavar='<host>',
           help=_('Name of host.'))
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'delete'],
           help=_("Actions: 'set' or 'delete'"))
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           action='append',
           default=[],
           help=_('Metadata to set or delete (only key is necessary on '
                  'delete)'))
def do_host_meta(cs, args):
    """Set or Delete metadata on all instances of a host."""
    hypervisors = cs.hypervisors.search(args.host, servers=True)
    for hyper in hypervisors:
        metadata = shell._extract_metadata(args)
        if hasattr(hyper, 'servers'):
            for server in hyper.servers:
                if args.action == 'set':
                    cs.servers.set_meta(server['uuid'], metadata)
                elif args.action == 'delete':
                    cs.servers.delete_meta(server['uuid'], metadata.keys())
