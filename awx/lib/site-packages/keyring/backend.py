"""
Keyring implementation support
"""

from __future__ import absolute_import

import abc
import logging

try:
    import importlib
except ImportError:
    pass

try:
    import pkg_resources
except ImportError:
    pass

from . import errors, util
from . import backends
from .util import properties
from .py27compat import add_metaclass, filter


log = logging.getLogger(__name__)


class KeyringBackendMeta(abc.ABCMeta):
    """
    A metaclass that's both an ABCMeta and a type that keeps a registry of
    all (non-abstract) types.
    """
    def __init__(cls, name, bases, dict):
        super(KeyringBackendMeta, cls).__init__(name, bases, dict)
        if not hasattr(cls, '_classes'):
            cls._classes = set()
        classes = cls._classes
        if not cls.__abstractmethods__:
            classes.add(cls)


@add_metaclass(KeyringBackendMeta)
class KeyringBackend(object):
    """The abstract base class of the keyring, every backend must implement
    this interface.
    """

    #@abc.abstractproperty
    def priority(cls):
        """
        Each backend class must supply a priority, a number (float or integer)
        indicating the priority of the backend relative to all other backends.
        The priority need not be static -- it may (and should) vary based
        attributes of the environment in which is runs (platform, available
        packages, etc.).

        A higher number indicates a higher priority. The priority should raise
        a RuntimeError with a message indicating the underlying cause if the
        backend is not suitable for the current environment.

        As a rule of thumb, a priority between zero but less than one is
        suitable, but a priority of one or greater is recommended.
        """

    @properties.ClassProperty
    @classmethod
    def viable(cls):
        with errors.ExceptionRaisedContext() as exc:
            cls.priority
        return not bool(exc)

    @abc.abstractmethod
    def get_password(self, service, username):
        """Get password of the username for the service
        """
        return None

    @abc.abstractmethod
    def set_password(self, service, username, password):
        """Set password for the username of the service
        """
        raise errors.PasswordSetError("reason")

    # for backward-compatibility, don't require a backend to implement
    #  delete_password
    #@abc.abstractmethod
    def delete_password(self, service, username):
        """Delete the password for the username of the service.
        """
        raise errors.PasswordDeleteError("reason")

class Crypter(object):
    """Base class providing encryption and decryption
    """

    @abc.abstractmethod
    def encrypt(self, value):
        """Encrypt the value.
        """
        pass

    @abc.abstractmethod
    def decrypt(self, value):
        """Decrypt the value.
        """
        pass

class NullCrypter(Crypter):
    """A crypter that does nothing
    """

    def encrypt(self, value):
        return value

    def decrypt(self, value):
        return value


def _load_backend(name):
    "Load a backend by name"
    if 'importlib' in globals():
        package = backends.__package__ or backends.__name__
        mod = importlib.import_module('.'+name, package)
    else:
        # Python 2.6 support
        ns = {}
        exec("from .backends import {name} as mod".format(name=name),
            globals(), ns)
        mod = ns['mod']
    # invoke __name__ on each module to ensure it's loaded in demand-import
    # environments
    mod.__name__

def _load_backends():
    "ensure that all keyring backends are loaded"
    backends = ('file', 'Gnome', 'Google', 'keyczar', 'kwallet', 'multi',
        'OS_X', 'pyfs', 'SecretService', 'Windows')
    list(map(_load_backend, backends))
    _load_plugins()

def _load_plugins():
    """
    Locate all setuptools entry points by the name 'keyring backends'
    and initialize them.
    Any third-party library may register an entry point by adding the
    following to their setup.py::

        entry_points = {
            'keyring backends': [
                'plugin_name = mylib.mymodule:initialize_func',
            ],
        },

    `plugin_name` can be anything, and is only used to display the name
    of the plugin at initialization time.

    `initialize_func` is optional, but will be invoked if callable.
    """
    if 'pkg_resources' not in globals():
        return
    group = 'keyring backends'
    entry_points = pkg_resources.iter_entry_points(group=group)
    for ep in entry_points:
        try:
            log.info('Loading %s', ep.name)
            init_func = ep.load()
            if callable(init_func):
                init_func()
        except Exception:
            log.exception("Error initializing plugin %s." % ep)

@util.once
def get_all_keyring():
    """
    Return a list of all implemented keyrings that can be constructed without
    parameters.
    """
    _load_backends()

    def is_class_viable(keyring_cls):
        try:
            keyring_cls.priority
        except RuntimeError:
            return False
        return True

    all_classes = KeyringBackend._classes
    viable_classes = filter(is_class_viable, all_classes)
    return list(util.suppress_exceptions(viable_classes,
        exceptions=TypeError))
