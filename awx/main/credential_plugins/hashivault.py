import os
import pathlib

from .plugin import CredentialPlugin

from hvac import Client


hashi_inputs = {
    'fields': [{
        'id': 'url',
        'label': 'Server URL',
        'type': 'string',
        'help_text': 'The URL to the HashiCorp Vault',
    }, {
        'id': 'secret_path',
        'label': 'Path to Secret',
        'type': 'string',
        'help_text': 'The path to the secret e.g., /some-engine/some-secret/',
    }, {
        'id': 'secret_field',
        'label': 'Key Name',
        'type': 'string',
        'help_text': 'The name of the key to look up in the secret.',
    }, {
        'id': 'token',
        'label': 'Token',
        'type': 'string',
        'secret': True,
        'help_text': 'The access token used to authenticate to the Vault server',
    }, {
        'id': 'api_version',
        'label': 'API Version',
        'choices': ['v1', 'v2'],
        'help_text': 'API v1 is for static key/value lookups.  API v2 is for versioned key/value lookups.',
        'default': 'v1',
    }, {
        'id': 'secret_version',
        'label': 'Secret Version (v2 only)',
        'type': 'string',
        'help_text': 'Used to specify a specific secret version (if left empty, the latest version will be used).',
    }],
    'required': ['url', 'secret_path', 'secret_field', 'token', 'api_version'],
}


def hashi_backend(**kwargs):
    token = kwargs.get('token')
    url = kwargs.get('url')
    secret_path = kwargs.get('secret_path')
    secret_field = kwargs.get('secret_field', None)
    verify = kwargs.get('verify', False)

    api_version = kwargs.get('api_version', None)

    client = Client(url=url, token=token, verify=verify)
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


hashivault_plugin = CredentialPlugin(
    'HashiCorp Vault Secret Lookup',
    inputs=hashi_inputs,
    backend=hashi_backend
)
