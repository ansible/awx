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
from novaclient.openstack.common.gettextutils import _
from novaclient import utils


class EvacuateHostResponse(base.Resource):
    pass


def _server_evacuate(cs, server, args):
    success = True
    error_message = ""
    try:
        cs.servers.evacuate(server['uuid'], args.target_host,
                            args.on_shared_storage)
    except Exception as e:
        success = False
        error_message = _("Error while evacuating instance: %s") % e
    return EvacuateHostResponse(base.Manager,
                                {"server_uuid": server['uuid'],
                                "evacuate_accepted": success,
                                "error_message": error_message})


@utils.arg('host', metavar='<host>', help='Name of host.')
@utils.arg('--target_host',
           metavar='<target_host>',
           default=None,
           help=_('Name of target host.'))
@utils.arg('--on-shared-storage',
           dest='on_shared_storage',
           action="store_true",
           default=False,
           help=_('Specifies whether all instances files are on shared '
                  ' storage'))
def do_host_evacuate(cs, args):
    """Evacuate all instances from failed host to specified one."""
    hypervisors = cs.hypervisors.search(args.host, servers=True)
    response = []
    for hyper in hypervisors:
        if hasattr(hyper, 'servers'):
            for server in hyper.servers:
                response.append(_server_evacuate(cs, server, args))

    utils.print_list(response,
                     ["Server UUID", "Evacuate Accepted", "Error Message"])
