from .plugin import CredentialPlugin, CertFiles, raise_for_status

from urllib.parse import urljoin, quote

from django.utils.translation import gettext_lazy as _
import requests
import base64
import binascii


conjur_inputs = {
    'fields': [
        {
            'id': 'url',
            'label': _('Conjur URL'),
            'type': 'string',
            'format': 'url',
        },
        {
            'id': 'api_key',
            'label': _('API Key'),
            'type': 'string',
            'secret': True,
        },
        {
            'id': 'account',
            'label': _('Account'),
            'type': 'string',
        },
        {
            'id': 'username',
            'label': _('Username'),
            'type': 'string',
        },
        {'id': 'cacert', 'label': _('Public Key Certificate'), 'type': 'string', 'multiline': True},
    ],
    'metadata': [
        {
            'id': 'secret_path',
            'label': _('Secret Identifier'),
            'type': 'string',
            'help_text': _('The identifier for the secret e.g., /some/identifier'),
        },
        {
            'id': 'secret_version',
            'label': _('Secret Version'),
            'type': 'string',
            'help_text': _('Used to specify a specific secret version (if left empty, the latest version will be used).'),
        },
    ],
    'required': ['url', 'api_key', 'account', 'username'],
}


def _is_base64(s: str) -> bool:
    try:
        return base64.b64encode(base64.b64decode(s.encode("utf-8"))) == s.encode("utf-8")
    except binascii.Error:
        return False


def conjur_backend(**kwargs):
    url = kwargs['url']
    api_key = kwargs['api_key']
    account = quote(kwargs['account'], safe='')
    username = quote(kwargs['username'], safe='')
    secret_path = quote(kwargs['secret_path'], safe='')
    version = kwargs.get('secret_version')
    cacert = kwargs.get('cacert', None)

    auth_kwargs = {
        'headers': {'Content-Type': 'text/plain', 'Accept-Encoding': 'base64'},
        'data': api_key,
        'allow_redirects': False,
    }

    with CertFiles(cacert) as cert:
        # https://www.conjur.org/api.html#authentication-authenticate-post
        auth_kwargs['verify'] = cert
        try:
            resp = requests.post(urljoin(url, '/'.join(['authn', account, username, 'authenticate'])), **auth_kwargs)
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            resp = requests.post(urljoin(url, '/'.join(['api', 'authn', account, username, 'authenticate'])), **auth_kwargs)
    raise_for_status(resp)
    token = resp.content.decode('utf-8')

    lookup_kwargs = {
        'headers': {'Authorization': 'Token token="{}"'.format(token if _is_base64(token) else base64.b64encode(token.encode('utf-8')).decode('utf-8'))},
        'allow_redirects': False,
    }

    # https://www.conjur.org/api.html#secrets-retrieve-a-secret-get
    path = urljoin(url, '/'.join(['secrets', account, 'variable', secret_path]))
    path_conjurcloud = urljoin(url, '/'.join(['api', 'secrets', account, 'variable', secret_path]))
    if version:
        ver = "version={}".format(version)
        path = '?'.join([path, ver])
        path_conjurcloud = '?'.join([path_conjurcloud, ver])

    with CertFiles(cacert) as cert:
        lookup_kwargs['verify'] = cert
        try:
            resp = requests.get(path, timeout=30, **lookup_kwargs)
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            resp = requests.get(path_conjurcloud, timeout=30, **lookup_kwargs)
    raise_for_status(resp)
    return resp.text


conjur_plugin = CredentialPlugin('CyberArk Conjur Secrets Manager Lookup', inputs=conjur_inputs, backend=conjur_backend)
