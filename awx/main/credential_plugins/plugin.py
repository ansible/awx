import os
import tempfile

from collections import namedtuple

from requests.exceptions import HTTPError

CredentialPlugin = namedtuple('CredentialPlugin', ['name', 'inputs', 'backend'])


def raise_for_status(resp):
    resp.raise_for_status()
    if resp.status_code >= 300:
        exc = HTTPError()
        setattr(exc, 'response', resp)
        raise exc


class CertFiles():
    """
    A context manager used for writing a certificate and (optional) key
    to $TMPDIR, and cleaning up afterwards.

    This is particularly useful as a shared resource for credential plugins
    that want to pull cert/key data out of the database and persist it
    temporarily to the file system so that it can loaded into the openssl
    certificate chain (generally, for HTTPS requests plugins make via the
    Python requests library)

    with CertFiles(cert_data, key_data) as cert:
        # cert is string representing a path to the cert or pemfile
        # temporarily written to disk
        requests.post(..., cert=cert)
    """

    certfile = None

    def __init__(self, cert, key=None):
        self.cert = cert
        self.key = key

    def __enter__(self):
        if not self.cert:
            return None
        self.certfile = tempfile.NamedTemporaryFile('wb', delete=False)
        self.certfile.write(self.cert.encode())
        if self.key:
            self.certfile.write(b'\n')
            self.certfile.write(self.key.encode())
        self.certfile.flush()
        return str(self.certfile.name)

    def __exit__(self, *args):
        if self.certfile and os.path.exists(self.certfile.name):
            os.remove(self.certfile.name)
