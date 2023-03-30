from .plugin import CredentialPlugin

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from thycotic.secrets.vault import SecretsVault


dsv_inputs = {
    'fields': [
        {
            'id': 'tenant',
            'label': _('Tenant'),
            'help_text': _('The tenant e.g. "ex" when the URL is https://ex.secretservercloud.com'),
            'type': 'string',
        },
        {
            'id': 'tld',
            'label': _('Top-level Domain (TLD)'),
            'help_text': _('The TLD of the tenant e.g. "com" when the URL is https://ex.secretservercloud.com'),
            'choices': ['ca', 'com', 'com.au', 'com.sg', 'eu'],
            'default': 'com',
        },
        {'id': 'client_id', 'label': _('Client ID'), 'type': 'string'},
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
    ],
    'required': ['tenant', 'client_id', 'client_secret', 'path', 'secret_field'],
}

if settings.DEBUG:
    dsv_inputs['fields'].append(
        {
            'id': 'url_template',
            'label': _('URL template'),
            'type': 'string',
            'default': 'https://{}.secretsvaultcloud.{}/v1',
        }
    )

dsv_plugin = CredentialPlugin(
    'Thycotic DevOps Secrets Vault',
    dsv_inputs,
    lambda **kwargs: SecretsVault(**{k: v for (k, v) in kwargs.items() if k in [field['id'] for field in dsv_inputs['fields']]}).get_secret(kwargs['path'])['data'][kwargs['secret_field']],  # fmt: skip
)
