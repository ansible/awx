from .plugin import CredentialPlugin

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from delinea.secrets.vault import PasswordGrantAuthorizer, SecretsVault
from base64 import b64decode

dsv_inputs = {
    'fields': [
        {
            'id': 'tenant',
            'label': _('Tenant'),
            'help_text': _('The tenant e.g. "ex" when the URL is https://ex.secretsvaultcloud.com'),
            'type': 'string',
        },
        {
            'id': 'tld',
            'label': _('Top-level Domain (TLD)'),
            'help_text': _('The TLD of the tenant e.g. "com" when the URL is https://ex.secretsvaultcloud.com'),
            'choices': ['ca', 'com', 'com.au', 'eu'],
            'default': 'com',
        },
        {
            'id': 'client_id',
            'label': _('Client ID'),
            'type': 'string',
        },
        {
            'id': 'client_secret',
            'label': _('Client Secret'),
            'type': 'string',
            'secret': True,
        },
    ],
    'metadata': [
        {
            'id': 'path',
            'label': _('Secret Path'),
            'type': 'string',
            'help_text': _('The secret path e.g. /test/secret1'),
        },
        {
            'id': 'secret_field',
            'label': _('Secret Field'),
            'help_text': _('The field to extract from the secret'),
            'type': 'string',
        },
        {
            'id': 'secret_decoding',
            'label': _('Should the secret be base64 decoded?'),
            'help_text': _('Specify whether the secret should be base64 decoded, typically used for storing files, such as SSH keys'),
            'choices': ['No Decoding', 'Decode Base64'],
            'type': 'string',
            'default': 'No Decoding',
        },
    ],
    'required': ['tenant', 'client_id', 'client_secret', 'path', 'secret_field', 'secret_decoding'],
}

if settings.DEBUG:
    dsv_inputs['fields'].append(
        {
            'id': 'url_template',
            'label': _('URL template'),
            'type': 'string',
            'default': 'https://{}.secretsvaultcloud.{}',
        }
    )


def dsv_backend(**kwargs):
    tenant_name = kwargs['tenant']
    tenant_tld = kwargs.get('tld', 'com')
    tenant_url_template = kwargs.get('url_template', 'https://{}.secretsvaultcloud.{}')
    client_id = kwargs['client_id']
    client_secret = kwargs['client_secret']
    secret_path = kwargs['path']
    secret_field = kwargs['secret_field']
    # providing a default value to remain backward compatible for secrets that have not specified this option
    secret_decoding = kwargs.get('secret_decoding', 'No Decoding')

    tenant_url = tenant_url_template.format(tenant_name, tenant_tld.strip("."))

    authorizer = PasswordGrantAuthorizer(tenant_url, client_id, client_secret)
    dsv_secret = SecretsVault(tenant_url, authorizer).get_secret(secret_path)

    # files can be uploaded base64 decoded to DSV and thus decoding it only, when asked for
    if secret_decoding == 'Decode Base64':
        return b64decode(dsv_secret['data'][secret_field]).decode()

    return dsv_secret['data'][secret_field]


dsv_plugin = CredentialPlugin(name='Thycotic DevOps Secrets Vault', inputs=dsv_inputs, backend=dsv_backend)
