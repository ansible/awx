from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import io
import json
import datetime
import importlib
from contextlib import redirect_stdout
from unittest import mock
import logging

from requests.models import Response

import pytest

from awx.main.tests.functional.conftest import _request
from awx.main.models import Organization, Project, Inventory, Credential, CredentialType


logger = logging.getLogger('awx.main.tests')


def sanitize_dict(din):
    '''Sanitize Django response data to purge it of internal types
    so it may be used to cast a requests response object
    '''
    if isinstance(din, (int, str, type(None), bool)):
        return din  # native JSON types, no problem
    elif isinstance(din, datetime.datetime):
        return din.isoformat()
    elif isinstance(din, list):
        for i in range(len(din)):
            din[i] = sanitize_dict(din[i])
        return din
    elif isinstance(din, dict):
        for k in din.copy().keys():
            din[k] = sanitize_dict(din[k])
        return din
    else:
        return str(din)  # translation proxies often not string but stringlike


@pytest.fixture
def run_module(request):
    # A placeholder to use while modules get converted
    def rf(module_name, module_params, request_user):

        def new_request(self, method, url, **kwargs):
            kwargs_copy = kwargs.copy()
            if 'data' in kwargs:
                if not isinstance(kwargs['data'], dict):
                    kwargs_copy['data'] = json.loads(kwargs['data'])
                else:
                    kwargs_copy['data'] = kwargs['data']
            if 'params' in kwargs and method == 'GET':
                # query params for GET are handled a bit differently by
                # tower-cli and python requests as opposed to REST framework APIRequestFactory
                kwargs_copy.setdefault('data', {})
                if isinstance(kwargs['params'], dict):
                    kwargs_copy['data'].update(kwargs['params'])
                elif isinstance(kwargs['params'], list):
                    for k, v in kwargs['params']:
                        kwargs_copy['data'][k] = v

            # make request
            rf = _request(method.lower())
            django_response = rf(url, user=request_user, expect=None, **kwargs_copy)

            # requests library response object is different from the Django response, but they are the same concept
            # this converts the Django response object into a requests response object for consumption
            resp = Response()
            py_data = django_response.data
            sanitize_dict(py_data)
            resp._content = bytes(json.dumps(django_response.data), encoding='utf8')
            resp.status_code = django_response.status_code

            if request.config.getoption('verbose') > 0:
                logger.info(
                    '%s %s by %s, code:%s',
                    method, '/api/' + url.split('/api/')[1],
                    request_user.username, resp.status_code
                )

            return resp

        def new_open(self, method, url, **kwargs):
            r = new_request(self, method, url, **kwargs)
            return mock.MagicMock(read=mock.MagicMock(return_value=r._content), status=r.status_code)

        stdout_buffer = io.StringIO()
        # Requies specific PYTHONPATH, see docs
        # Note that a proper Ansiballz explosion of the modules will have an import path like:
        # ansible_collections.awx.awx.plugins.modules.{}
        # We should consider supporting that in the future
        resource_module = importlib.import_module('plugins.modules.{0}'.format(module_name))

        if not isinstance(module_params, dict):
            raise RuntimeError('Module params must be dict, got {0}'.format(type(module_params)))

        # Ansible params can be passed as an invocation argument or over stdin
        # this short circuits within the AnsibleModule interface
        def mock_load_params(self):
            self.params = module_params

        with mock.patch.object(resource_module.TowerModule, '_load_params', new=mock_load_params):
            # Call the test utility (like a mock server) instead of issuing HTTP requests
            with mock.patch('ansible.module_utils.urls.Request.open', new=new_open):
                with mock.patch('tower_cli.api.Session.request', new=new_request):
                    # Ansible modules return data to the mothership over stdout
                    with redirect_stdout(stdout_buffer):
                        try:
                            resource_module.main()
                        except SystemExit:
                            pass  # A system exit indicates successful execution

        module_stdout = stdout_buffer.getvalue().strip()
        result = json.loads(module_stdout)
        return result

    return rf


@pytest.fixture
def organization():
    return Organization.objects.create(name='Default')


@pytest.fixture
def project(organization):
    return Project.objects.create(
        name="test-proj",
        description="test-proj-desc",
        organization=organization,
        playbook_files=['helloworld.yml'],
        local_path='_92__test_proj',
        scm_revision='1234567890123456789012345678901234567890',
        scm_url='localhost',
        scm_type='git'
    )


@pytest.fixture
def inventory(organization):
    return Inventory.objects.create(
        name='test-inv',
        organization=organization
    )


@pytest.fixture
def machine_credential(organization):
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()
    return Credential.objects.create(
        credential_type=ssh_type, name='machine-cred',
        inputs={'username': 'test_user', 'password': 'pas4word'}
    )


@pytest.fixture
def vault_credential(organization):
    ct = CredentialType.defaults['vault']()
    ct.save()
    return Credential.objects.create(
        credential_type=ct, name='vault-cred',
        inputs={'vault_id': 'foo', 'vault_password': 'pas4word'}
    )
