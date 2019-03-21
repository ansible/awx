#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Ansible Tower/AWX dynamic inventory script
==========================================

Generates dynamic inventory for Tower

Author: Matthew Jones (@matburt)
"""

import argparse
import re
import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


def parse_configuration():
    """
    Create command line parser for oVirt dynamic inventory script.
    """
    parser = argparse.ArgumentParser(
        description='Ansible dynamic inventory script for Ansible Tower.',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        default=True,
        help='Return all hosts known to Tower given a particular inventory',
    )
    parser.parse_args()
    host_name = os.environ.get("TOWER_HOST", None)
    username = os.environ.get("TOWER_USERNAME", None)
    password = os.environ.get("TOWER_PASSWORD", None)
    ignore_ssl = False
    ssl_negative_var = os.environ.get("TOWER_IGNORE_SSL", None)
    if ssl_negative_var:
        ignore_ssl = ssl_negative_var.lower() in ("1", "yes", "true")
    else:
        ssl_positive_var = os.environ.get("TOWER_VERIFY_SSL", None)
        if ssl_positive_var:
            ignore_ssl = ssl_positive_var.lower() not in ('true', '1', 't', 'y', 'yes')
    inventory = os.environ.get("TOWER_INVENTORY", None)
    license_type = os.environ.get("TOWER_LICENSE_TYPE", "enterprise")

    errors = []
    if not host_name:
        errors.append("Missing TOWER_HOST in environment")
    if not username:
        errors.append("Missing TOWER_USERNAME in environment")
    if not password:
        errors.append("Missing TOWER_PASSWORD in environment")
    if not inventory:
        errors.append("Missing TOWER_INVENTORY in environment")
    if errors:
        raise RuntimeError("\n".join(errors))

    return dict(tower_host=host_name,
                tower_user=username,
                tower_pass=password,
                tower_inventory=inventory,
                tower_license_type=license_type,
                ignore_ssl=ignore_ssl)


def read_tower_inventory(tower_host, tower_user, tower_pass, inventory, license_type, ignore_ssl=False):
    if not re.match('(?:http|https)://', tower_host):
        tower_host = "https://{}".format(tower_host)
    inventory_url = urljoin(tower_host, "/api/v2/inventories/{}/script/?hostvars=1&towervars=1&all=1".format(inventory.replace('/', '')))
    config_url = urljoin(tower_host, "/api/v2/config/")
    try:
        if license_type != "open":
            config_response = requests.get(config_url,
                                           auth=HTTPBasicAuth(tower_user, tower_pass),
                                           verify=not ignore_ssl)
            if config_response.ok:
                source_type = config_response.json()['license_info']['license_type']
                if not source_type == license_type:
                    raise RuntimeError("Tower server licenses must match: source: {} local: {}".format(source_type,
                                                                                                       license_type))
            else:
                raise RuntimeError("Failed to validate the license of the remote Tower: {}".format(config_response))

        response = requests.get(inventory_url,
                                auth=HTTPBasicAuth(tower_user, tower_pass),
                                verify=not ignore_ssl)
        if not response.ok:
            # If the GET /api/v2/inventories/N/script is not HTTP 200, print the error code
            msg = "Connection to remote host failed: {}".format(response)
            if response.text:
                msg += " with message: {}".format(response.text)
            raise RuntimeError(msg)
        try:
            # Attempt to parse JSON
            return response.json()
        except (ValueError, TypeError) as e:
            # If the JSON parse fails, print the ValueError
            raise RuntimeError("Failed to parse json from host: {}".format(e))
    except requests.ConnectionError as e:
        raise RuntimeError("Connection to remote host failed: {}".format(e))


def main():
    config = parse_configuration()
    inventory_hosts = read_tower_inventory(config['tower_host'],
                                           config['tower_user'],
                                           config['tower_pass'],
                                           config['tower_inventory'],
                                           config['tower_license_type'],
                                           ignore_ssl=config['ignore_ssl'])
    print(
        json.dumps(
            inventory_hosts
        )
    )


if __name__ == '__main__':
    main()
