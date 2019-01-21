from .plugin import CredentialPlugin

from hvac import Client


hashi_inputs = {
    'fields': [{
        'id': 'url',
        'label': 'Hashivault Server URL',
        'type': 'string',
        'help_text': 'The Hashivault server url.'
    }, {
        'id': 'secret_path',
        'label': 'Secret Path',
        'type': 'string',
        'help_text': 'The path to the secret.'
    }, {
        'id': 'secret_field',
        'label': 'Secret Field',
        'type': 'string',
        'help_text': 'The data field to access on the secret.'
    }, {
        'id': 'token',
        'label': 'Token',
        'type': 'string',
        'secret': True,
        'help_text': 'An access token for the Hashivault server.'
    }],
    'required': ['url', 'secret_path', 'token'],
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


hashivault_plugin = CredentialPlugin('Hashivault', inputs=hashi_inputs, backend=hashi_backend)
