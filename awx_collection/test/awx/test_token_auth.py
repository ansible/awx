from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from requests.models import Response
from unittest import mock


def getheader(self, header_name, default):
    return default


def read(self):
    return json.dumps({})


def status(self):
    return 200


def make_recorder():
    """Build a mock for Request.open that records every call made through it."""
    calls = []

    def opener(self, method, url, **kwargs):
        calls.append({'method': method, 'url': url, 'headers': kwargs.get('headers') or {}})
        r = Response()
        r.getheader = getheader.__get__(r)
        r.read = read.__get__(r)
        r.status = status.__get__(r)
        return r

    return opener, calls


def make_module(collection_import, module_args, **kwargs):
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': module_args}
    # patch the cached args directly: AnsibleModule caches sys.argv parsing in
    # basic._ANSIBLE_ARGS, so patching sys.argv would leak args between tests
    with mock.patch.object(basic, '_ANSIBLE_ARGS', to_bytes(json.dumps(cli_data))):
        # ansible-core 2.21+ also requires a serialization profile alongside the args
        if hasattr(basic, '_ANSIBLE_PROFILE'):
            with mock.patch.object(basic, '_ANSIBLE_PROFILE', 'legacy'):
                return ControllerAPIModule(argument_spec=dict(), **kwargs)
        return ControllerAPIModule(argument_spec=dict(), **kwargs)


@pytest.mark.parametrize(
    'token_value',
    [
        'a-token-string',
        {'token': 'a-token-string', 'id': 1},  # the aap_token fact set by ansible.platform.token
    ],
    ids=['string', 'dict'],
)
def test_aap_token_sends_bearer_header(collection_import, token_value):
    module = make_module(collection_import, {'aap_token': token_value})
    assert module.aap_token == 'a-token-string'

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    assert len(calls) == 1, calls
    assert calls[0]['headers']['Authorization'] == 'Bearer a-token-string'
    assert module.authenticated is True


@pytest.mark.parametrize('param', ['oauth_token', 'controller_oauthtoken', 'tower_oauthtoken'])
def test_aap_token_legacy_aliases(collection_import, param):
    module = make_module(collection_import, {param: 'legacy-token'})
    assert module.aap_token == 'legacy-token'


def test_lookup_oauth_token_option_maps_to_aap_token(collection_import):
    # Older lookup/inventory plugin releases pass options through as direct
    # params keyed by the plugin option name; oauth_token must resolve to
    # aap_token via the argspec alias.
    module = make_module(collection_import, {'oauth_token': 'plugin-token'})
    assert module.aap_token == 'plugin-token'

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    assert calls[0]['headers']['Authorization'] == 'Bearer plugin-token'


def test_config_file_legacy_oauth_token_key(collection_import, tmp_path):
    # tower_cli.cfg-style config files from older releases used the oauth_token key
    config_file = tmp_path / 'tower_cli.cfg'
    config_file.write_text('[general]\nhost = https://127.0.0.1\noauth_token = ini-legacy-token\n')

    module = make_module(collection_import, {'controller_config_file': str(config_file)})
    assert module.aap_token == 'ini-legacy-token'


def test_config_file_aap_token_wins_over_legacy_key(collection_import, tmp_path):
    config_file = tmp_path / 'tower_cli.cfg'
    config_file.write_text('[general]\nhost = https://127.0.0.1\noauth_token = ini-legacy-token\naap_token = ini-new-token\n')

    module = make_module(collection_import, {'controller_config_file': str(config_file)})
    assert module.aap_token == 'ini-new-token'


def test_aap_token_dict_without_token_entry_fails(collection_import):
    errors = []

    def error_callback(**kwargs):
        errors.append(kwargs)
        raise SystemExit(1)

    with pytest.raises(SystemExit):
        make_module(collection_import, {'aap_token': {'id': 1}}, error_callback=error_callback)

    assert 'did not properly contain the token entry' in errors[0]['msg']


def test_no_token_falls_back_to_basic_auth(collection_import):
    module = make_module(collection_import, {'controller_username': 'admin', 'controller_password': 'secret'})

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    # first call is the authentication probe, second is the actual request
    assert len(calls) == 2, calls
    for call in calls:
        assert call['headers']['Authorization'].startswith('Basic '), call
    assert module.authenticated is True
