import types
import os

from .utils import (
    PseudoNamespace,
    load_credentials,
    load_projects,
    to_bool,
)

config = PseudoNamespace()


def getvalue(self, name):
    return self.__getitem__(name)


if os.getenv('AWXKIT_BASE_URL'):
    config.base_url = os.getenv('AWXKIT_BASE_URL')

if os.getenv('AWXKIT_CREDENTIAL_FILE'):
    config.credentials = load_credentials(os.getenv('AWXKIT_CREDENTIAL_FILE'))

if os.getenv('AWXKIT_PROJECT_FILE'):
    config.project_urls = load_projects(config.get('AWXKIT_PROJECT_FILE'))

# kludge to mimic pytest.config
config.getvalue = types.MethodType(getvalue, config)

config.assume_untrusted = config.get('assume_untrusted', True)

config.client_connection_attempts = int(os.getenv('AWXKIT_CLIENT_CONNECTION_ATTEMPTS', 5))
config.prevent_teardown = to_bool(os.getenv('AWXKIT_PREVENT_TEARDOWN', False))
config.use_sessions = to_bool(os.getenv('AWXKIT_SESSIONS', False))
