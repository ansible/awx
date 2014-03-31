"""
core.py

Created by Kang Zhang on 2009-07-09
"""
import os
import sys
import warnings
import logging

from .py27compat import configparser

from . import logger
from . import backend
from .util import platform_ as platform

log = logging.getLogger(__name__)

_keyring_backend = None

def set_keyring(keyring):
    """Set current keyring backend.
    """
    global _keyring_backend
    if not isinstance(keyring, backend.KeyringBackend):
        raise TypeError("The keyring must be a subclass of KeyringBackend")
    _keyring_backend = keyring


def get_keyring():
    """Get current keyring backend.
    """
    return _keyring_backend


def get_password(service_name, username):
    """Get password from the specified service.
    """
    return _keyring_backend.get_password(service_name, username)


def set_password(service_name, username, password):
    """Set password for the user in the specified service.
    """
    _keyring_backend.set_password(service_name, username, password)


def delete_password(service_name, username):
    """Delete the password for the user in the specified service.
    """
    _keyring_backend.delete_password(service_name, username)


def init_backend():
    """
    Load a keyring specified in the config file or infer the best available.
    """
    _load_library_extensions()
    set_keyring(load_config() or _get_best_keyring())


def _get_best_keyring():
    """
    Return the best keyring backend for the given environment based on
    priority.
    """
    keyrings = backend.get_all_keyring()
    # rank by priority
    keyrings.sort(key = lambda x: -x.priority)
    # get the most recommended one
    return keyrings[0]


def load_keyring(keyring_path, keyring_name):
    """
    Load the specified keyring by name (a fully-qualified name to the
    keyring, such as 'keyring.backends.file.PlaintextKeyring')

    `keyring_path` is an additional, optional search path and may be None.
    **deprecated** In the future, keyring_path must be None.
    """
    module_name, sep, class_name = keyring_name.rpartition('.')
    if keyring_path is not None and keyring_path not in sys.path:
        warnings.warn("keyring_path is deprecated and should always be None",
            DeprecationWarning)
        sys.path.insert(0, keyring_path)
    __import__(module_name)
    module = sys.modules[module_name]
    class_ = getattr(module, class_name)
    # invoke the priority to ensure it is viable, or raise a RuntimeError
    class_.priority
    return class_()


def load_config():
    """Load a keyring using the config file.

    The config file can be in the current working directory, or in the user's
    home directory.
    """
    keyring = None

    filename = 'keyringrc.cfg'

    local_path = os.path.join(os.getcwd(), filename)
    config_path = os.path.join(platform.config_root(), filename)

    # search from current working directory and the data root
    keyring_cfg_candidates = [local_path, config_path]

    # initialize the keyring_config with the first detected config file
    keyring_cfg = None
    for path in keyring_cfg_candidates:
        keyring_cfg = path
        if os.path.exists(path):
            break

    if os.path.exists(keyring_cfg):
        config = configparser.RawConfigParser()
        config.read(keyring_cfg)
        _load_keyring_path(config)

        # load the keyring class name, and then load this keyring
        try:
            if config.has_section("backend"):
                keyring_name = config.get("backend", "default-keyring").strip()
            else:
                raise configparser.NoOptionError('backend', 'default-keyring')

            keyring = load_keyring(None, keyring_name)
        except (configparser.NoOptionError, ImportError):
            logger.warning("Keyring config file contains incorrect values.\n" +
                           "Config file: %s" % keyring_cfg)

    return keyring

def _load_keyring_path(config):
    "load the keyring-path option (if present)"
    try:
        path = config.get("backend", "keyring-path").strip()
        sys.path.insert(0, path)
    except (configparser.NoOptionError, configparser.NoSectionError):
        pass

def _load_library_extensions():
    """
    Locate all setuptools entry points by the name 'keyring backends'
    and initialize them.

    Any third-party library may register an entry point by adding the
    following to their setup.py::

        entry_points = {
            'keyring backends': [
                'plugin name = mylib.mymodule:initialize_func',
            ],
        },

    `plugin name` can be anything.
    `initialize_func` is optional and will be invoked by keyring on startup.

    Most plugins will simply provide or import a KeyringBackend in `mymodule`.
    """
    group = 'keyring backends'
    try:
        pkg_resources = __import__('pkg_resources')
    except ImportError:
        return
    entry_points = pkg_resources.iter_entry_points(group=group)
    for ep in entry_points:
        try:
            log.info('Loading keyring backends from %s', ep.name)
            init_func = ep.load()
            if callable(init_func):
                init_func()
        except Exception as exc:
            log.exception("Error initializing plugin %s (%s).", ep, exc)

# init the _keyring_backend
init_backend()
