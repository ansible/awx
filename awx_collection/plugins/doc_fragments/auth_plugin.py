# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible by Red Hat, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Ansible Tower documentation fragment
    DOCUMENTATION = r'''
options:
    host:
        description: The network address of your Ansible Tower host.
        env:
            - name: TOWER_HOST
    username:
        description: The user that you plan to use to access inventories on Ansible Tower.
        env:
            - name: TOWER_USERNAME
    password:
        description: The password for your Ansible Tower user.
        env:
            - name: TOWER_PASSWORD
    oauth_token:
        description:
            - The Tower OAuth token to use.
        env:
            - name: TOWER_OAUTH_TOKEN
    verify_ssl:
        description:
            - Specify whether Ansible should verify the SSL certificate of Ansible Tower host.
            - Defaults to True, but this is handled by the shared module_utils code
        type: bool
        env:
            - name: TOWER_VERIFY_SSL
        aliases: [ validate_certs ]

notes:
- If no I(config_file) is provided we will attempt to use the tower-cli library
  defaults to find your Tower host information.
- I(config_file) should contain Tower configuration in the following format
    host=hostname
    username=username
    password=password
'''
