from azure.keyvault.secrets import SecretClient
from azure.identity import ClientSecretCredential
from msrestazure import azure_cloud

from .plugin import CredentialPlugin

from django.utils.translation import gettext_lazy as _


# https://github.com/Azure/msrestazure-for-python/blob/master/msrestazure/azure_cloud.py
clouds = [vars(azure_cloud)[n] for n in dir(azure_cloud) if n.startswith("AZURE_") and n.endswith("_CLOUD")]
default_cloud = vars(azure_cloud)["AZURE_PUBLIC_CLOUD"]


azure_keyvault_inputs = {
    'fields': [
        {
            'id': 'url',
            'label': _('Vault URL (DNS Name)'),
            'type': 'string',
            'format': 'url',
        },
        {'id': 'client', 'label': _('Client ID'), 'type': 'string'},
        {
            'id': 'secret',
            'label': _('Client Secret'),
            'type': 'string',
            'secret': True,
        },
        {'id': 'tenant', 'label': _('Tenant ID'), 'type': 'string'},
        {
            'id': 'cloud_name',
            'label': _('Cloud Environment'),
            'help_text': _('Specify which azure cloud environment to use.'),
            'choices': list(set([default_cloud.name] + [c.name for c in clouds])),
            'default': default_cloud.name,
        },
    ],
    'metadata': [
        {
            'id': 'secret_field',
            'label': _('Secret Name'),
            'type': 'string',
            'help_text': _('The name of the secret to look up.'),
        },
        {
            'id': 'secret_version',
            'label': _('Secret Version'),
            'type': 'string',
            'help_text': _('Used to specify a specific secret version (if left empty, the latest version will be used).'),
        },
    ],
    'required': ['url', 'client', 'secret', 'tenant', 'secret_field'],
}


def azure_keyvault_backend(**kwargs):
    csc = ClientSecretCredential(tenant_id=kwargs['tenant'], client_id=kwargs['client'], client_secret=kwargs['secret'])
    kv = SecretClient(credential=csc, vault_url=kwargs['url'])
    return kv.get_secret(name=kwargs['secret_field'], version=kwargs.get('secret_version', '')).value


azure_keyvault_plugin = CredentialPlugin('Microsoft Azure Key Vault', inputs=azure_keyvault_inputs, backend=azure_keyvault_backend)
