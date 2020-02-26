from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

from unittest import mock

import json


def test_duplicate_config(collection_import):
    # imports done here because of PATH issues unique to this test suite
    TowerModule = collection_import('plugins.module_utils.tower_api').TowerModule
    data = {
        'name': 'zigzoom',
        'zig': 'zoom',
        'tower_username': 'bob',
        'tower_config_file': 'my_config'
    }
    cli_data = {'ANSIBLE_MODULE_ARGS': data}
    testargs = ['module_file.py', json.dumps(cli_data)]
    with mock.patch('ansible.module_utils.basic.AnsibleModule.warn') as mock_warn:
        with mock.patch.object(sys, 'argv', testargs):
            with mock.patch.object(TowerModule, 'load_config') as mock_load:
                argument_spec = dict(
                    name=dict(required=True),
                    zig=dict(type='str'),
                )
                TowerModule(argument_spec=argument_spec)
            mock_load.mock_calls[-1] == mock.call('my_config')
    mock_warn.assert_called_once_with(
        'The parameter(s) tower_username were provided at the same time as '
        'tower_config_file. Precedence may be unstable, '
        'we suggest either using config file or params.'
    )
