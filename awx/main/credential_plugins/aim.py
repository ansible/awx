from .plugin import CredentialPlugin, CertFiles, raise_for_status

from urllib.parse import quote, urlencode, urljoin

from django.utils.translation import ugettext_lazy as _
import requests

aim_inputs = {
    'fields': [{
        'id': 'url',
        'label': _('CyberArk AIM URL'),
        'type': 'string',
        'format': 'url',
    }, {
        'id': 'app_id',
        'label': _('Application ID'),
        'type': 'string',
        'secret': True,
    }, {
        'id': 'client_key',
        'label': _('Client Key'),
        'type': 'string',
        'secret': True,
        'multiline': True,
    }, {
        'id': 'client_cert',
        'label': _('Client Certificate'),
        'type': 'string',
        'secret': True,
        'multiline': True,
    }, {
        'id': 'verify',
        'label': _('Verify SSL Certificates'),
        'type': 'boolean',
        'default': True,
    }],
    'metadata': [{
        'id': 'object_query',
        'label': _('Object Query'),
        'type': 'string',
        'help_text': _('Lookup query for the object. Ex: Safe=TestSafe;Object=testAccountName123'),
    }, {
        'id': 'object_query_format',
        'label': _('Object Query Format'),
        'type': 'string',
        'default': 'Exact',
        'choices': ['Exact', 'Regexp']
    }, {
        'id': 'reason',
        'label': _('Reason'),
        'type': 'string',
        'help_text': _('Object request reason. This is only needed if it is required by the object\'s policy.')
    }],
    'required': ['url', 'app_id', 'object_query'],
}


def aim_backend(**kwargs):
    url = kwargs['url']
    client_cert = kwargs.get('client_cert', None)
    client_key = kwargs.get('client_key', None)
    verify = kwargs['verify']
    app_id = kwargs['app_id']
    object_query = kwargs['object_query']
    object_query_format = kwargs['object_query_format']
    reason = kwargs.get('reason', None)

    query_params = {
        'AppId': app_id,
        'Query': object_query,
        'QueryFormat': object_query_format,
    }
    if reason:
        query_params['reason'] = reason

    request_qs = '?' + urlencode(query_params, quote_via=quote)
    request_url = urljoin(url, '/'.join(['AIMWebService', 'api', 'Accounts']))

    with CertFiles(client_cert, client_key) as cert:
        res = requests.get(
            request_url + request_qs,
            timeout=30,
            cert=cert,
            verify=verify,
            allow_redirects=False,
        )
    raise_for_status(res)
    return res.json()['Content']


aim_plugin = CredentialPlugin(
    'CyberArk AIM Central Credential Provider Lookup',
    inputs=aim_inputs,
    backend=aim_backend
)
