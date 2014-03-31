# Copyright 2011 OpenStack LLC.
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
Disk Config extension
"""

from novaclient import utils
from novaclient.v1_1 import servers
from novaclient.v1_1 import shell

API_DISK_CONFIG = "OS-DCF:diskConfig"

# This function was removed from python-novaclient, so we are defining it here
# So the add_args() function will work again.

def add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(f, 'arguments'):
        f.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in f.arguments:
        # Because of the semantics of the decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        f.arguments.insert(0, (args, kwargs))

def add_args():
    add_arg(shell.do_boot,
        '--disk-config',
        default=None,
        metavar='<auto|manual>',
        help="Whether to expand primary partition to fill disk."
             " This overrides the value inherited from image.")


def bind_args_to_resource_manager(args):
    def add_disk_config(args):
        return dict(disk_config=args.disk_config)

    utils.add_resource_manager_extra_kwargs_hook(
            shell.do_boot, add_disk_config)


def add_modify_body_hook():
    def modify_body_for_create(body, **kwargs):
        disk_config = kwargs.get('disk_config')
        if disk_config:
            disk_config = disk_config.upper()

            if disk_config in ('AUTO', 'MANUAL'):
                body["server"][API_DISK_CONFIG] = disk_config
            else:
                raise Exception("Unrecognized disk_config '%s'" % disk_config)

    servers.ServerManager.add_hook(
            'modify_body_for_create', modify_body_for_create)


def __pre_parse_args__():
    add_args()


def __post_parse_args__(args):
    bind_args_to_resource_manager(args)
    add_modify_body_hook()
