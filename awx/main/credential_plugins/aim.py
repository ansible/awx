from .plugin import CredentialPlugin

import os
import stat
import tempfile
import threading
from urllib.parse import quote, urljoin

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
        'label': _('Client Cert'),
        'type': 'string',
        'secret': True,
        'multiline': True,
    }, {
        'id': 'verify',
        'type': 'boolean',
        'default': True,
        'label': _('Verify'),
        'help_text': _('Verify SSL certificates for HTTPS requests'),
    }],
    'metadata': [{
        'id': 'safe',
        'label': _('Safe'),
        'type': 'string',
    }, {
        'id': 'object',
        'label': _('Object'),
        'type': 'string',
    }],
    'required': ['url', 'app_id', 'safe', 'object'],
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
    verify = kwargs['verify']
    client_cert = kwargs.get('client_cert', None)
    client_key = kwargs.get('client_key', None)
    app_id = quote(kwargs['app_id'])
    safe = quote(kwargs['safe'])
    object_ = quote(kwargs['object'])

    request_qs = '?AppId={0}&Safe={1}&object={2}'.format(app_id, safe, object_)
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
