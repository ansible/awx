import os
import pathlib

from .plugin import CredentialPlugin

from hvac import Client


base_inputs = {
    'fields': [{
        'id': 'url',
        'label': 'Server URL',
        'type': 'string',
        'help_text': 'The URL to the HashiCorp Vault',
    }, {
        'id': 'token',
        'label': 'Token',
        'type': 'string',
        'secret': True,
        'help_text': 'The access token used to authenticate to the Vault server',
    }, {
        'id': 'secret_path',
        'label': 'Path to Secret',
        'type': 'string',
        'help_text': 'The path to the secret e.g., /some-engine/some-secret/',
    }],
    'required': ['url', 'token', 'secret_path'],
}

hashi_kv_inputs = {
    'fields': base_inputs['fields'] + [{
        'id': 'secret_field',
        'label': 'Key Name',
        'type': 'string',
        'help_text': 'The name of the key to look up in the secret.',
    }, {
        'id': 'secret_version',
        'label': 'Secret Version (v2 only)',
        'type': 'string',
        'help_text': 'Used to specify a specific secret version (if left empty, the latest version will be used).',
    }, {
        'id': 'api_version',
        'label': 'API Version',
        'choices': ['v1', 'v2'],
        'help_text': 'API v1 is for static key/value lookups.  API v2 is for versioned key/value lookups.',
        'default': 'v1',
    }],
    'required': base_inputs['required'] + ['secret_field', 'api_version']
}

hashi_ssh_inputs = {
    'fields': base_inputs['fields'] + [{
        'id': 'role',
        'label': 'Role Name',
        'type': 'string',
        'help_text': 'The name of the role used to sign.'
    }, {
        'id': 'valid_principals',
        'label': 'Valid Principals',
        'type': 'string',
        'help_text': 'Valid principals (either usernames or hostnames) that the certificate should be signed for.',
    }],
    'required': base_inputs['required'] + ['role']
}


def kv_backend(raw, **kwargs):
    token = kwargs['token']
    url = kwargs['url']
    secret_path = kwargs['secret_path']
    secret_field = kwargs.get('secret_field', None)

    api_version = kwargs.get('api_version', None)

    client = Client(url=url, token=token, verify=True)
    if api_version == 'v2':
        try:
            mount_point, *path = pathlib.Path(secret_path.lstrip(os.sep)).parts
            os.path.join(*path)
            response = client.secrets.kv.v2.read_secret_version(
                mount_point=mount_point,
                path=os.path.join(*path),
                version=kwargs.get('secret_version', None)
            )['data']
        except Exception:
            raise RuntimeError(
                'could not read secret {} from {}'.format(secret_path, url)
            )
    else:
        try:
            response = client.read(secret_path)
        except Exception:
            raise RuntimeError(
                'could not read secret {} from {}'.format(secret_path, url)
            )

    if response is None:
        raise RuntimeError(
            'could not read secret {} from {}'.format(secret_path, url)
        )

    if secret_field:
        try:
            return response['data'][secret_field]
        except KeyError:
            raise RuntimeError(
                '{} is not present at {}'.format(secret_field, secret_path)
            )
    return response['data']


def ssh_backend(raw, **kwargs):
    token = kwargs['token']
    url = kwargs['url']

    client = Client(url=url, token=token, verify=True)
    json = {
        'public_key': raw
    }
    if kwargs.get('valid_principals'):
        json['valid_principals'] = kwargs['valid_principals']
    resp = client._adapter.post(
        '/v1/{}/sign/{}'.format(kwargs['secret_path'], kwargs['role']),
        json=json,
    )
    return resp.json()['data']['signed_key']


hashivault_kv_plugin = CredentialPlugin(
    'HashiCorp Vault Secret Lookup',
    inputs=hashi_kv_inputs,
    backend=kv_backend
)

hashivault_ssh_plugin = CredentialPlugin(
    'HashiCorp Vault Signed SSH',
    inputs=hashi_ssh_inputs,
    backend=ssh_backend
)
