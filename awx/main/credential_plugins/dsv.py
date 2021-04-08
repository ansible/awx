from .plugin import CredentialPlugin

from django.conf import settings
from django.utils.translation import get_language, to_locale, ugettext_lazy as _
from thycotic.secrets.vault import SecretsVault


dsv_inputs = {
    'fields': [
        {
            'id': 'tenant',
            'label': _('Tenant'),
            'help_text': _('The tenant e.g. "ex" when the URL is https://ex.secretservercloud.com'),
            'type': 'string',
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
            'id': 'expr',
            'label': _('Attribute Expression'),
            'type': 'string',
            'help_text': _('A Python expression on the dict representation of the secret e.g. "data.username"'),
        },
    ],
    'required': ['tenant', 'client_id', 'client_secret', 'path'],
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

if to_locale(get_language()) != 'en_US':
    dsv_inputs['fields'].append(
        {
            'id': 'tld',
            'label': _('Top-level Domain (TLD)'),
            'help_text': _('The Top-level domain of the tenant e.g. "com" when the URL is https://ex.secretservercloud.com'),
            'type': 'string',
            'default': 'com',
            'choices': ['ca', 'com', 'com.au', 'com.sg', 'eu'],
        }
    )


dsv_plugin = CredentialPlugin(
    'Thycotic DevOps Secrets Vault',
    dsv_inputs,
    lambda **kwargs: eval(
        kwargs['expr'],
        SecretsVault(**{k: v for (k, v) in kwargs.items() if k in [field['id'] for field in dsv_inputs['fields']]}).get_secret(kwargs['path']),
    ),
)
