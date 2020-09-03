from .plugin import CredentialPlugin, CertFiles, raise_for_status

import base64
from urllib.parse import urljoin, quote

from django.utils.translation import ugettext_lazy as _
import requests


conjur_inputs = {
    'fields': [{
        'id': 'url',
        'label': _('Conjur URL'),
        'type': 'string',
        'format': 'url',
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
    account = quote(kwargs['account'], safe='') 
    username = quote(kwargs['username'], safe='')
    secret_path = quote(kwargs['secret_path'], safe='')
    version = kwargs.get('secret_version')
    cacert = kwargs.get('cacert', None)

    auth_kwargs = {
        'headers': {'Content-Type': 'text/plain'},
        'data': api_key,
        'allow_redirects': False,
    }

    with CertFiles(cacert) as cert:
        # https://www.conjur.org/api.html#authentication-authenticate-post
        auth_kwargs['verify'] = cert
        resp = requests.post(
            urljoin(url, '/'.join(['authn', account, username, 'authenticate'])),
            **auth_kwargs
        )
    raise_for_status(resp)
    token = base64.b64encode(resp.content).decode('utf-8')

    lookup_kwargs = {
        'headers': {'Authorization': 'Token token="{}"'.format(token)},
        'allow_redirects': False,
    }

    # https://www.conjur.org/api.html#secrets-retrieve-a-secret-get
    path = urljoin(url, '/'.join([
        'secrets',
        account,
        'variable',
        secret_path
    ]))
    if version:
        path = '?'.join([path, version])

    with CertFiles(cacert) as cert:
        lookup_kwargs['verify'] = cert
        resp = requests.get(path, timeout=30, **lookup_kwargs)
    raise_for_status(resp)
    return resp.text


conjur_plugin = CredentialPlugin(
    'CyberArk Conjur Secret Lookup',
    inputs=conjur_inputs,
    backend=conjur_backend
)
