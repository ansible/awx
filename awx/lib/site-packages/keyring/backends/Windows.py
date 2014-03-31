import sys
import base64
import platform
import functools

from ..py27compat import unicode_str
from ..util import escape, properties
from ..backend import KeyringBackend
from ..errors import PasswordDeleteError, ExceptionRaisedContext
from . import file

try:
    import pywintypes
    import win32cred
except ImportError:
    pass

try:
    import winreg
except ImportError:
    try:
        # Python 2 compatibility
        import _winreg as winreg
    except ImportError:
        pass

try:
    from . import _win_crypto
except ImportError:
    pass

def has_pywin32():
    """
    Does this environment have pywin32?
    Should return False even when Mercurial's Demand Import allowed import of
    win32cred.
    """
    with ExceptionRaisedContext() as exc:
        win32cred.__name__
    return not bool(exc)

def has_wincrypto():
    """
    Does this environment have wincrypto?
    Should return False even when Mercurial's Demand Import allowed import of
    _win_crypto, so accesses an attribute of the module.
    """
    with ExceptionRaisedContext() as exc:
        _win_crypto.__name__
    return not bool(exc)

class EncryptedKeyring(file.BaseKeyring):
    """
    A File-based keyring secured by Windows Crypto API.
    """

    @properties.ClassProperty
    @classmethod
    def priority(self):
        """
        Preferred over file.EncryptedKeyring but not other, more sophisticated
        Windows backends.
        """
        if not platform.system() == 'Windows':
            raise RuntimeError("Requires Windows")
        return .8

    filename = 'wincrypto_pass.cfg'

    def encrypt(self, password):
        """Encrypt the password using the CryptAPI.
        """
        return _win_crypto.encrypt(password)

    def decrypt(self, password_encrypted):
        """Decrypt the password using the CryptAPI.
        """
        return _win_crypto.decrypt(password_encrypted)


class WinVaultKeyring(KeyringBackend):
    """
    WinVaultKeyring stores encrypted passwords using the Windows Credential
    Manager.

    Requires pywin32

    This backend does some gymnastics to simulate multi-user support,
    which WinVault doesn't support natively. See
    https://bitbucket.org/kang/python-keyring-lib/issue/47/winvaultkeyring-only-ever-returns-last#comment-731977
    for details on the implementation, but here's the gist:

    Passwords are stored under the service name unless there is a collision
    (another password with the same service name but different user name),
    in which case the previous password is moved into a compound name:
    {username}@{service}
    """

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        """
        If available, the preferred backend on Windows.
        """
        if not has_pywin32():
            raise RuntimeError("Requires Windows and pywin32")
        return 5

    @staticmethod
    def _compound_name(username, service):
        return escape.u('%(username)s@%(service)s') % vars()

    def get_password(self, service, username):
        # first attempt to get the password under the service name
        res = self._get_password(service)
        if not res or res['UserName'] != username:
            # It wasn't found so attempt to get it with the compound name
            res = self._get_password(self._compound_name(username, service))
        if not res:
            return None
        blob = res['CredentialBlob']
        return blob.decode('utf-16')

    def _get_password(self, target):
        try:
            res = win32cred.CredRead(
                Type=win32cred.CRED_TYPE_GENERIC,
                TargetName=target,
            )
        except pywintypes.error as e:
            e = OldPywinError.wrap(e)
            if e.winerror == 1168 and e.funcname == 'CredRead': # not found
                return None
            raise
        return res

    def set_password(self, service, username, password):
        existing_pw = self._get_password(service)
        if existing_pw:
            # resave the existing password using a compound target
            existing_username = existing_pw['UserName']
            target = self._compound_name(existing_username, service)
            self._set_password(target, existing_username,
                existing_pw['CredentialBlob'].decode('utf-16'))
        self._set_password(service, username, unicode_str(password))

    def _set_password(self, target, username, password):
        credential = dict(Type=win32cred.CRED_TYPE_GENERIC,
                          TargetName=target,
                          UserName=username,
                          CredentialBlob=password,
                          Comment="Stored using python-keyring",
                          Persist=win32cred.CRED_PERSIST_ENTERPRISE)
        win32cred.CredWrite(credential, 0)

    def delete_password(self, service, username):
        compound = self._compound_name(username, service)
        deleted = False
        for target in service, compound:
            existing_pw = self._get_password(target)
            if existing_pw and existing_pw['UserName'] == username:
                deleted = True
                self._delete_password(target)
        if not deleted:
            raise PasswordDeleteError(service)

    def _delete_password(self, target):
        win32cred.CredDelete(
            Type=win32cred.CRED_TYPE_GENERIC,
            TargetName=target,
        )


class RegistryKeyring(KeyringBackend):
    """
    RegistryKeyring is a keyring which use Windows CryptAPI to encrypt
    the user's passwords and store them under registry keys
    """

    @properties.ClassProperty
    @classmethod
    def priority(self):
        """
        Preferred on Windows when pywin32 isn't installed
        """
        if platform.system() != 'Windows':
            raise RuntimeError("Requires Windows")
        if not has_wincrypto():
            raise RuntimeError("Requires ctypes")
        return 2

    def get_password(self, service, username):
        """Get password of the username for the service
        """
        try:
            # fetch the password
            key = r'Software\%s\Keyring' % service
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
            password_saved = winreg.QueryValueEx(hkey, username)[0]
            password_base64 = password_saved.encode('ascii')
            # decode with base64
            password_encrypted = base64.decodestring(password_base64)
            # decrypted the password
            password = _win_crypto.decrypt(password_encrypted).decode('utf-8')
        except EnvironmentError:
            password = None
        return password

    def set_password(self, service, username, password):
        """Write the password to the registry
        """
        # encrypt the password
        password_encrypted = _win_crypto.encrypt(password.encode('utf-8'))
        # encode with base64
        password_base64 = base64.encodestring(password_encrypted)
        # encode again to unicode
        password_saved = password_base64.decode('ascii')

        # store the password
        key_name = r'Software\%s\Keyring' % service
        hkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_name)
        winreg.SetValueEx(hkey, username, 0, winreg.REG_SZ, password_saved)

    def delete_password(self, service, username):
        """Delete the password for the username of the service.
        """
        try:
            key_name = r'Software\%s\Keyring' % service
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name, 0,
                winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(hkey, username)
        except WindowsError:
            e = sys.exc_info()[1]
            raise PasswordDeleteError(e)


class OldPywinError(object):
    """
    A compatibility wrapper for old PyWin32 errors, such as reported in
    https://bitbucket.org/kang/python-keyring-lib/issue/140/
    """
    def __init__(self, orig):
        self.orig = orig

    @property
    def funcname(self):
        return self.orig[1]

    @property
    def winerror(self):
        return self.orig[0]

    @classmethod
    def wrap(cls, orig_err):
        attr_check = functools.partial(hasattr, orig_err)
        is_old = not all(map(attr_check, ['funcname', 'winerror']))
        return cls(orig_err) if is_old else orig_err
