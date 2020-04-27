from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import sys

from requests.models import Response
from unittest import mock


def getheader(self, header_name, default):
    mock_headers = {'X-API-Product-Name': 'not-junk', 'X-API-Product-Version': '1.2.3'}
    return mock_headers.get(header_name, default)


def read(self):
    return json.dumps({})


def status(self):
    return 200


def mock_ping_response(self, method, url, **kwargs):
    r = Response()
    r.getheader = getheader.__get__(r)
    r.read = read.__get__(r)
    r.status = status.__get__(r)
    return r


def test_version_warning(collection_import, silence_warning):
    TowerModule = collection_import('plugins.module_utils.tower_api').TowerModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    with mock.patch('ansible.module_utils.basic.AnsibleModule.warn') as mock_warn:
        with mock.patch.object(sys, 'argv', testargs):
            with mock.patch('ansible.module_utils.urls.Request.open', new=mock_ping_response):
                my_module = TowerModule(argument_spec=dict())
                my_module._COLLECTION_VERSION = "1.0.0"
                my_module._COLLECTION_TYPE = "not-junk"
                my_module.collection_to_version['not-junk'] = 'not-junk'
                my_module.get_endpoint('ping')
    mock_warn.assert_called_once_with(
        'You are running collection version 1.0.0 but connecting to tower version 1.2.3'
    )


def test_type_warning(collection_import, silence_warning):
    TowerModule = collection_import('plugins.module_utils.tower_api').TowerModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    with mock.patch('ansible.module_utils.basic.AnsibleModule.warn') as mock_warn:
        with mock.patch.object(sys, 'argv', testargs):
            with mock.patch('ansible.module_utils.urls.Request.open', new=mock_ping_response):
                my_module = TowerModule(argument_spec={})
                my_module._COLLECTION_VERSION = "1.2.3"
                my_module._COLLECTION_TYPE = "junk"
                my_module.collection_to_version['junk'] = 'junk'
                my_module.get_endpoint('ping')
    mock_warn.assert_called_once_with(
        'You are using the junk version of this collection but connecting to not-junk'
    )


def test_duplicate_config(collection_import):
    # imports done here because of PATH issues unique to this test suite
    TowerModule = collection_import('plugins.module_utils.tower_api').TowerModule
    data = {
        'name': 'zigzoom',
        'zig': 'zoom',
        'tower_username': 'bob',
        'tower_config_file': 'my_config'
    }

    class DuplicateTestTowerModule(TowerModule):
        def load_config(self, config_path):
            assert config_path == 'my_config'

        def _load_params(self):
            self.params = data

    cli_data = {'ANSIBLE_MODULE_ARGS': data}
    testargs = ['module_file.py', json.dumps(cli_data)]
    with mock.patch('ansible.module_utils.basic.AnsibleModule.warn') as mock_warn:
        with mock.patch.object(sys, 'argv', testargs):
            argument_spec = dict(
                name=dict(required=True),
                zig=dict(type='str'),
            )
            DuplicateTestTowerModule(argument_spec=argument_spec)
    mock_warn.assert_called_once_with(
        'The parameter(s) tower_username were provided at the same time as '
        'tower_config_file. Precedence may be unstable, '
        'we suggest either using config file or params.'
    )
