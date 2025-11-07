# Copyright (c) 2025 Akeyless Security Ltd.
# All Rights Reserved.

from ast import List
from dataclasses import dataclass
import logging
import os
import tempfile
from types import SimpleNamespace
from typing import Callable, Dict, Any, Optional, List
import json

from akeyless import Configuration, ApiClient, V2Api, Auth, DescribeItem, GetSecretValue
from akeyless.rest import ApiException
from akeyless.models.item import Item
from akeyless.models.item_general_info import ItemGeneralInfo
from akeyless.models.static_secret_details_info import StaticSecretDetailsInfo
from akeyless.models.get_ssh_certificate import GetSSHCertificate


logger = logging.getLogger('awx.main.credential_plugins.akeyless')

SUPPORTED_ITEM_TYPES = ['STATIC_SECRET']
TMP_CA_CERT_ATTRIBUTE_NAME = '_ca_tmp_file_path'
COMMON_PLUGIN_FIELDS: List[Dict[str, Any]] = [
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
        'help_text': 'Path to the CA certificate for TLS verification (PEM format)',
        'required': False,
    },
]

# COMMON


class AkeylessPlugin(SimpleNamespace):
    def __init__(
        self,
        name: str,
        namespace: str,
        metadata: List[Dict[str, Any]],
        required: List[str],
        backend: Callable,
    ):
        self.name = name
        self.namespace = namespace
        self.kind = 'external'
        self.inputs = {
            'metadata': metadata,
            'required': required,
            'fields': COMMON_PLUGIN_FIELDS,
        }
        self.backend = backend
        self.injectors = {}


def create_plugin(
    name: str,
    namespace: str,
    metadata: List[Dict[str, Any]],
    required: List[str],
    backend: Callable,
) -> AkeylessPlugin:
    """
    Create a new Akeyless plugin.

    Args:
        `name` (``str``): The name of the plugin
        `namespace` (``str``): The namespace of the plugin
        `metadata` (``List[Dict[str, Any]]``): The metadata of the plugin
        `required` (``List[str]``): The required fields of the plugin
        `backend` (``Callable``): The backend of the plugin

    Returns:
        ``AkeylessPlugin``: The Akeyless plugin
    """
    return AkeylessPlugin(
        name=name,
        namespace=namespace,
        metadata=metadata,
        required=required,
        backend=backend,
    )


@dataclass
class CommonPluginInputs:
    gateway_url: str
    access_id: str
    access_key: str
    ca_cert: Optional[str]


def create_ca_cert_file(ca_cert: str) -> str:
    """
    Create a CA certificate file in a temporary directory.

    Args:
        ``ca_cert`` (``str``): The CA certificate in PEM format.

    Returns:
        ``str``: The path to the CA certificate file.
    """
    ca_tmp_file_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".pem") as temp_file:
        temp_file.write(ca_cert)
        ca_tmp_file_path = temp_file.name
    os.chmod(ca_tmp_file_path, 0o600)
    return ca_tmp_file_path


def cleanup_ca_cert_file(ca_tmp_file_path: str):
    """
    Cleanup the CA certificate file.

    Args:
        ``ca_tmp_file_path`` (``str``): The path to the CA certificate file.
    """
    logger.debug(f"Cleaning up CA certificate file '{ca_tmp_file_path}'...")
    if ca_tmp_file_path:
        try:
            os.unlink(ca_tmp_file_path)
            logger.debug(f"CA certificate file '{ca_tmp_file_path}' cleaned up")
        except OSError as e:
            logger.error(f"Failed to cleanup CA certificate file '{ca_tmp_file_path}': {e}", exc_info=True)


def setup_client(plugin_inputs: CommonPluginInputs) -> V2Api:
    """
    Setup the Akeyless client.

    Args:
        ``plugin_inputs`` (``CommonPluginInputs``): Plugin inputs

    Returns:
        ``akeyless.V2Api``: The Akeyless API instance
    """
    logger.debug(f"Setting up Akeyless client with gateway URL '{plugin_inputs.gateway_url}'...")
    client_configuration = Configuration(host=plugin_inputs.gateway_url)
    ca_tmp_file_path = None
    if plugin_inputs.ca_cert:
        logger.debug(f"Setting up Akeyless client with CA certificate...")
        ca_tmp_file_path = create_ca_cert_file(plugin_inputs.ca_cert)
        client_configuration.ssl_ca_cert = ca_tmp_file_path
        client_configuration.verify_ssl = True
    api_client = ApiClient(client_configuration)
    api_client.user_agent = 'AWX'
    api_client.default_headers['akeylessclienttype'] = 'AWX'
    v2_api = V2Api(api_client)
    setattr(v2_api, TMP_CA_CERT_ATTRIBUTE_NAME, ca_tmp_file_path)
    return v2_api


def authenticate(plugin_inputs: CommonPluginInputs, api_instance: V2Api) -> str:
    """
    Authenticate with Akeyless.

    Args:
        ``plugin_inputs`` (``CommonPluginInputs``): Plugin inputs
        ``api_instance`` (``akeyless.V2Api``): The Akeyless API instance

    Returns:
        ``str``: The authentication token.

    Raises:
        ``Exception``: If authentication fails.
    """

    auth_body = Auth(access_id=plugin_inputs.access_id, access_key=plugin_inputs.access_key)
    auth_response = api_instance.auth(auth_body)
    if not auth_response.token:
        raise Exception("Failed to authenticate with Akeyless: No token received")
    return auth_response.token


# SECRETS PLUGIN


@dataclass
class SecretsPluginInputs:
    secret_path: str
    secret_key: Optional[str]


def parse_plugin_inputs(**kwargs) -> CommonPluginInputs:
    """
    Parse plugin inputs.

    Args:
        **kwargs: Keyword arguments

    Returns:
        ``CommonPluginInputs``: Common plugin inputs
    """

    gateway_url = kwargs.get('gateway_url').rstrip('/')
    access_id = kwargs.get('access_id')
    access_key = kwargs.get('access_key')
    ca_cert = kwargs.get('ca_cert')

    if not all([gateway_url, access_id, access_key]):
        raise Exception("Missing required parameters: gateway_url, access_id, and access_key are required")

    return CommonPluginInputs(gateway_url=gateway_url, access_id=access_id, access_key=access_key, ca_cert=ca_cert)


def parse_secrets_plugin_inputs(**kwargs) -> SecretsPluginInputs:
    """
    Parse the secrets plugin inputs.

    Args:
        **kwargs: Keyword arguments

    Returns:
        SecretsPluginInputs: Secrets plugin inputs
    """
    secret_path = kwargs.get('secret_path')
    secret_key = kwargs.get('secret_key')
    return SecretsPluginInputs(secret_path=secret_path, secret_key=secret_key)


def get_secret_value(**kwargs) -> str:
    """
    Backend function to retrieve secrets from Akeyless Vault.

    Args:
        `gateway_url` (``str``): Akeyless Gateway URL
        `access_id` (``str``): API Access ID
        `access_key` (``str``): API Access Key
        `ca_cert` (``str``): Optional CA certificate for TLS verification
        `secret_path` (``str``): Path to the secret in Akeyless
        `secret_key` (``str``): Optional specific key within the secret to retrieve

    Returns:
        ``str``: The secret value or specific key value

    Raises:
        ``Exception``: If authentication fails or secret cannot be retrieved
    """
    plugin_inputs = parse_plugin_inputs(**kwargs)
    secrets_plugin_inputs = parse_secrets_plugin_inputs(**kwargs)

    try:
        # Configure Akeyless client
        api_instance = setup_client(plugin_inputs)

        # Authenticate
        t_token = authenticate(plugin_inputs, api_instance)

        # Describe the item
        logger.debug(f"Describing item '{secrets_plugin_inputs.secret_path}'...")
        describe_item_request_body = DescribeItem(name=secrets_plugin_inputs.secret_path, token=t_token)
        describe_item_response: Item = api_instance.describe_item(describe_item_request_body)

        logger.debug(f"Describe item response: {describe_item_response}")

        item_type = describe_item_response.item_type

        if item_type not in SUPPORTED_ITEM_TYPES:
            raise NotImplementedError(
                f"Secret '{secrets_plugin_inputs.secret_path}' is of type '{item_type}' is not supported (supported types: {SUPPORTED_ITEM_TYPES})"
            )

        # Get the static secret format (e.g. text, json, key/value)
        item_general_info: ItemGeneralInfo = describe_item_response.item_general_info
        static_secret_info: StaticSecretDetailsInfo = item_general_info.static_secret_info
        static_secret_format: str = static_secret_info.format
        static_secret_sub_type: str = describe_item_response.item_sub_type

        logger.debug(f"Static secret format is '{static_secret_format}'")

        # Get secret value
        get_secret_body = GetSecretValue(names=[secrets_plugin_inputs.secret_path], token=t_token)
        secret_response = api_instance.get_secret_value(get_secret_body)

        # Retrieve the static secret value depending on the format
        if static_secret_format == 'text':

            if static_secret_sub_type == 'password':
                if secrets_plugin_inputs.secret_key:
                    if secrets_plugin_inputs.secret_key in ['username', 'password']:
                        secret_data = secret_response[secrets_plugin_inputs.secret_path]
                        secret_dict = json.loads(secret_data)
                        secret_value = secret_dict[secrets_plugin_inputs.secret_key]
                    else:
                        raise NotImplementedError(
                            f"Static secret sub type '{static_secret_sub_type}' does not have the key '{secrets_plugin_inputs.secret_key}', only 'username' and 'password' are supported"
                        )
                else:
                    secret_value = secret_response[secrets_plugin_inputs.secret_path]

            elif static_secret_sub_type == 'generic':
                secret_value = secret_response[secrets_plugin_inputs.secret_path]
            else:
                raise NotImplementedError(f"Static secret sub type '{static_secret_sub_type}' is not supported (supported sub types: 'password', 'generic')")
        elif static_secret_format == 'json' or static_secret_format == 'key-value':
            secret_data = secret_response[secrets_plugin_inputs.secret_path]
            # If a specific key is requested, try to parse as JSON and extract the key
            # Otherwise, return the entire secret data
            if secrets_plugin_inputs.secret_key:
                secret_dict = json.loads(secret_data)
                if secrets_plugin_inputs.secret_key in secret_dict:
                    secret_value = secret_dict[secrets_plugin_inputs.secret_key]
                else:
                    raise KeyError(f"Key '{secrets_plugin_inputs.secret_key}' not found in secret at path: {secrets_plugin_inputs.secret_path}")
            else:
                secret_value = str(secret_data)
        else:
            raise NotImplementedError(f"Static secret format '{static_secret_format}' is not supported (supported formats: 'text', 'json', 'key-value')")

        return secret_value
    except ApiException as e:
        logger.error(f"Akeyless API error: {e.reason} (Status: {e.status})")
        raise Exception(f"Akeyless API error: {e.reason} (Status: {e.status})")
    except Exception as e:
        logger.error(f"Failed to retrieve secret from Akeyless: {str(e)}")
        raise Exception(f"Failed to retrieve secret from Akeyless: {str(e)}")
    finally:
        tmp = getattr(api_instance, TMP_CA_CERT_ATTRIBUTE_NAME, None) if api_instance else None
        if tmp:
            cleanup_ca_cert_file(tmp)


akeyless_plugin = create_plugin(
    name='Akeyless',
    namespace='akeyless',
    metadata=[
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
    required=['gateway_url', 'access_id', 'access_key', 'secret_path'],
    backend=get_secret_value,
)

# SSH PLUGIN


@dataclass
class SSHPluginInputs:
    cert_issue_name: str
    cert_username: str
    public_key_data: str
    ttl: Optional[int]


def parse_ssh_plugin_inputs(**kwargs) -> SSHPluginInputs:
    """
    Parse the ssh plugin inputs.

    Args:
        ``**kwargs``: Keyword arguments

    Returns:
        ``SSHPluginInputs``: SSH plugin inputs
    """

    cert_issue_name = kwargs.get('cert_issue_name')
    cert_username = kwargs.get('cert_username')
    ttl = kwargs.get('ttl')
    public_key_data = kwargs.get('public_key_data')
    return SSHPluginInputs(
        cert_issue_name=cert_issue_name,
        cert_username=cert_username,
        ttl=ttl,
        public_key_data=public_key_data,
    )


def generate_ssh_certificate(
    api_instance: V2Api,
    t_token: str,
    ssh_plugin_inputs: SSHPluginInputs,
) -> str:
    """
    Generate a signed SSH certificate from Akeyless.

    Args:
        ``api_instance`` (``akeyless.V2Api``): The Akeyless API instance
        ``t_token`` (``str``): The authentication token
        ``ssh_plugin_inputs`` (``SSHPluginInputs``): The SSH plugin inputs

    Returns:
        ``str``: The signed SSH public key data (e.g. 'rsa-sha2-256-cert-v01@openssh.com AAAAHHNzaC1yc/2...+/ZHU=')

    Raises:
        ``Exception``: If the SSH certificate cannot be generated
    """

    body = GetSSHCertificate(
        token=t_token,
        cert_issuer_name=ssh_plugin_inputs.cert_issue_name,
        cert_username=ssh_plugin_inputs.cert_username,
        ttl=ssh_plugin_inputs.ttl,
        public_key_data=ssh_plugin_inputs.public_key_data,
    )
    response = api_instance.get_ssh_certificate(body)
    if not response.data:
        raise Exception("Failed to generate signed SSH certificate from Akeyless: No data received")
    return response.data


def create_ssh_certificate(**kwargs) -> str:
    """
    Create a signed SSH certificate from Akeyless.

    Args:
        ``**kwargs``: Keyword arguments

    Returns:
        ``str``: The signed SSH public key data (e.g. 'rsa-sha2-256-cert-v01@openssh.com AAAAHHNzaC1yc/2...+/ZHU=')

    Raises:
        ``Exception``: If the SSH certificate cannot be generated
    """

    plugin_inputs = parse_plugin_inputs(**kwargs)
    ssh_plugin_inputs = parse_ssh_plugin_inputs(**kwargs)

    try:
        api_instance = setup_client(plugin_inputs)

        t_token = authenticate(plugin_inputs, api_instance)

        ssh_certificate = generate_ssh_certificate(api_instance, t_token, ssh_plugin_inputs)
        return ssh_certificate

    except ApiException as e:
        logger.error(f"Akeyless API error: {e.reason} (Status: {e.status})")
        raise Exception(f"Akeyless API error: {e.reason} (Status: {e.status})")
    except Exception as e:
        logger.error(f"Failed to generate signed SSH certificate from Akeyless: {str(e)}")
        raise Exception(f"Failed to generate signed SSH certificate from Akeyless: {str(e)}")
    finally:
        tmp = getattr(api_instance, TMP_CA_CERT_ATTRIBUTE_NAME, None) if api_instance else None
        if tmp:
            cleanup_ca_cert_file(tmp)


akeyless_ssh_plugin = create_plugin(
    name='Akeyless SSH',
    namespace='akeyless_ssh',
    metadata=[
        {
            'id': 'cert_issue_name',
            'label': 'Certificate Issuer Name',
            'type': 'string',
            'help_text': 'The full path to the certificate issuer in Akeyless (e.g., /remote/ssh/certificate/issuer)',
            'required': True,
        },
        {
            'id': 'cert_username',
            'label': 'Certificate Username',
            'type': 'string',
            'help_text': 'The username(s) to sign into the SSH certificate in a comma-separated list, e.g., "ubuntu,nobody,nonroot"',
            'required': True,
        },
        {
            'id': 'public_key_data',
            'label': 'Public Key Data',
            'type': 'string',
            'help_text': 'The public key data to sign the SSH certificate with (e.g. "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDA/ZHU=")',
            'required': True,
        },
        {
            'id': 'ttl',
            'label': 'TTL',
            'type': 'number',
            'help_text': 'Time to live in seconds for the SSH certificate. If not defined, will use the default TTL of the certificate issuer. The value must be larger than the one defined in the certificate issuer.',
            'required': False,
        },
    ],
    required=['gateway_url', 'access_id', 'access_key', 'cert_issue_name', 'cert_username', 'public_key_data'],
    backend=create_ssh_certificate,
)
