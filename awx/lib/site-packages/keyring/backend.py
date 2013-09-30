"""
Keyring implementation support
"""

from __future__ import absolute_import

import abc
import itertools

from keyring import errors
from keyring.util import properties

import keyring.util

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


class KeyringBackend(object):
    """The abstract base class of the keyring, every backend must implement
    this interface.
    """
    __metaclass__ = KeyringBackendMeta

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

@keyring.util.once
def get_all_keyring():
    """
    Return a list of all implemented keyrings that can be constructed without
    parameters.
    """
    # ensure that all keyring backends are loaded
    for mod_name in ('file', 'Gnome', 'Google', 'keyczar', 'kwallet', 'multi',
            'OS_X', 'pyfs', 'SecretService', 'Windows'):
        # use fromlist to cause the module to resolve under Demand Import
        __import__('keyring.backends.'+mod_name, fromlist=('__name__',))

    def is_class_viable(keyring_cls):
        try:
            keyring_cls.priority
        except RuntimeError:
            return False
        return True

    all_classes = KeyringBackend._classes
    viable_classes = itertools.ifilter(is_class_viable, all_classes)
    return list(keyring.util.suppress_exceptions(viable_classes,
        exceptions=TypeError))
