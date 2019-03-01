from .plugin import CredentialPlugin

import base64
import io
from urllib.parse import urljoin, quote_plus

from django.utils.translation import ugettext_lazy as _
import requests


conjur_inputs = {
    'fields': [{
        'id': 'url',
        'label': _('Conjur URL'),
        'type': 'string',
    }, {
        'id': 'api_key',
        'label': _('API Key'),
        'type': 'string',
        'secret': True,
    }, {
        'id': 'account',
        'label': _('Account'),
        'type': 'string',
    }, {
        'id': 'username',
        'label': _('Username'),
        'type': 'string',
    }, {
        'id': 'cacert',
        'label': _('Public Key Certificate'),
        'type': 'string',
        'multiline': True
    }],
    'metadata': [{
        'id': 'secret_path',
        'label': _('Secret Identifier'),
        'type': 'string',
        'help_text': _('The identifier for the secret e.g., /some/identifier'),
    }, {
        'id': 'secret_version',
        'label': _('Secret Version'),
        'type': 'string',
        'help_text': _('Used to specify a specific secret version (if left empty, the latest version will be used).'),
    }],
    'required': ['url', 'api_key', 'account', 'username'],
}


def conjur_backend(**kwargs):
    url = kwargs['url']
    api_key = kwargs['api_key']
    account = quote_plus(kwargs['account'])
    username = quote_plus(kwargs['username'])
    secret_path = quote_plus(kwargs['secret_path'])
    version = kwargs.get('secret_version')
    cert = io.StringIO()
    cert.write(kwargs.get('cacert', ''))

    # https://www.conjur.org/api.html#authentication-authenticate-post
    resp = requests.post(
        urljoin(url, '/'.join(['authn', account, username, 'authenticate'])),
        headers={'Content-Type': 'text/plain'},
        data=api_key,
        verify=cert
    )
    resp.raise_for_status()
    token = base64.b64encode(resp.content).decode('utf-8')

    # https://www.conjur.org/api.html#secrets-retrieve-a-secret-get
    path = urljoin(url, '/'.join([
        'secrets',
        account,
        'variable',
        secret_path
    ]))
    if version:
        path = '?'.join([path, version])
    resp = requests.get(
        path,
        headers={'Authorization': 'Token token="{}"'.format(token)},
        verify=cert
    )
    resp.raise_for_status()
    return resp.text


conjur_plugin = CredentialPlugin(
    'CyberArk Conjur Secret Lookup',
    inputs=conjur_inputs,
    backend=conjur_backend
)
