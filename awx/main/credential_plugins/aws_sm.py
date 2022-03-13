from .plugin import CredentialPlugin
from django.utils.translation import ugettext_lazy as _
import boto3

aws_secretsmanager_inputs = {
    'fields': [
        {
            'id': 'username',
            'label': _('Access Key'),
            'type': 'string'
        },
        {
            'id': 'password',
            'label': _('Secret Key'),
            'type': 'string',
            'secret': True,
        },
        {
            'id': 'region',
            'label': _('Region'),
            'type': 'string'
        },
    ],
    'metadata': [
        {
            'id': 'secret_field',
            'label': _('Secret Name'),
            'type': 'string',
            'help_text': _('The name of the secret to look up.'),
        },
    ],
    'required': ['username', 'password', 'region', 'secret_field'],
}



def aws_secretsmanager_backend(**kwargs):
    session = boto3.session.Session()
    client = session.client(
        service_name = 'secretsmanager',
        aws_access_key_id = kwargs['username'],
        aws_secret_access_key = kwargs['password'],
        region_name = kwargs['region']
    )

    get_secret_value_response = client.get_secret_value(
        SecretId = kwargs['secret_field']
    )

    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        secret = get_secret_value_response['SecretBinary'].decode()

    return secret


aws_secretsmanager_plugin = CredentialPlugin(
        'AWS Secrets Manager',
        inputs=aws_secretsmanager_inputs,
        backend=aws_secretsmanager_backend
)
