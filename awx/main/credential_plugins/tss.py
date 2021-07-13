from .plugin import CredentialPlugin
from django.utils.translation import ugettext_lazy as _

from thycotic.secrets.server import SecretServer, PasswordGrantAuthorizer

tss_inputs = {
    'fields': [
        {
            'id': 'server_url',
            'label': _('Secret Server URL'),
            'help_text': _('The Base URL of Secret Server e.g. https://myserver/SecretServer or https://mytenant.secretservercloud.com'),
            'type': 'string',
        },
        {
            'id': 'username',
            'label': _('Username'),
            'help_text': _('The (Application) user username'),
            'type': 'string',
        },
        {
            'id': 'password',
            'label': _('Password'),
            'help_text': _('The corresponding password'),
            'type': 'string',
            'secret': True,
        },
    ],
    'metadata': [
        {
            'id': 'secret_id',
            'label': _('Secret ID'),
            'help_text': _('The integer ID of the secret'),
            'type': 'string',
        },
    ],
    'required': ['server_url', 'username', 'password', 'secret_id'],
}

tss_plugin = CredentialPlugin(
    'Thycotic Secret Server',
    tss_inputs,
    lambda **kwargs: SecretServer(
        kwargs['server_url'], PasswordGrantAuthorizer(kwargs['server_url'].rstrip('/') + '/oauth2/token', kwargs['username'], kwargs['password'])
    ).get_secret(kwargs['secret_id']),
)
