# flake8: noqa

__all__ = [
    'ExtensionManager',
    'EnabledExtensionManager',
    'NamedExtensionManager',
    'HookManager',
    'DriverManager',
]

from .extension import ExtensionManager
from .enabled import EnabledExtensionManager
from .named import NamedExtensionManager
from .hook import HookManager
from .driver import DriverManager

import logging

# Configure a NullHandler for our log messages in case
# the app we're used from does not set up logging.
LOG = logging.getLogger('stevedore')

if hasattr(logging, 'NullHandler'):
    LOG.addHandler(logging.NullHandler())
else:
    class NullHandler(logging.Handler):
        def handle(self, record):
            pass

        def emit(self, record):
            pass

        def createLock(self):
            self.lock = None

    LOG.addHandler(NullHandler())
