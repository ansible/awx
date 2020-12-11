from .plugin import CredentialPlugin, raise_for_status
from django.utils.translation import ugettext_lazy as _
from urllib.parse import urljoin
import requests
import base64
import json
pas_inputs = {
    'fields': [{
        'id': 'url',
        'label': _('Centrify Tenant URL'),
        'type': 'string',
        'help_text': _('Centrify Tenant URL'),
        'format': 'url',
    }, {
        'id':'client_id',
        'label':_('Centrify API User'),
        'type':'string',
        'help_text': _('Centrify API User, having necessary permissions as mentioned in support doc'),

    }, {
        'id':'client_password',
        'label':_('Centrify API Password'),
        'type':'string',
        'help_text': _('Password of Centrify API User with necessary permissions'),
        'secret':True,
    }],
    'metadata': [{
        'id': 'account-name',
        'label': _('Account Name'),
        'type': 'string',
        'help_text': _('Local system account or Domain account name enrolled in Centrify Vault. eg. (root or DOMAIN/Administrator)'),
        'secret': True,
    },{
        'id': 'system-name',
        'label': _('System Name'),
        'type': 'string',
        'help_text': _('Machine Name enrolled with in Centrify Portal'),
    }],
    'required': ['url', 'account-name', 'system-name','client_id','client_password'],
}


# generate bearer token to authenticate with PAS portal, Input : Client ID, Client Secret
def handle_auth(**kwargs):
    tokens = None
    post_data = {
        "grant_type": "client_credentials", 
        "scope":"siem" 
    }
    post_header = {
        "Authorization": 'Basic ' + base64.b64encode(bytes(kwargs['client_id'] + ":" + kwargs['client_password'], 'ascii')).decode('ascii')
    }
    response = requests.post(
        kwargs['endpoint'],
        data = post_data,
        headers = post_header, 
        verify = True,
        timeout = (5, 30)
    )
    raise_for_status(response)
    tokens = json.loads(response.text)
    try: 
        return tokens['access_token']
    except KeyError:
        raise RuntimeError('OAuth request to tenant was unsuccessful')


# fetch the ID of system with RedRock query, Input : System Name, Account Name
def get_ID(**kwargs):
    endpoint = urljoin(kwargs['url'],'/Redrock/query')
    name=" Name='{0}' and User='{1}'".format(kwargs['system_name'],kwargs['acc_name'])
    query  = 'Select * from VaultAccount where {0}'.format(name)
    post_data = json.dumps({'Script': query})
    post_headers = {
        "Authorization": "Bearer " + kwargs['access_token'], 
        "X-CENTRIFY-NATIVE-CLIENT":"true"
    }
    response = requests.post(
        endpoint,
        data = post_data,
        headers = post_headers, 
        timeout = (5, 30)
    )
    raise_for_status(response)
    tokens = json.loads(response.text)
    result_str=tokens["Result"]["Results"]
    try:
        acc_ID=result_str[0]["Row"]["ID"]
        return acc_ID
    except IndexError:
        raise RuntimeError("Error Detected!! Check the Inputs")       


# CheckOut Password from Centrify Vault, Input : ID
def get_passwd(**kwargs):
    endpoint = urljoin(kwargs['url'],'/ServerManage/CheckoutPassword')
    post_data = json.dumps({'ID': kwargs['acc_id']})
    post_headers = {
        "Authorization": "Bearer " + kwargs['access_token'], 
        "X-CENTRIFY-NATIVE-CLIENT":"true"
    }
    response = requests.post(
        endpoint,
        data = post_data,
        headers = post_headers,
        timeout = (5, 30)
    )
    raise_for_status(response)
    tokens=json.loads(response.text)
    try:
        result_str=tokens["Result"]["Password"]
        return result_str
    except TypeError:
        raise RuntimeError("Password Not Found")     


def centrify_backend(**kwargs):
    url = kwargs.get('url')      #
    acc_name = kwargs.get('account-name')
    system_name = kwargs.get('system-name')
    client_id = kwargs.get('client_id')
    client_password = kwargs.get('client_password')
    endpoint = urljoin(url,'/oauth2/token/oauthsiem')
    endpoint = {'endpoint':endpoint,'client_id':client_id,'client_password':client_password}
    token = handle_auth(**endpoint)
    get_id_args = {'system_name':system_name,'acc_name':acc_name,'url':url,'access_token':token}
    acc_id = get_ID(**get_id_args)
    get_pwd_args = {'url':url,'acc_id':acc_id,'access_token':token}
    return get_passwd(**get_pwd_args)


centrify_plugin = CredentialPlugin(
    'Centrify Vault Credential Provider Lookup',
    inputs=pas_inputs,
    backend=centrify_backend
)
