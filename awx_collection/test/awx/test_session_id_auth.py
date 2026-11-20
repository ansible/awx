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
    with mock.patch.object(basic, '_ANSIBLE_ARGS', to_bytes(json.dumps(cli_data))):
        if hasattr(basic, '_ANSIBLE_PROFILE'):
            with mock.patch.object(basic, '_ANSIBLE_PROFILE', 'legacy'):
                return ControllerAPIModule(argument_spec=dict(), **kwargs)
        return ControllerAPIModule(argument_spec=dict(), **kwargs)


def test_session_id_sets_cookies_and_headers(collection_import):
    session_id = {'csrftoken': 'my-csrf-token', 'gateway_sessionid': 'my-session-id'}
    module = make_module(collection_import, {'aap_session_id': session_id})
    assert module.aap_session_id == session_id

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    assert len(calls) == 2, calls
    assert calls[0]['method'] == 'GET'
    assert '/me/' in calls[0]['url']
    assert module.authenticated is True

    cookies = {c.name: c.value for c in module.session.cookies}
    assert cookies['csrftoken'] == 'my-csrf-token'
    assert cookies['gateway_sessionid'] == 'my-session-id'

    assert module.session.headers.get('X-Csrftoken') == 'my-csrf-token'
    assert module.session.headers.get('Referer') is not None


def test_session_id_auth_probe_then_actual_request(collection_import):
    session_id = {'csrftoken': 'tok', 'gateway_sessionid': 'sess'}
    module = make_module(collection_import, {'aap_session_id': session_id})

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    assert len(calls) == 2
    assert '/me/' in calls[0]['url']
    assert '/ping/' in calls[1]['url']


def test_session_id_missing_csrftoken_fails(collection_import):
    errors = []

    def error_callback(**kwargs):
        errors.append(kwargs)
        raise SystemExit(1)

    module = make_module(
        collection_import,
        {'aap_session_id': {'gateway_sessionid': 'sess'}},
        error_callback=error_callback,
    )

    with pytest.raises(SystemExit):
        module.authenticate()

    assert len(errors) == 1
    assert 'csrftoken' in errors[0]['msg']


def test_session_id_missing_gateway_sessionid_fails(collection_import):
    errors = []

    def error_callback(**kwargs):
        errors.append(kwargs)
        raise SystemExit(1)

    module = make_module(
        collection_import,
        {'aap_session_id': {'csrftoken': 'tok'}},
        error_callback=error_callback,
    )

    with pytest.raises(SystemExit):
        module.authenticate()

    assert len(errors) == 1
    assert 'gateway_sessionid' in errors[0]['msg']


def test_session_id_missing_both_keys_fails(collection_import):
    errors = []

    def error_callback(**kwargs):
        errors.append(kwargs)
        raise SystemExit(1)

    module = make_module(
        collection_import,
        {'aap_session_id': {'unrelated_key': 'value'}},
        error_callback=error_callback,
    )

    with pytest.raises(SystemExit):
        module.authenticate()

    assert len(errors) == 1
    assert 'csrftoken' in errors[0]['msg'] and 'gateway_sessionid' in errors[0]['msg']


def test_token_takes_priority_over_session_id(collection_import):
    """When both aap_token and aap_session_id are provided, token wins."""
    session_id = {'csrftoken': 'tok', 'gateway_sessionid': 'sess'}
    module = make_module(collection_import, {
        'aap_token': 'my-bearer-token',
        'aap_session_id': session_id,
    })

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    assert len(calls) == 1, calls
    assert module.session.headers.get('Authorization') == 'Bearer my-bearer-token'
    cookies = {c.name: c.value for c in module.session.cookies}
    assert 'gateway_sessionid' not in cookies


def test_basic_auth_takes_priority_over_session_id(collection_import):
    """When both username/password and aap_session_id are provided, basic auth wins."""
    session_id = {'csrftoken': 'tok', 'gateway_sessionid': 'sess'}
    module = make_module(collection_import, {
        'controller_username': 'admin',
        'controller_password': 'secret',
        'aap_session_id': session_id,
    })

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.get_endpoint('ping')

    assert len(calls) == 2, calls
    assert module.session.headers.get('Authorization', '').startswith('Basic ')
    cookies = {c.name: c.value for c in module.session.cookies}
    assert 'gateway_sessionid' not in cookies


@pytest.mark.parametrize('param', ['controller_session_id', 'gateway_session_id'])
def test_session_id_legacy_aliases(collection_import, param):
    session_id = {'csrftoken': 'tok', 'gateway_sessionid': 'sess'}
    module = make_module(collection_import, {param: session_id})
    assert module.aap_session_id == session_id


def test_session_id_not_authenticated_until_authenticate_called(collection_import):
    session_id = {'csrftoken': 'tok', 'gateway_sessionid': 'sess'}
    module = make_module(collection_import, {'aap_session_id': session_id})
    assert module.authenticated is False


def test_no_auth_info_fails(collection_import):
    errors = []

    def error_callback(**kwargs):
        errors.append(kwargs)
        raise SystemExit(1)

    module = make_module(collection_import, {}, error_callback=error_callback)

    with pytest.raises(SystemExit):
        module.authenticate()

    assert len(errors) == 1
    assert 'No authentication information found' in errors[0]['msg'] or 'Failed to get user info' in errors[0]['msg']


def test_authenticate_is_idempotent(collection_import):
    """Calling authenticate() twice should not re-authenticate."""
    session_id = {'csrftoken': 'tok', 'gateway_sessionid': 'sess'}
    module = make_module(collection_import, {'aap_session_id': session_id})

    opener, calls = make_recorder()
    with mock.patch('ansible.module_utils.urls.Request.open', new=opener):
        module.authenticate()
        module.authenticate()

    me_calls = [c for c in calls if '/me/' in c['url']]
    assert len(me_calls) == 1
