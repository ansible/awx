# -*- coding: utf-8 -*-
#
# Copyright 2013 Red Hat, Inc.
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

import argparse

from ironicclient.common import utils
from ironicclient.openstack.common import cliutils


def _print_driver_show(driver):
    fields = ['name', 'hosts']
    data = dict([(f, getattr(driver, f, '')) for f in fields])
    cliutils.print_dict(data, wrap=72)


def do_driver_list(cc, args):
    """List the enabled drivers."""
    drivers = cc.driver.list()
    # NOTE(lucasagomes): Separate each host by a comma.
    # It's easier to read.
    for d in drivers:
        d.hosts = ', '.join(d.hosts)
    field_labels = ['Supported driver(s)', 'Active host(s)']
    fields = ['name', 'hosts']
    cliutils.print_list(drivers, fields, field_labels=field_labels)


@cliutils.arg('driver_name', metavar='<driver>',
              help='Name of the driver.')
def do_driver_show(cc, args):
    """Show information about a driver."""
    driver = cc.driver.get(args.driver_name)
    _print_driver_show(driver)


@cliutils.arg('driver_name', metavar='<driver>',
              help="Name of the driver.")
def do_driver_properties(cc, args):
    """Get properties of a driver."""
    properties = cc.driver.properties(args.driver_name)
    obj_list = []
    for key, value in properties.iteritems():
        data = {'Property': key, 'Description': value}
        obj_list.append(type('iface', (object,), data))
    fields = ['Property', 'Description']
    cliutils.print_list(obj_list, fields, mixed_case_fields=fields)


@cliutils.arg('driver_name',
              metavar='<driver>',
              help='Name of the driver.')
@cliutils.arg('method',
              metavar='<method>',
              help="Vendor-passthru method to be called.")
@cliutils.arg('arguments',
              metavar='<arg=value>',
              nargs='*',
              action='append',
              default=[],
              help="Argument to be passed to the vendor-passthru method. "
                   "Can be specified multiple times.")
@cliutils.arg('--http-method',
              metavar='<http-method>',
              choices=['POST', 'PUT', 'GET', 'DELETE', 'PATCH'],
              help="The HTTP method to use in the request. Valid HTTP "
              "methods are: 'POST', 'PUT', 'GET', 'DELETE', and 'PATCH'. "
              "Defaults to 'POST'.")
@cliutils.arg('--http_method',
              help=argparse.SUPPRESS)
def do_driver_vendor_passthru(cc, args):
    """Call a vendor-passthru extension for a driver."""
    arguments = utils.args_array_to_dict({'args': args.arguments[0]},
                                         'args')['args']

    # If there were no arguments for the method, arguments will still
    # be an empty list. So make it an empty dict.
    if not arguments:
        arguments = {}

    resp = cc.driver.vendor_passthru(args.driver_name, args.method,
                                     http_method=args.http_method,
                                     args=arguments)
    if resp:
        # Print the raw response we don't know how it should be formated
        print(str(resp.to_dict()))
