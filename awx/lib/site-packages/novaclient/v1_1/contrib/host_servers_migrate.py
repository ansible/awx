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
from novaclient import utils


class HostServersMigrateResponse(base.Resource):
    pass


def _server_migrate(cs, server):
    success = True
    error_message = ""
    try:
        cs.servers.migrate(server['uuid'])
    except Exception as e:
        success = False
        error_message = "Error while migrating instance: %s" % e
    return HostServersMigrateResponse(base.Manager,
                                      {"server_uuid": server['uuid'],
                                       "migration_accepted": success,
                                       "error_message": error_message})


@utils.arg('host', metavar='<host>', help='Name of host.')
def do_host_servers_migrate(cs, args):
    """Migrate all instances of the specified host to other available hosts."""
    hypervisors = cs.hypervisors.search(args.host, servers=True)
    response = []
    for hyper in hypervisors:
        if hasattr(hyper, 'servers'):
            for server in hyper.servers:
                response.append(_server_migrate(cs, server))

    utils.print_list(response,
                     ["Server UUID", "Migration Accepted", "Error Message"])
