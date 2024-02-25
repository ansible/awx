import boto3
from botocore.exceptions import ClientError

from .plugin import CredentialPlugin
from django.utils.translation import gettext_lazy as _


secrets_manager_inputs = {
    'fields': [
        {
            'id': 'aws_access_key',
            'label': _('AWS Access Key'),
            'type': 'string',
        },
        {
            'id': 'aws_secret_key',
            'label': _('AWS Secret Key'),
            'type': 'string',
            'secret': True,
        },
    ],
    'metadata': [
        {
            'id': 'region_name',
            'label': _('AWS Secrets Manager Region'),
            'type': 'string',
            'help_text': _('Region which the secrets manager is located'),
        },
        {
            'id': 'secret_name',
            'label': _('AWS Secret Name'),
            'type': 'string',
        },
    ],
    'required': ['aws_access_key', 'aws_secret_key', 'region_name', 'secret_name'],
}


def aws_secretsmanager_backend(**kwargs):
    secret_name = kwargs['secret_name']
    region_name = kwargs['region_name']
    aws_secret_access_key = kwargs['aws_secret_key']
    aws_access_key_id = kwargs['aws_access_key']

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager', region_name=region_name, aws_secret_access_key=aws_secret_access_key, aws_access_key_id=aws_access_key_id
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    # Secrets Manager decrypts the secret value using the associated KMS CMK
    # Depending on whether the secret was a string or binary, only one of these fields will be populated
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']

    else:
        secret = get_secret_value_response['SecretBinary']

    return secret


aws_secretmanager_plugin = CredentialPlugin('AWS Secrets Manager lookup', inputs=secrets_manager_inputs, backend=aws_secretsmanager_backend)
