import base64
import os


def csp(request):
    return {
        'csp_nonce': base64.encodebytes(os.urandom(32)).decode().rstrip(),
    }
