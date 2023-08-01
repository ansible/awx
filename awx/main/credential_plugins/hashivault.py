import copy
import os
import pathlib
import time
from urllib.parse import urljoin

from .plugin import CredentialPlugin, CertFiles, raise_for_status

import requests
from django.utils.translation import gettext_lazy as _

base_inputs = {
    'fields': [
        {
            'id': 'url',
            'label': _('Server URL'),
            'type': 'string',
            'format': 'url',
            'help_text': _('The URL to the HashiCorp Vault'),
        },
        {
            'id': 'token',
            'label': _('Token'),
            'type': 'string',
            'secret': True,
            'help_text': _('The access token used to authenticate to the Vault server'),
        },
        {
            'id': 'cacert',
            'label': _('CA Certificate'),
            'type': 'string',
            'multiline': True,
            'help_text': _('The CA certificate used to verify the SSL certificate of the Vault server'),
        },
        {'id': 'role_id', 'label': _('AppRole role_id'), 'type': 'string', 'multiline': False, 'help_text': _('The Role ID for AppRole Authentication')},
        {
            'id': 'secret_id',
            'label': _('AppRole secret_id'),
            'type': 'string',
            'multiline': False,
            'secret': True,
            'help_text': _('The Secret ID for AppRole Authentication'),
        },
        {
            'id': 'namespace',
            'label': _('Namespace name (Vault Enterprise only)'),
            'type': 'string',
            'multiline': False,
            'help_text': _('Name of the namespace to use when authenticate and retrieve secrets'),
        },
        {
            'id': 'kubernetes_role',
            'label': _('Kubernetes role'),
            'type': 'string',
            'multiline': False,
            'help_text': _(
                'The Role for Kubernetes Authentication.'
                ' This is the named role, configured in Vault server, for AWX pod auth policies.'
                ' see https://www.vaultproject.io/docs/auth/kubernetes#configuration'
            ),
        },
        {
            'id': 'default_auth_path',
            'label': _('Path to Auth'),
            'type': 'string',
            'multiline': False,
            'default': 'approle',
            'help_text': _('The Authentication path to use if one isn\'t provided in the metadata when linking to an input field. Defaults to \'approle\''),
        },
    ],
    'metadata': [
        {
            'id': 'secret_path',
            'label': _('Path to Secret'),
            'type': 'string',
            'help_text': _(
                (
                    'The path to the secret stored in the secret backend e.g, /some/secret/. It is recommended'
                    ' that you use the secret backend field to identify the storage backend and to use this field'
                    ' for locating a specific secret within that store. However, if you prefer to fully identify'
                    ' both the secret backend and one of its secrets using only this field, join their locations'
                    ' into a single path without any additional separators, e.g, /location/of/backend/some/secret.'
                )
            ),
        },
        {
            'id': 'auth_path',
            'label': _('Path to Auth'),
            'type': 'string',
            'multiline': False,
            'help_text': _('The path where the Authentication method is mounted e.g, approle'),
        },
    ],
    'required': ['url', 'secret_path'],
}

hashi_kv_inputs = copy.deepcopy(base_inputs)
hashi_kv_inputs['fields'].append(
    {
        'id': 'api_version',
        'label': _('API Version'),
        'choices': ['v1', 'v2'],
        'help_text': _('API v1 is for static key/value lookups.  API v2 is for versioned key/value lookups.'),
        'default': 'v1',
    }
)
hashi_kv_inputs['metadata'] = (
    [
        {
            'id': 'secret_backend',
            'label': _('Name of Secret Backend'),
            'type': 'string',
            'help_text': _('The name of the kv secret backend (if left empty, the first segment of the secret path will be used).'),
        }
    ]
    + hashi_kv_inputs['metadata']
    + [
        {
            'id': 'secret_key',
            'label': _('Key Name'),
            'type': 'string',
            'help_text': _('The name of the key to look up in the secret.'),
        },
        {
            'id': 'secret_version',
            'label': _('Secret Version (v2 only)'),
            'type': 'string',
            'help_text': _('Used to specify a specific secret version (if left empty, the latest version will be used).'),
        },
    ]
)
hashi_kv_inputs['required'].extend(['api_version', 'secret_key'])

hashi_ssh_inputs = copy.deepcopy(base_inputs)
hashi_ssh_inputs['metadata'] = (
    [
        {
            'id': 'public_key',
            'label': _('Unsigned Public Key'),
            'type': 'string',
            'multiline': True,
        }
    ]
    + hashi_ssh_inputs['metadata']
    + [
        {'id': 'role', 'label': _('Role Name'), 'type': 'string', 'help_text': _('The name of the role used to sign.')},
        {
            'id': 'valid_principals',
            'label': _('Valid Principals'),
            'type': 'string',
            'help_text': _('Valid principals (either usernames or hostnames) that the certificate should be signed for.'),
        },
    ]
)
hashi_ssh_inputs['required'].extend(['public_key', 'role'])


def handle_auth(**kwargs):
    token = None

    if kwargs.get('token'):
        token = kwargs['token']
    elif kwargs.get('role_id') and kwargs.get('secret_id'):
        token = method_auth(**kwargs, auth_param=approle_auth(**kwargs))
    elif kwargs.get('kubernetes_role'):
        token = method_auth(**kwargs, auth_param=kubernetes_auth(**kwargs))
    else:
        raise Exception('Either token or AppRole/Kubernetes authentication parameters must be set')

    return token


def approle_auth(**kwargs):
    return {'role_id': kwargs['role_id'], 'secret_id': kwargs['secret_id']}


def kubernetes_auth(**kwargs):
    jwt_file = pathlib.Path('/var/run/secrets/kubernetes.io/serviceaccount/token')
    with jwt_file.open('r') as jwt_fo:
        jwt = jwt_fo.read().rstrip()
    return {'role': kwargs['kubernetes_role'], 'jwt': jwt}


def method_auth(**kwargs):
    # get auth method specific params
    request_kwargs = {'json': kwargs['auth_param'], 'timeout': 30}

    # we first try to use the 'auth_path' from the metadata
    # if not found we try to fetch the 'default_auth_path' from inputs
    auth_path = kwargs.get('auth_path') or kwargs['default_auth_path']

    url = urljoin(kwargs['url'], 'v1')
    cacert = kwargs.get('cacert', None)

    sess = requests.Session()
    # Namespace support
    if kwargs.get('namespace'):
        sess.headers['X-Vault-Namespace'] = kwargs['namespace']
    request_url = '/'.join([url, 'auth', auth_path, 'login']).rstrip('/')
    with CertFiles(cacert) as cert:
        request_kwargs['verify'] = cert
        resp = sess.post(request_url, **request_kwargs)
    resp.raise_for_status()
    token = resp.json()['auth']['client_token']
    return token


def kv_backend(**kwargs):
    token = handle_auth(**kwargs)
    url = kwargs['url']
    secret_path = kwargs['secret_path']
    secret_backend = kwargs.get('secret_backend', None)
    secret_key = kwargs.get('secret_key', None)
    cacert = kwargs.get('cacert', None)
    api_version = kwargs['api_version']

    request_kwargs = {
        'timeout': 30,
        'allow_redirects': False,
    }

    sess = requests.Session()
    sess.headers['Authorization'] = 'Bearer {}'.format(token)
    # Compatibility header for older installs of Hashicorp Vault
    sess.headers['X-Vault-Token'] = token
    if kwargs.get('namespace'):
        sess.headers['X-Vault-Namespace'] = kwargs['namespace']

    if api_version == 'v2':
        if kwargs.get('secret_version'):
            request_kwargs['params'] = {'version': kwargs['secret_version']}
        if secret_backend:
            path_segments = [secret_backend, 'data', secret_path]
        else:
            try:
                mount_point, *path = pathlib.Path(secret_path.lstrip(os.sep)).parts
                '/'.join(path)
            except Exception:
                mount_point, path = secret_path, []
            # https://www.vaultproject.io/api/secret/kv/kv-v2.html#read-secret-version
            path_segments = [mount_point, 'data'] + path
    else:
        if secret_backend:
            path_segments = [secret_backend, secret_path]
        else:
            path_segments = [secret_path]

    request_url = urljoin(url, '/'.join(['v1'] + path_segments)).rstrip('/')
    with CertFiles(cacert) as cert:
        request_kwargs['verify'] = cert
        request_retries = 0
        while request_retries < 5:
            response = sess.get(request_url, **request_kwargs)
            # https://developer.hashicorp.com/vault/docs/enterprise/consistency
            if response.status_code == 412:
                request_retries += 1
                time.sleep(1)
            else:
                break
    raise_for_status(response)

    json = response.json()
    if api_version == 'v2':
        json = json['data']

    if secret_key:
        try:
            if (secret_key != 'data') and (secret_key not in json['data']) and ('data' in json['data']):
                return json['data']['data'][secret_key]
            return json['data'][secret_key]
        except KeyError:
            raise RuntimeError('{} is not present at {}'.format(secret_key, secret_path))
    return json['data']


def ssh_backend(**kwargs):
    token = handle_auth(**kwargs)
    url = urljoin(kwargs['url'], 'v1')
    secret_path = kwargs['secret_path']
    role = kwargs['role']
    cacert = kwargs.get('cacert', None)

    request_kwargs = {
        'timeout': 30,
        'allow_redirects': False,
    }

    request_kwargs['json'] = {'public_key': kwargs['public_key']}
    if kwargs.get('valid_principals'):
        request_kwargs['json']['valid_principals'] = kwargs['valid_principals']

    sess = requests.Session()
    sess.headers['Authorization'] = 'Bearer {}'.format(token)
    if kwargs.get('namespace'):
        sess.headers['X-Vault-Namespace'] = kwargs['namespace']
    # Compatability header for older installs of Hashicorp Vault
    sess.headers['X-Vault-Token'] = token
    # https://www.vaultproject.io/api/secret/ssh/index.html#sign-ssh-key
    request_url = '/'.join([url, secret_path, 'sign', role]).rstrip('/')

    with CertFiles(cacert) as cert:
        request_kwargs['verify'] = cert
        request_retries = 0
        while request_retries < 5:
            resp = sess.post(request_url, **request_kwargs)
            # https://developer.hashicorp.com/vault/docs/enterprise/consistency
            if resp.status_code == 412:
                request_retries += 1
                time.sleep(1)
            else:
                break
    raise_for_status(resp)
    return resp.json()['data']['signed_key']


hashivault_kv_plugin = CredentialPlugin('HashiCorp Vault Secret Lookup', inputs=hashi_kv_inputs, backend=kv_backend)

hashivault_ssh_plugin = CredentialPlugin('HashiCorp Vault Signed SSH', inputs=hashi_ssh_inputs, backend=ssh_backend)
