# Copyright (c) 2025 Akeyless Security Ltd.
# All Rights Reserved.

import logging
from typing import Dict, Any

try:
    import akeyless
    from akeyless.rest import ApiException
except ImportError:
    akeyless = None
    ApiException = Exception

logger = logging.getLogger('awx.main.credential_plugins.akeyless')


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
    if akeyless is None:
        raise Exception("Akeyless Python SDK is not installed. Please install it with: pip install akeyless")
    
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
        configuration = akeyless.Configuration()
        configuration.host = gateway_url.rstrip('/')
        
        # Add CA certificate if provided
        if ca_cert:
            configuration.ssl_ca_cert = ca_cert
        
        # Create API client
        api_client = akeyless.ApiClient(configuration)
        api_instance = akeyless.V2Api(api_client)
        
        # Authenticate
        auth_body = akeyless.Auth(access_id=access_id, access_key=access_key)
        auth_response = api_instance.auth(auth_body)
        
        if not auth_response.token:
            raise Exception("Failed to authenticate with Akeyless: No token received")
        
        # Set the token for subsequent API calls
        configuration.api_key['Authorization'] = auth_response.token
        configuration.api_key_prefix['Authorization'] = 'Bearer'
        
        # Get secret value
        get_secret_body = akeyless.GetSecretValue(name=secret_path)
        secret_response = api_instance.get_secret_value(get_secret_body)
        
        if not secret_response.value:
            raise Exception(f"Secret not found or empty at path: {secret_path}")
        
        secret_value = secret_response.value
        
        # If a specific key is requested, try to parse as JSON and extract the key
        if secret_key:
            try:
                import json
                secret_dict = json.loads(secret_value)
                if secret_key in secret_dict:
                    return str(secret_dict[secret_key])
                else:
                    raise Exception(f"Key '{secret_key}' not found in secret at path: {secret_path}")
            except (json.JSONDecodeError, TypeError):
                raise Exception(f"Secret at path '{secret_path}' is not valid JSON, cannot extract key '{secret_key}'")
        
        return secret_value
        
    except ApiException as e:
        error_msg = f"Akeyless API error: {e.reason} (Status: {e.status})"
        if e.body:
            try:
                import json
                error_detail = json.loads(e.body)
                if 'error' in error_detail:
                    error_msg += f" - {error_detail['error']}"
            except (json.JSONDecodeError, TypeError):
                pass
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to retrieve secret from Akeyless: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# Define the plugin object
akeyless_plugin = type('AkeylessPlugin', (), {
    'name': 'Akeyless Vault Secret Lookup',
    'namespace': 'akeyless_vault',
    'kind': 'external',
    'inputs': {
        'fields': [
            {
                'id': 'gateway_url',
                'label': 'Gateway URL',
                'type': 'string',
                'help_text': 'The URL of your Akeyless Gateway (e.g., https://your-gateway.akeyless.io)',
                'required': True,
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
        ],
        'metadata': [
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
        ],
    },
    'backend': akeyless_backend,
})()
