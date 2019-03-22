from .plugin import CredentialPlugin

import os
import stat
import tempfile
import threading
from urllib.parse import quote, urlencode, urljoin

from django.utils.translation import ugettext_lazy as _
import requests


aim_inputs = {
    'fields': [{
        'id': 'url',
        'label': _('CyberArk AIM URL'),
        'type': 'string',
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
        'help_text': _('Lookup query for the object. Ex: "Safe=TestSafe;Object=testAccountName123"'),
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
    'required': ['url', 'app_id', 'query'],
}


def create_temporary_fifo(data):
    """Open fifo named pipe in a new thread using a temporary file path. The
    thread blocks until data is read from the pipe.

    Returns the path to the fifo.

    :param data(bytes): Data to write to the pipe.
    """
    path = os.path.join(tempfile.mkdtemp(), next(tempfile._get_candidate_names()))
    os.mkfifo(path, stat.S_IRUSR | stat.S_IWUSR)

    threading.Thread(
        target=lambda p, d: open(p, 'wb').write(d),
        args=(path, data)
    ).start()
    return path


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

    cert = None
    if client_cert and client_key:
        cert = (
            create_temporary_fifo(client_cert.encode()),
            create_temporary_fifo(client_key.encode())
        )
    elif client_cert:
        cert = create_temporary_fifo(client_cert.encode())

    res = requests.get(request_url + request_qs, cert=cert, verify=verify)
    res.raise_for_status()
    return res.json()['Content']


aim_plugin = CredentialPlugin(
    'CyberArk AIM Secret Lookup',
    inputs=aim_inputs,
    backend=aim_backend
)
