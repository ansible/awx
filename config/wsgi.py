import sys
if sys.prefix != '/var/lib/awx/venv/tower':
    raise RuntimeError('Tower virtualenv not activated. Check WSGIPythonHome in Apache configuration.')
from awx.wsgi import application  # NOQA
