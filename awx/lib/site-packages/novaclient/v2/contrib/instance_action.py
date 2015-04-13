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

import pprint

from novaclient import base
from novaclient.i18n import _
from novaclient.openstack.common import cliutils
from novaclient import utils


class InstanceActionManager(base.ManagerWithFind):
    resource_class = base.Resource

    def get(self, server, request_id):
        """
        Get details of an action performed on an instance.

        :param request_id: The request_id of the action to get.
        """
        return self._get("/servers/%s/os-instance-actions/%s" %
                         (base.getid(server), request_id), 'instanceAction')

    def list(self, server):
        """
        Get a list of actions performed on an server.
        """
        return self._list('/servers/%s/os-instance-actions' %
                          base.getid(server), 'instanceActions')


@cliutils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to show an action for.'))
@cliutils.arg(
    'request_id',
    metavar='<request_id>',
    help=_('Request ID of the action to get.'))
def do_instance_action(cs, args):
    """Show an action."""
    server = utils.find_resource(cs.servers, args.server)
    action_resource = cs.instance_action.get(server, args.request_id)
    action = action_resource._info
    if 'events' in action:
        action['events'] = pprint.pformat(action['events'])
    utils.print_dict(action)


@cliutils.arg(
    'server',
    metavar='<server>',
    help=_('Name or UUID of the server to list actions for.'))
def do_instance_action_list(cs, args):
    """List actions on a server."""
    server = utils.find_resource(cs.servers, args.server)
    actions = cs.instance_action.list(server)
    utils.print_list(actions,
                     ['Action', 'Request_ID', 'Message', 'Start_Time'],
                     sortby_index=3)
