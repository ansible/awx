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
        'label': 'Secret Path',
        'type': 'string',
        'help_text': 'The path to the secret e.g., /some-engine/some-secret/',
    }, {
        'id': 'secret_field',
        'label': 'Secret Field',
        'type': 'string',
        'help_text': 'The name of the key to look up in the secret.',
    }, {
        'id': 'token',
        'label': 'Token',
        'type': 'string',
        'secret': True,
        'help_text': 'The access token used to authenticate to the Vault server',
    }],
    'required': ['url', 'secret_path', 'secret_field', 'token'],
}


def hashi_backend(**kwargs):
    token = kwargs.get('token')
    url = kwargs.get('url')
    secret_path = kwargs.get('secret_path')
    secret_field = kwargs.get('secret_field', None)
    verify = kwargs.get('verify', False)

    client = Client(url=url, token=token, verify=verify)
    response = client.read(secret_path)

    if secret_field:
        return response['data'][secret_field]
    return response['data']


hashivault_plugin = CredentialPlugin('HashiCorp Vault KV Lookup', inputs=hashi_inputs, backend=hashi_backend)
