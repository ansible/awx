# Copyright 2012 OpenStack LLC.
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

"""
Instance create default networks extension
"""
from novaclient import utils
from novaclient.v1_1 import servers
from novaclient.v1_1 import shell


def add_args():
    utils.add_arg(shell.do_boot,
        '--no-public',
        dest='public',
        action='store_false',
        default=True,
        help='Boot instance without public network connectivity.')
    utils.add_arg(shell.do_boot,
        '--no-service-net',
        dest='service_net',
        action='store_false',
        default=True,
        help='Boot instance without service network connectivity.')


def bind_args_to_resource_manager(args):
    def add_default_networks_config(args):
        return dict(public=args.public, service_net=args.service_net)

    utils.add_resource_manager_extra_kwargs_hook(
            shell.do_boot, add_default_networks_config)


def add_modify_body_hook():
    def modify_body_for_create(body, **kwargs):
        if not body.get('server'):
            # NOTE(tr3buchet) need to figure why this is being triggered on
            # network creates, quick fix for now..
            return
        public = kwargs.get('public')
        service_net = kwargs.get('service_net')
        networks = body['server'].get('networks') or []
        pub_dict = {'uuid': '00000000-0000-0000-0000-000000000000'}
        snet_dict = {'uuid': '11111111-1111-1111-1111-111111111111'}
        if public and pub_dict not in networks:
            networks.append(pub_dict)
        if service_net and snet_dict not in networks:
            networks.append(snet_dict)

        body['server']['networks'] = networks

    servers.ServerManager.add_hook(
            'modify_body_for_create', modify_body_for_create)


def __pre_parse_args__():
    add_args()


def __post_parse_args__(args):
    bind_args_to_resource_manager(args)
    add_modify_body_hook()
