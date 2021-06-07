import base64
import os

from awx.main.utils import get_awx_version


def csp(request):
    return {'csp_nonce': base64.encodebytes(os.urandom(32)).decode().rstrip()}


def version(request):
    context = getattr(request, 'parser_context', {})
    return {
        'version': get_awx_version(),
        'tower_version': get_awx_version(),
        'short_tower_version': get_awx_version().split('-')[0],
        'deprecated': getattr(context.get('view'), 'deprecated', False),
    }
