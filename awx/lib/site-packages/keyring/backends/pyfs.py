import os
import base64

from ..py27compat import configparser

from .. import errors
from ..util.escape import escape as escape_for_ini
from ..util import platform_, properties
from ..backend import KeyringBackend, NullCrypter
from . import keyczar

try:
    import fs.opener
    import fs.osfs
    import fs.errors
    import fs.path
    import fs.remote
except ImportError:
    pass

def has_pyfs():
    """
    Does this environment have pyfs installed?
    Should return False even when Mercurial's Demand Import allowed import of
    fs.*.
    """
    with errors.ExceptionRaisedContext() as exc:
        fs.__name__
    return not bool(exc)

class BasicKeyring(KeyringBackend):
    """BasicKeyring is a Pyfilesystem-based implementation of
    keyring.

    It stores the password directly in the file, and supports
    encryption and decryption. The encrypted password is stored in base64
    format.
    Being based on Pyfilesystem the file can be local or network-based and
    served by any of the filesystems supported by Pyfilesystem including Amazon
    S3, FTP, WebDAV, memory and more.
    """

    _filename = 'keyring_pyf_pass.cfg'

    def __init__(self, crypter, filename=None, can_create=True,
                 cache_timeout=None):
        super(BasicKeyring, self).__init__()
        self._crypter = crypter
        self._filename = (filename or
                          os.path.join(platform_.data_root(),
                                       self.__class__._filename))
        self._can_create = can_create
        self._cache_timeout = cache_timeout

    @properties.NonDataProperty
    def file_path(self):
        """
        The path to the file where passwords are stored. This property
        may be overridden by the subclass or at the instance level.
        """
        return os.path.join(platform_.data_root(), self.filename)

    @property
    def filename(self):
        """The filename used to store the passwords.
        """
        return self._filename

    def encrypt(self, password):
        """Encrypt the password.
        """
        if not password or not self._crypter:
            return password or ''
        return self._crypter.encrypt(password)

    def decrypt(self, password_encrypted):
        """Decrypt the password.
        """
        if not password_encrypted or not self._crypter:
            return password_encrypted or ''
        return self._crypter.decrypt(password_encrypted)

    def _open(self, mode='rb'):
        """Open the password file in the specified mode
        """
        open_file = None
        writeable = 'w' in mode or 'a' in mode or '+' in mode
        try:
            # NOTE: currently the MemOpener does not split off any filename
            #       which causes errors on close()
            #       so we add a dummy name and open it separately
            if (self.filename.startswith('mem://') or
                    self.filename.startswith('ram://')):
                open_file = fs.opener.fsopendir(self.filename).open('kr.cfg',
                                                                    mode)
            else:
                if not hasattr(self, '_pyfs'):
                    # reuse the pyfilesystem and path
                    self._pyfs, self._path = fs.opener.opener.parse(self.filename,
                                               writeable=writeable)
                    # cache if permitted
                    if self._cache_timeout is not None:
                        self._pyfs = fs.remote.CacheFS(
                            self._pyfs, cache_timeout=self._cache_timeout)
                open_file = self._pyfs.open(self._path, mode)
        except fs.errors.ResourceNotFoundError:
            if self._can_create:
                segments = fs.opener.opener.split_segments(self.filename)
                if segments:
                    # this seems broken, but pyfilesystem uses it, so we must
                    fs_name, credentials, url1, url2, path = segments.groups()
                    assert fs_name, 'Should be a remote filesystem'
                    host = ''
                    # allow for domain:port
                    if ':' in url2:
                        split_url2 = url2.split('/', 1)
                        if len(split_url2) > 1:
                            url2 = split_url2[1]
                        else:
                            url2 = ''
                        host = split_url2[0]
                    pyfs = fs.opener.opener.opendir('%s://%s' %(fs_name, host))
                    # cache if permitted
                    if self._cache_timeout is not None:
                        pyfs = fs.remote.CacheFS(
                            pyfs, cache_timeout=self._cache_timeout)
                    # NOTE: fs.path.split does not function in the same way os os.path.split... at least under windows
                    url2_path, url2_filename = os.path.split(url2)
                    if url2_path and not pyfs.exists(url2_path):
                        pyfs.makedir(url2_path, recursive=True)
                else:
                    # assume local filesystem
                    full_url = fs.opener._expand_syspath(self.filename)
                    # NOTE: fs.path.split does not function in the same way os os.path.split... at least under windows
                    url2_path, url2 = os.path.split(full_url)
                    pyfs = fs.osfs.OSFS(url2_path)

                try:
                    # reuse the pyfilesystem and path
                    self._pyfs = pyfs
                    self._path = url2
                    return pyfs.open(url2, mode)
                except fs.errors.ResourceNotFoundError:
                    if writeable:
                        raise
                    else:
                        pass
            # NOTE: ignore read errors as the underlying caller can fail safely
            if writeable:
                raise
            else:
                pass
        return open_file

    @property
    def config(self):
        """load the passwords from the config file
        """
        if not hasattr(self, '_config'):
            raw_config = configparser.RawConfigParser()
            f = self._open()
            if f:
                raw_config.readfp(f)
                f.close()
            self._config = raw_config
        return self._config

    def get_password(self, service, username):
        """Read the password from the file.
        """
        service = escape_for_ini(service)
        username = escape_for_ini(username)

        # fetch the password
        try:
            password_base64 = self.config.get(service, username).encode()
            # decode with base64
            password_encrypted = base64.decodestring(password_base64)
            # decrypted the password
            password = self.decrypt(password_encrypted).decode('utf-8')
        except (configparser.NoOptionError, configparser.NoSectionError):
            password = None
        return password

    def set_password(self, service, username, password):
        """Write the password in the file.
        """
        service = escape_for_ini(service)
        username = escape_for_ini(username)

        # encrypt the password
        password = password or ''
        password_encrypted = self.encrypt(password.encode('utf-8'))

        # encode with base64
        password_base64 = base64.encodestring(password_encrypted).decode()
        # write the modification
        if not self.config.has_section(service):
            self.config.add_section(service)
        self.config.set(service, username, password_base64)
        config_file = self._open('w')
        self.config.write(config_file)
        config_file.close()

    def delete_password(self, service, username):
        service = escape_for_ini(service)
        username = escape_for_ini(username)

        try:
            self.config.remove_option(service, username)
        except configparser.NoSectionError:
            raise errors.PasswordDeleteError('Password not found')
        config_file = self._open('w')
        self.config.write(config_file)
        config_file.close()

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        if not has_pyfs():
            raise RuntimeError("pyfs required")
        return 2

class PlaintextKeyring(BasicKeyring):
    """Unencrypted Pyfilesystem Keyring
    """

    def __init__(self, filename=None, can_create=True, cache_timeout=None):
        super(PlaintextKeyring, self).__init__(
            NullCrypter(), filename=filename, can_create=can_create,
            cache_timeout=cache_timeout)

class EncryptedKeyring(BasicKeyring):
    """Encrypted Pyfilesystem Keyring
    """

    _filename = 'crypted_pyf_pass.cfg'

    def __init__(self, crypter, filename=None, can_create=True,
                 cache_timeout=None):
        super(EncryptedKeyring, self).__init__(
            crypter, filename=filename, can_create=can_create,
            cache_timeout=cache_timeout)

class KeyczarKeyring(EncryptedKeyring):
    """Encrypted Pyfilesystem Keyring using Keyczar keysets specified in
    environment vars
    """

    def __init__(self):
        super(KeyczarKeyring, self).__init__(
            keyczar.EnvironCrypter())
