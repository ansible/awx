from .plugin import CredentialPlugin, raise_for_status
from django.utils.translation import gettext_lazy as _
from urllib.parse import urljoin
import requests

pas_inputs = {
    'fields': [
        {
            'id': 'url',
            'label': _('Centrify Tenant URL'),
            'type': 'string',
            'help_text': _('Centrify Tenant URL'),
            'format': 'url',
        },
        {
            'id': 'client_id',
            'label': _('Centrify API User'),
            'type': 'string',
            'help_text': _('Centrify API User, having necessary permissions as mentioned in support doc'),
        },
        {
            'id': 'client_password',
            'label': _('Centrify API Password'),
            'type': 'string',
            'help_text': _('Password of Centrify API User with necessary permissions'),
            'secret': True,
        },
        {
            'id': 'oauth_application_id',
            'label': _('OAuth2 Application ID'),
            'type': 'string',
            'help_text': _('Application ID of the configured OAuth2 Client (defaults to \'awx\')'),
            'default': 'awx',
        },
        {
            'id': 'oauth_scope',
            'label': _('OAuth2 Scope'),
            'type': 'string',
            'help_text': _('Scope of the configured OAuth2 Client (defaults to \'awx\')'),
            'default': 'awx',
        },
    ],
    'metadata': [
        {
            'id': 'account-name',
            'label': _('Account Name'),
            'type': 'string',
            'help_text': _('Local system account or Domain account name enrolled in Centrify Vault. eg. (root or DOMAIN/Administrator)'),
        },
        {
            'id': 'system-name',
            'label': _('System Name'),
            'type': 'string',
            'help_text': _('Machine Name enrolled with in Centrify Portal'),
        },
    ],
    'required': ['url', 'account-name', 'system-name', 'client_id', 'client_password'],
}


# generate bearer token to authenticate with PAS portal, Input : Client ID, Client Secret
def handle_auth(**kwargs):
    post_data = {"grant_type": "client_credentials", "scope": kwargs['oauth_scope']}
    response = requests.post(kwargs['endpoint'], data=post_data, auth=(kwargs['client_id'], kwargs['client_password']), verify=True, timeout=(5, 30))
    raise_for_status(response)
    try:
        return response.json()['access_token']
    except KeyError:
        raise RuntimeError('OAuth request to tenant was unsuccessful')


# fetch the ID of system with RedRock query, Input : System Name, Account Name
def get_ID(**kwargs):
    endpoint = urljoin(kwargs['url'], '/Redrock/query')
    name = " Name='{0}' and User='{1}'".format(kwargs['system_name'], kwargs['acc_name'])
    query = 'Select ID from VaultAccount where {0}'.format(name)
    post_headers = {"Authorization": "Bearer " + kwargs['access_token'], "X-CENTRIFY-NATIVE-CLIENT": "true"}
    response = requests.post(endpoint, json={'Script': query}, headers=post_headers, verify=True, timeout=(5, 30))
    raise_for_status(response)
    try:
        result_str = response.json()["Result"]["Results"]
        return result_str[0]["Row"]["ID"]
    except (IndexError, KeyError):
        raise RuntimeError("Error Detected!! Check the Inputs")


# CheckOut Password from Centrify Vault, Input : ID
def get_passwd(**kwargs):
    endpoint = urljoin(kwargs['url'], '/ServerManage/CheckoutPassword')
    post_headers = {"Authorization": "Bearer " + kwargs['access_token'], "X-CENTRIFY-NATIVE-CLIENT": "true"}
    response = requests.post(endpoint, json={'ID': kwargs['acc_id']}, headers=post_headers, verify=True, timeout=(5, 30))
    raise_for_status(response)
    try:
        return response.json()["Result"]["Password"]
    except KeyError:
        raise RuntimeError("Password Not Found")


def centrify_backend(**kwargs):
    url = kwargs.get('url')
    acc_name = kwargs.get('account-name')
    system_name = kwargs.get('system-name')
    client_id = kwargs.get('client_id')
    client_password = kwargs.get('client_password')
    app_id = kwargs.get('oauth_application_id', 'awx')
    endpoint = urljoin(url, f'/oauth2/token/{app_id}')
    endpoint = {'endpoint': endpoint, 'client_id': client_id, 'client_password': client_password, 'oauth_scope': kwargs.get('oauth_scope', 'awx')}
    token = handle_auth(**endpoint)
    get_id_args = {'system_name': system_name, 'acc_name': acc_name, 'url': url, 'access_token': token}
    acc_id = get_ID(**get_id_args)
    get_pwd_args = {'url': url, 'acc_id': acc_id, 'access_token': token}
    return get_passwd(**get_pwd_args)


centrify_plugin = CredentialPlugin('Centrify Vault Credential Provider Lookup', inputs=pas_inputs, backend=centrify_backend)
