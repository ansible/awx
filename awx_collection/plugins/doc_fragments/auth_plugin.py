# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible by Red Hat, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    # Automation Platform Controller documentation fragment
    DOCUMENTATION = r'''
options:
  host:
    description: The network address of your Automation Platform Controller host.
    env:
    - name: CONTROLLER_HOST
    - name: TOWER_HOST
      deprecated:
        collection_name: 'awx.awx'
        version: '4.0.0'
        why: Collection name change
        alternatives: 'CONTROLLER_HOST'
  username:
    description: The user that you plan to use to access inventories on the controller.
    env:
    - name: CONTROLLER_USERNAME
    - name: TOWER_USERNAME
      deprecated:
        collection_name: 'awx.awx'
        version: '4.0.0'
        why: Collection name change
        alternatives: 'CONTROLLER_USERNAME'
  password:
    description: The password for your controller user.
    env:
    - name: CONTROLLER_PASSWORD
    - name: TOWER_PASSWORD
      deprecated:
        collection_name: 'awx.awx'
        version: '4.0.0'
        why: Collection name change
        alternatives: 'CONTROLLER_PASSWORD'
  oauth_token:
    description:
    - The OAuth token to use.
    env:
    - name: CONTROLLER_OAUTH_TOKEN
    - name: TOWER_OAUTH_TOKEN
      deprecated:
        collection_name: 'awx.awx'
        version: '4.0.0'
        why: Collection name change
        alternatives: 'CONTROLLER_OAUTH_TOKEN'
  verify_ssl:
    description:
    - Specify whether Ansible should verify the SSL certificate of the controller host.
    - Defaults to True, but this is handled by the shared module_utils code
    type: bool
    env:
    - name: CONTROLLER_VERIFY_SSL
    - name: TOWER_VERIFY_SSL
      deprecated:
        collection_name: 'awx.awx'
        version: '4.0.0'
        why: Collection name change
        alternatives: 'CONTROLLER_VERIFY_SSL'
    aliases: [ validate_certs ]

notes:
- If no I(config_file) is provided we will attempt to use the tower-cli library
  defaults to find your host information.
- I(config_file) should be in the following format
    host=hostname
    username=username
    password=password
'''
