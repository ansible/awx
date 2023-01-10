from .plugin import CredentialPlugin
from django.utils.translation import gettext_lazy as _

from thycotic.secrets.server import PasswordGrantAuthorizer, SecretServer, ServerSecret

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
        {
            'id': 'secret_field',
            'label': _('Secret Field'),
            'help_text': _('The field to extract from the secret'),
            'type': 'string',
        },
    ],
    'required': ['server_url', 'username', 'password', 'secret_id', 'secret_field'],
}


def tss_backend(**kwargs):
    authorizer = PasswordGrantAuthorizer(kwargs['server_url'], kwargs['username'], kwargs['password'])
    secret_server = SecretServer(kwargs['server_url'], authorizer)
    secret_dict = secret_server.get_secret(kwargs['secret_id'])
    secret = ServerSecret(**secret_dict)
    #Fix Issue https://github.com/ansible/awx/issues/13384
    # For SSH Key types thycotic is returning a Object of Type <class 'requests.models.Response'>
    # So we need to check whether response is a string or object and based on that we need return value
    
    if type(secret.fields[kwargs['secret_field']].value) != str :
        return secret.fields[kwargs['secret_field']].value.text
    else:
        return secret.fields[kwargs['secret_field']].value

    


tss_plugin = CredentialPlugin(
    'Thycotic Secret Server',
    tss_inputs,
    tss_backend,
)
