from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import sys

from unittest import mock

import pytest
from requests.models import Response


def mock_ping_response(self, method, url, **kwargs):
    r = Response()
    r.getheader = lambda header_name, default: {
        'X-API-Product-Name': 'AWX',
        'X-API-Product-Version': '1.0.0',
    }.get(header_name, default)
    r.read = lambda: json.dumps({})
    r.status = 200
    return r


class TestAapTokenParsing:
    """Tests for aap_token parameter parsing in ControllerModule.__init__"""

    def test_string_token(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={'controller_host': 'https://localhost', 'aap_token': 'my-gateway-token'},
        )
        assert module.oauth_token == 'my-gateway-token'

    def test_dict_token_with_token_key(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={'controller_host': 'https://localhost', 'aap_token': {'token': 'dict-token-value', 'id': 1}},
        )
        assert module.oauth_token == 'dict-token-value'

    def test_dict_token_missing_token_key(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        with pytest.raises(SystemExit):
            ControllerAPIModule(
                argument_spec={},
                direct_params={'controller_host': 'https://localhost', 'aap_token': {'id': 1}},
            )

    def test_invalid_token_type(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        with pytest.raises(SystemExit):
            ControllerAPIModule(
                argument_spec={},
                direct_params={'controller_host': 'https://localhost', 'aap_token': 12345},
            )

    def test_no_token(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={'controller_host': 'https://localhost'},
        )
        assert module.oauth_token is None

    def test_env_var_fallback(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        cli_data = {'ANSIBLE_MODULE_ARGS': {}}
        testargs = ['module_file.py', json.dumps(cli_data)]
        with mock.patch.object(sys, 'argv', testargs):
            with mock.patch.dict('os.environ', {'CONTROLLER_OAUTH_TOKEN': 'env-token', 'CONTROLLER_HOST': 'https://localhost'}):
                module = ControllerAPIModule(argument_spec={})
        assert module.oauth_token == 'env-token'


class TestBearerAuthHeader:
    """Tests for Bearer auth header in make_request"""

    def test_bearer_header_sent_when_token_present(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={'controller_host': 'https://localhost', 'aap_token': 'my-gateway-token'},
        )
        module._COLLECTION_TYPE = 'awx'

        captured_headers = {}

        def mock_open(self, method, url, **kwargs):
            captured_headers.update(kwargs.get('headers', {}))
            r = Response()
            r.status_code = 200
            r._content = json.dumps({'count': 0, 'results': []}).encode()
            r.getheader = lambda h, d: None
            r.read = lambda: r._content
            r.status = 200
            return r

        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_open):
            module.make_request('GET', 'job_templates')

        assert 'Authorization' in captured_headers
        assert captured_headers['Authorization'] == 'Bearer my-gateway-token'

    def test_basic_auth_used_without_token(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={
                'controller_host': 'https://localhost',
                'controller_username': 'admin',
                'controller_password': 'password',
            },
        )
        module._COLLECTION_TYPE = 'awx'

        captured_headers = {}

        def mock_open(self, method, url, **kwargs):
            captured_headers.update(kwargs.get('headers', {}))
            r = Response()
            r.status_code = 200
            r._content = json.dumps({'count': 0, 'results': []}).encode()
            r.getheader = lambda h, d: None
            r.read = lambda: r._content
            r.status = 200
            return r

        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_open):
            module.make_request('GET', 'job_templates')

        assert 'Authorization' in captured_headers
        assert captured_headers['Authorization'].startswith('Basic ')

    def test_token_skips_basic_auth(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={'controller_host': 'https://localhost', 'aap_token': 'my-gateway-token'},
        )
        module._COLLECTION_TYPE = 'awx'

        def mock_open(self, method, url, **kwargs):
            r = Response()
            r.status_code = 200
            r._content = json.dumps({'count': 0, 'results': []}).encode()
            r.getheader = lambda h, d: None
            r.read = lambda: r._content
            r.status = 200
            return r

        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_open):
            with mock.patch.object(module, '_authenticate_with_basic_auth') as mock_basic:
                module.make_request('GET', 'job_templates')
                mock_basic.assert_not_called()

    def test_token_precedence_over_username_password(self, collection_import):
        ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
        module = ControllerAPIModule(
            argument_spec={},
            direct_params={
                'controller_host': 'https://localhost',
                'aap_token': 'my-gateway-token',
                'controller_username': 'admin',
                'controller_password': 'password',
            },
        )
        module._COLLECTION_TYPE = 'awx'

        captured_headers = {}

        def mock_open(self, method, url, **kwargs):
            captured_headers.update(kwargs.get('headers', {}))
            r = Response()
            r.status_code = 200
            r._content = json.dumps({'count': 0, 'results': []}).encode()
            r.getheader = lambda h, d: None
            r.read = lambda: r._content
            r.status = 200
            return r

        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_open):
            module.make_request('GET', 'job_templates')

        assert captured_headers['Authorization'] == 'Bearer my-gateway-token'
