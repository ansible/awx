# Copyright (c) 2025 Akeyless Security Ltd.
# All Rights Reserved.

import collections
import logging
from typing import Dict, Any
import json

from akeyless import Configuration, ApiClient, V2Api, Auth, DescribeItem, GetSecretValue
from akeyless.rest import ApiException
from akeyless.models.item import Item
from akeyless.models.item_general_info import ItemGeneralInfo
from akeyless.models.static_secret_details_info import StaticSecretDetailsInfo


SUPPORTED_ITEM_TYPES = ['STATIC_SECRET']

logger = logging.getLogger('awx.main.credential_plugins.akeyless')
logger.setLevel(logging.DEBUG)
logger.info('Akeyless credential plugin initialized')

AkeylessCredentialPlugin = collections.namedtuple('AkeylessCredentialPlugin', ['name', 'namespace', 'kind', 'inputs', 'backend', 'injectors'])


def akeyless_backend(**kwargs) -> str:
    """
    Backend function to retrieve secrets from Akeyless Vault.

    Args:
        gateway_url: Akeyless Gateway URL
        access_id: API Access ID
        access_key: API Access Key
        ca_cert: Optional CA certificate for TLS verification
        secret_path: Path to the secret in Akeyless
        secret_key: Optional specific key within the secret to retrieve

    Returns:
        str: The secret value or specific key value

    Raises:
        Exception: If authentication fails or secret cannot be retrieved
    """

    logger.info('=== AKEYLESS BACKED CALLED ===')
    logger.info(f"Received kwargs: {kwargs}")

    # Extract credential inputs
    gateway_url = kwargs.get('gateway_url')
    access_id = kwargs.get('access_id')
    access_key = kwargs.get('access_key')
    ca_cert = kwargs.get('ca_cert')

    # Extract metadata for secret lookup
    secret_path = kwargs.get('secret_path')
    secret_key = kwargs.get('secret_key')

    if not all([gateway_url, access_id, access_key, secret_path]):
        raise Exception("Missing required parameters: gateway_url, access_id, access_key, and secret_path are required")

    try:
        # Configure Akeyless client
        configuration = Configuration()
        configuration.host = gateway_url.rstrip('/')

        # Add CA certificate if provided
        # if ca_cert:
        #     configuration.ssl_ca_cert = ca_cert

        # Create API client
        api_client = ApiClient(configuration)
        api_client.user_agent = 'AWX'
        api_client.default_headers['akeylessclienttype'] = 'AWX'

        api_instance = V2Api(api_client)

        # Authenticate
        logger.info(f"Authenticating with Akeyless...")
        auth_body = Auth(access_id=access_id, access_key=access_key)
        auth_response = api_instance.auth(auth_body)

        # TODO move to debug for prod
        logger.info(f"Auth response: {auth_response}")

        if not auth_response.token:
            raise Exception("Failed to authenticate with Akeyless: No token received")

        t_token = auth_response.token

        # Describe the item
        # TODO move to debug for prod
        logger.info(f"Describing item '{secret_path}'...")
        describe_item_request_body = DescribeItem(name=secret_path, token=t_token)
        describe_item_response: Item = api_instance.describe_item(describe_item_request_body)

        # TODO move to debug for prod
        logger.info(f"Describe item response: {describe_item_response}, type: {type(describe_item_response)}")

        item_type = describe_item_response.item_type

        if item_type not in SUPPORTED_ITEM_TYPES:
            raise NotImplementedError(f"Secret '{secret_path}' is of type '{item_type}' is not supported (supported types: {SUPPORTED_ITEM_TYPES})")

        # Get the static secret format (e.g. text, json, key/value)
        item_general_info: ItemGeneralInfo = describe_item_response.item_general_info
        static_secret_info: StaticSecretDetailsInfo = item_general_info.static_secret_info
        static_secret_format: str = static_secret_info.format
        static_secret_sub_type: str = describe_item_response.item_sub_type

        # TODO move to debug for prod
        logger.info(f"Static secret format is '{static_secret_format}'")

        # Get secret value
        get_secret_body = GetSecretValue(names=[secret_path], token=t_token)
        secret_response = api_instance.get_secret_value(get_secret_body)

        # TODO move to debug for prod
        logger.info(f"Secret response: {secret_response}")

        # Retrieve the static secret value depending on the format
        if static_secret_format == 'text':

            if static_secret_sub_type == 'password':
                if secret_key:
                    if secret_key in ['username', 'password']:
                        secret_data = secret_response[secret_path]
                        secret_dict = json.loads(secret_data)
                        secret_value = secret_dict[secret_key]
                    else:
                        raise NotImplementedError(
                            f"Static secret sub type '{static_secret_sub_type}' does not have the key '{secret_key}', only 'username' and 'password' are supported"
                        )
                else:
                    secret_value = secret_response[secret_path]

            elif static_secret_sub_type == 'generic':
                secret_value = secret_response[secret_path]
            else:
                raise NotImplementedError(f"Static secret sub type '{static_secret_sub_type}' is not supported (supported sub types: 'password', 'generic')")
        elif static_secret_format == 'json' or static_secret_format == 'key-value':
            secret_data = secret_response[secret_path]
            # If a specific key is requested, try to parse as JSON and extract the key
            # Otherwise, return the entire secret data
            if secret_key:
                secret_dict = json.loads(secret_data)
                if secret_key in secret_dict:
                    secret_value = secret_dict[secret_key]
                else:
                    raise KeyError(f"Key '{secret_key}' not found in secret at path: {secret_path}")
            else:
                secret_value = str(secret_data)
        else:
            raise NotImplementedError(f"Static secret format '{static_secret_format}' is not supported (supported formats: 'text', 'json', 'key-value')")

        # TODO remove for prod
        logger.info(f"Secret value: '{secret_value}' (type: {type(secret_value)})")
        return secret_value
    except ApiException as e:
        logger.error(f"Akeyless API error: {e.reason} (Status: {e.status})")
        raise Exception(f"Akeyless API error: {e.reason} (Status: {e.status})")
    except Exception as e:
        logger.error(f"Failed to retrieve secret from Akeyless: {str(e)}")
        raise Exception(f"Failed to retrieve secret from Akeyless: {str(e)}")


inputs: Dict[str, Any] = {}
inputs['fields'] = [
    {
        'id': 'gateway_url',
        'label': 'Gateway URL',
        'type': 'string',
        'help_text': 'The URL of your Akeyless Gateway (e.g., https://api.akeyless.io, https://my.akeyless.gw/api/v2)',
        'required': True,
        'default': 'https://api.akeyless.io',
    },
    {
        'id': 'access_id',
        'label': 'Access ID',
        'type': 'string',
        'help_text': 'Your Akeyless API Access ID',
        'required': True,
    },
    {
        'id': 'access_key',
        'label': 'Access Key',
        'type': 'string',
        'help_text': 'Your Akeyless API Access Key',
        'secret': True,
        'required': True,
    },
    {
        'id': 'ca_cert',
        'label': 'CA Certificate',
        'type': 'string',
        'multiline': True,
        'help_text': 'Optional CA certificate for TLS verification (PEM format)',
        'required': False,
    },
]
inputs['metadata'] = [
    {
        'id': 'secret_path',
        'label': 'Secret Path',
        'type': 'string',
        'help_text': 'The path to the secret in Akeyless (e.g., /myapp/database/password)',
        'required': True,
    },
    {
        'id': 'secret_key',
        'label': 'Secret Key',
        'type': 'string',
        'help_text': 'Optional specific key within the secret to retrieve (for JSON secrets)',
        'required': False,
    },
]
inputs['required'] = ['gateway_url', 'access_id', 'access_key', 'secret_path']

akeyless_plugin = AkeylessCredentialPlugin(
    'Akeyless',
    namespace='akeyless',
    kind='external',
    inputs=inputs,
    backend=akeyless_backend,
    injectors={},
)
