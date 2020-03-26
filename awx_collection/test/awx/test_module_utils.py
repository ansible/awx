from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import pytest

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


@pytest.mark.parametrize('endpoint, expect', [
    ('users', ('username', None,)),
    ('hosts', ('name', 'inventory',)),
    ('workflow_job_templates', ('name', 'organization')),
    ('workflow_job_template_nodes', ('identifier', 'workflow_job_template'))
])
def test_find_lookup_fields(collection_import, endpoint, expect):
    TowerModule = collection_import('plugins.module_utils.tower_api').TowerModule
    # abuse the self argument here, because initializing a module is hard
    assert TowerModule.find_lookup_fields(endpoint) == expect


@pytest.mark.parametrize('endpoint, spec, expect', [
    ('users', dict(
        username=dict(),
    ), []),
    ('hosts', dict(
        name=dict(),
        inventory=dict(),
        organization=dict(),
    ), ['organization', 'inventory']),
    ('workflow_job_templates', dict(
        name=dict(),
        organization=dict(),
        inventory=dict(),
        webhook_credential=dict(),
    ), ['organization', 'inventory', 'webhook_credential']),
    ('workflow_job_template_nodes', dict(
        identifier=dict(),
        workflow_job_template=dict(),
        organization=dict(),
        inventory=dict(),
        unified_job_template=dict(),
        success_nodes=dict(type='list', elements='str'),
        credentials=dict(type='list', elements='str'),
    ), ['organization', 'workflow_job_template', 'credentials', 'inventory', 'success_nodes', 'unified_job_template'])
])
def test_find_lookup_order(collection_import, endpoint, spec, expect):
    TowerModule = collection_import('plugins.module_utils.tower_api').TowerModule

    def mock_load_params(self):
        self.params = {}

    with mock.patch.object(TowerModule, '_load_params', new=mock_load_params):
        module = TowerModule(argument_spec=spec)
        assert module.find_lookup_order(endpoint) == expect
