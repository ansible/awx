# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Ansible Tower documentation fragment
    DOCUMENTATION = r'''
options:
  tower_host:
    description:
    - URL to your Tower or AWX instance.
    - If value not set, will try environment variable C(TOWER_HOST) and then config files
    - If value not specified by any means, the value of C(127.0.0.1) will be used
    type: str
  tower_username:
    description:
    - Username for your Tower or AWX instance.
    - If value not set, will try environment variable C(TOWER_USERNAME) and then config files
    type: str
  tower_password:
    description:
    - Password for your Tower or AWX instance.
    - If value not set, will try environment variable C(TOWER_PASSWORD) and then config files
    type: str
  tower_oauthtoken:
    description:
    - The Tower OAuth token to use.
    - This value can be in one of two formats.
    - A string which is the token itself. (i.e. bqV5txm97wqJqtkxlMkhQz0pKhRMMX)
    - A dictionary structure as returned by the tower_token module.
    - If value not set, will try environment variable C(TOWER_OAUTH_TOKEN) and then config files
    type: raw
    version_added: "3.7"
  validate_certs:
    description:
    - Whether to allow insecure connections to Tower or AWX.
    - If C(no), SSL certificates will not be validated.
    - This should only be used on personally controlled sites using self-signed certificates.
    - If value not set, will try environment variable C(TOWER_VERIFY_SSL) and then config files
    type: bool
    aliases: [ tower_verify_ssl ]
  tower_config_file:
    description:
    - Path to the Tower or AWX config file.
    - If provided, the other locations for config files will not be considered.
    type: path

notes:
- If no I(config_file) is provided we will attempt to use the tower-cli library
  defaults to find your Tower host information.
- I(config_file) should contain Tower configuration in the following format
    host=hostname
    username=username
    password=password
'''
