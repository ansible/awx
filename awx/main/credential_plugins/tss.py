from .plugin import CredentialPlugin
from django.utils.translation import ugettext_lazy as _

from thycotic.secrets.server import SecretServer, PasswordGrantAuthorizer

tss_inputs = {
    'fields': [
        {
            'id': 'server_url',
            'label': _('Secret Server URL'),
            'help_text': _(''),
            'type': 'string',
        },
        {
            'id': 'username',
            'label': _('Username'),
            'help_text': _(''),
            'type': 'string',
        },
        {
            'id': 'password',
            'label': _('Password'),
            'help_text': _(''),
            'type': 'string',
            'secret': True,
        },
    ],
    'metadata': [
        {
            'id': 'secret_id',
            'label': _('Secret ID'),
            'help_text': _(''),
            'type': 'int',
        },
    ],
    'required': ['server_url', 'username', 'password', 'secret_id'],
}


def tss_backend(**kwargs):
    authorizer = PasswordGrantAuthorizer(kwargs['server_url'], kwargs['username'], kwargs['password'])
    return SecretServer(authorizer).get_secret(kwargs['secret_id'])


tss_plugin = CredentialPlugin('Thycotic Secret Server', inputs=tss_inputs, backend=tss_backend)
