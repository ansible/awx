# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    # Automation Platform Controller documentation fragment
    DOCUMENTATION = r'''
options:
  controller_host:
    description:
    - URL to your Automation Platform Controller instance.
    - If value not set, will try environment variable C(CONTROLLER_HOST) and then config files
    - If value not specified by any means, the value of C(127.0.0.1) will be used
    type: str
    aliases: [ tower_host ]
  controller_username:
    description:
    - Username for your controller instance.
    - If value not set, will try environment variable C(CONTROLLER_USERNAME) and then config files
    type: str
    aliases: [ tower_username ]
  controller_password:
    description:
    - Password for your controller instance.
    - If value not set, will try environment variable C(CONTROLLER_PASSWORD) and then config files
    type: str
    aliases: [ tower_password ]
  controller_oauthtoken:
    description:
    - The OAuth token to use.
    - This value can be in one of two formats.
    - A string which is the token itself. (i.e. bqV5txm97wqJqtkxlMkhQz0pKhRMMX)
    - A dictionary structure as returned by the token module.
    - If value not set, will try environment variable C(CONTROLLER_OAUTH_TOKEN) and then config files
    type: raw
    version_added: "3.7.0"
    aliases: [ tower_oauthtoken ]
  validate_certs:
    description:
    - Whether to allow insecure connections to AWX.
    - If C(no), SSL certificates will not be validated.
    - This should only be used on personally controlled sites using self-signed certificates.
    - If value not set, will try environment variable C(CONTROLLER_VERIFY_SSL) and then config files
    type: bool
    aliases: [ tower_verify_ssl ]
  request_timeout:
    description:
    - Specify the timeout Ansible should use in requests to the controller host.
    - Defaults to 10s, but this is handled by the shared module_utils code
    type: float
  controller_config_file:
    description:
    - Path to the controller config file.
    - If provided, the other locations for config files will not be considered.
    type: path
    aliases: [tower_config_file]

notes:
- If no I(config_file) is provided we will attempt to use the tower-cli library
  defaults to find your host information.
- I(config_file) should be in the following format
    host=hostname
    username=username
    password=password
'''
