from .plugin import CredentialPlugin

from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.common.credentials import ServicePrincipalCredentials


azure_keyvault_inputs = {
    'fields': [{
        'id': 'url',
        'label': 'Vault URL (DNS Name)',
        'type': 'string',
    }, {
        'id': 'client',
        'label': 'Client ID',
        'type': 'string'
    }, {
        'id': 'secret',
        'label': 'Client Secret',
        'type': 'string',
        'secret': True,
    }, {
        'id': 'tenant',
        'label': 'Tenant ID',
        'type': 'string'
    }],
    'metadata': [{
        'id': 'secret_field',
        'label': 'Secret Name',
        'type': 'string',
        'help_text': 'The name of the secret to look up.',
    }, {
        'id': 'secret_version',
        'label': 'Secret Version',
        'type': 'string',
        'help_text': 'Used to specify a specific secret version (if left empty, the latest version will be used).',
    }],
    'required': ['url', 'client', 'secret', 'tenant', 'secret_field'],
}


def azure_keyvault_backend(raw, **kwargs):
    url = kwargs['url']

    def auth_callback(server, resource, scope):
        credentials = ServicePrincipalCredentials(
            url = url,
            client_id = kwargs['client'],
            secret = kwargs['secret'],
            tenant = kwargs['tenant'],
            resource = "https://vault.azure.net",
        )
        token = credentials.token
        return token['token_type'], token['access_token']

    kv = KeyVaultClient(KeyVaultAuthentication(auth_callback))
    return kv.get_secret(url, kwargs['secret_field'], kwargs.get('secret_version', '')).value


azure_keyvault_plugin = CredentialPlugin(
    'Microsoft Azure Key Vault',
    inputs=azure_keyvault_inputs,
    backend=azure_keyvault_backend
)
