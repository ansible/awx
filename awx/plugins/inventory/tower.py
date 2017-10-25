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
from urlparse import urljoin


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
    host_name = os.environ.get("TOWER_HOSTNAME", None)
    username = os.environ.get("TOWER_USERNAME", None)
    password = os.environ.get("TOWER_PASSWORD", None)
    ignore_ssl = os.environ.get("TOWER_IGNORE_SSL", "0").lower() in ("1", "yes", "true")
    inventory = os.environ.get("TOWER_INVENTORY", None)

    errors = []
    if not host_name:
        errors.append("Missing TOWER_HOSTNAME in environment")
    if not username:
        errors.append("Missing TOWER_USERNAME in environment")
    if not password:
        errors.append("Missing TOWER_PASSWORD in environment")
    if not inventory:
        errors.append("Missing TOWER_INVENTORY in environment")
    if errors:
        print("\n".join(errors))
        sys.exit(1)
        
    return dict(tower_host=host_name,
                tower_user=username,
                tower_pass=password,
                tower_inventory=inventory,
                ignore_ssl=ignore_ssl)


def read_tower_inventory(tower_host, tower_user, tower_pass, inventory, ignore_ssl=False):
    if not re.match('(?:http|https)://', tower_host):
        tower_host = "https://{}".format(tower_host)
    inventory_url = urljoin(tower_host, "/api/v2/inventories/{}/script/?hostvars=1".format(inventory))
    try:
        response = requests.get(inventory_url,
                                auth=HTTPBasicAuth(tower_user, tower_pass),
                                verify=not ignore_ssl)
        if response.ok:
            return response.json()
        json_reason = response.json()
        reason = json_reason.get('detail', 'Retrieving Tower Inventory Failed')
    except requests.ConnectionError, e:
        reason = "Connection to remote host failed: {}".format(e)
    print(reason)
    sys.exit(1)


def main():
    config = parse_configuration()
    inventory_hosts = read_tower_inventory(config['tower_host'],
                                           config['tower_user'],
                                           config['tower_pass'],
                                           config['tower_inventory'],
                                           ignore_ssl=config['ignore_ssl'])
    print(
        json.dumps(
            inventory_hosts
        )
    )

if __name__ == '__main__':
    main()
