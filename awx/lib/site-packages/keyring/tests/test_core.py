"""
test_core.py

Created by Kang Zhang on 2009-08-09
"""

from __future__ import with_statement

import os
import tempfile
import shutil

import mock
import pytest

import keyring.backend
import keyring.core
import keyring.util.platform_
from keyring import errors

PASSWORD_TEXT = "This is password"
PASSWORD_TEXT_2 = "This is password2"


@pytest.yield_fixture()
def config_filename(tmpdir):
    filename = tmpdir / 'keyringrc.cfg'
    with mock.patch('keyring.util.platform_.config_root', lambda: str(tmpdir)):
        yield str(filename)


class TestKeyring(keyring.backend.KeyringBackend):
    """A faked keyring for test.
    """
    def __init__(self):
        self.passwords = {}

    def supported(self):
        return 0

    def get_password(self, service, username):
        return PASSWORD_TEXT

    def set_password(self, service, username, password):
        self.passwords[(service, username)] = password
        return 0

    def delete_password(self, service, username):
        try:
            del self.passwords[(service, username)]
        except KeyError:
            raise errors.PasswordDeleteError("not set")


class TestKeyring2(TestKeyring):
    """Another faked keyring for test.
    """
    def get_password(self, service, username):
        return PASSWORD_TEXT_2


class TestCore:
    mock_global_backend = mock.patch('keyring.core._keyring_backend')

    @mock_global_backend
    def test_set_password(self, backend):
        """
        set_password on the default keyring is called.
        """
        keyring.core.set_password("test", "user", "passtest")
        backend.set_password.assert_called_once_with('test', 'user',
            'passtest')

    @mock_global_backend
    def test_get_password(self, backend):
        """
        set_password on the default keyring is called.
        """
        result = keyring.core.get_password("test", "user")
        backend.get_password.assert_called_once_with('test', 'user')
        assert result is not None

    @mock_global_backend
    def test_delete_password(self, backend):
        keyring.core.delete_password("test", "user")
        backend.delete_password.assert_called_once_with('test', 'user')

    def test_set_keyring_in_runtime(self):
        """Test the function of set keyring in runtime.
        """
        keyring.core.set_keyring(TestKeyring())

        keyring.core.set_password("test", "user", "password")
        assert keyring.core.get_password("test", "user") == PASSWORD_TEXT

    def test_set_keyring_in_config(self, config_filename):
        """Test setting the keyring by config file.
        """
        # create the config file
        with open(config_filename, 'w') as config_file:
            config_file.writelines([
                "[backend]\n",
                # the path for the user created keyring
                "keyring-path= %s\n" % os.path.dirname(os.path.abspath(__file__)),
                # the name of the keyring class
                "default-keyring=test_core.TestKeyring2\n",
                ])

        # init the keyring lib, the lib will automaticlly load the
        # config file and load the user defined module
        keyring.core.init_backend()

        keyring.core.set_password("test", "user", "password")
        assert keyring.core.get_password("test", "user") == PASSWORD_TEXT_2

    def test_load_config_empty(self, config_filename):
        "A non-existent or empty config should load"
        assert keyring.core.load_config() is None

    def test_load_config_degenerate(self, config_filename):
        "load_config should succeed in the absence of a backend section"
        with open(config_filename, 'w') as config_file:
            config_file.write('[keyring]')
        assert keyring.core.load_config() is None

    def test_load_config_blank_backend(self, config_filename):
        "load_config should succeed with an empty [backend] section"
        with open(config_filename, 'w') as config_file:
            config_file.write('[backend]')
        assert keyring.core.load_config() is None
