import os

try:
    from gi import Repository
    if Repository.get_default().enumerate_versions('GnomeKeyring'):
        from gi.repository import GnomeKeyring
except ImportError:
    pass

from keyring.backend import KeyringBackend
from keyring.errors import PasswordSetError, PasswordDeleteError
from keyring.util import properties
from keyring.py27compat import unicode_str

class Keyring(KeyringBackend):
    """Gnome Keyring"""

    # Name of the keyring to store the passwords in.
    # Use None for the default keyring.
    KEYRING_NAME = None

    requisite_vars = [
        'GNOME_KEYRING_CONTROL',
        'DISPLAY',
        'DBUS_SESSION_BUS_ADDRESS',
    ]

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        if 'GnomeKeyring' not in globals():
            raise RuntimeError("GnomeKeyring module required")
        if not cls.has_requisite_vars():
            raise RuntimeError("Requisite environment vars are not present")
        return int(cls.has_requisite_vars())

    @classmethod
    def has_requisite_vars(cls):
        """
        Return True if the requisite environment vars are present in the
        environment.
        """
        return set(cls.requisite_vars).issubset(os.environ)

    def _find_passwords(self, service, username, deleting=False):
        """Get password of the username for the service
        """
        passwords = []

        service = self._safe_string(service)
        username = self._safe_string(username)
        for attrs_tuple in (('username', 'service'), ('user', 'domain')):
            attrs = GnomeKeyring.Attribute.list_new()
            GnomeKeyring.Attribute.list_append_string(attrs, attrs_tuple[0], username)
            GnomeKeyring.Attribute.list_append_string(attrs, attrs_tuple[1], service)
            result, items = GnomeKeyring.find_items_sync(
                GnomeKeyring.ItemType.NETWORK_PASSWORD, attrs)
            if result == GnomeKeyring.Result.OK:
                passwords += items
            elif deleting:
                if result == GnomeKeyring.Result.CANCELLED:
                    raise PasswordDeleteError("Cancelled by user")
                elif result != GnomeKeyring.Result.NO_MATCH:
                    raise PasswordDeleteError(result.value_name)
        return passwords

    def get_password(self, service, username):
        """Get password of the username for the service
        """
        items = self._find_passwords(service, username)
        if not items:
            return None

        secret = items[0].secret
        return secret if isinstance(secret, unicode_str) else secret.decode('utf-8')

    def set_password(self, service, username, password):
        """Set password for the username of the service
        """
        service = self._safe_string(service)
        username = self._safe_string(username)
        password = self._safe_string(password)
        attrs = GnomeKeyring.Attribute.list_new()
        GnomeKeyring.Attribute.list_append_string(attrs, 'username', username)
        GnomeKeyring.Attribute.list_append_string(attrs, 'service', service)
        GnomeKeyring.Attribute.list_append_string(attrs, 'application', 'python-keyring')
        result = GnomeKeyring.item_create_sync(
            self.KEYRING_NAME, GnomeKeyring.ItemType.NETWORK_PASSWORD,
            "Password for '%s' on '%s'" % (username, service),
            attrs, password, True)[0]
        if result == GnomeKeyring.Result.CANCELLED:
            # The user pressed "Cancel" when prompted to unlock their keyring.
            raise PasswordSetError("Cancelled by user")
        elif result != GnomeKeyring.Result.OK:
            raise PasswordSetError(result.value_name)

    def delete_password(self, service, username):
        """Delete the password for the username of the service.
        """
        items = self._find_passwords(service, username, deleting=True)
        if not items:
            raise PasswordDeleteError("Password not found")
        for current in items:
            result = GnomeKeyring.item_delete_sync(current.keyring,
                                                   current.item_id)
            if result == GnomeKeyring.Result.CANCELLED:
                raise PasswordDeleteError("Cancelled by user")
            elif result != GnomeKeyring.Result.OK:
                raise PasswordDeleteError(result.value_name)

    def _safe_string(self, source, encoding='utf-8'):
        """Convert unicode to string as gnomekeyring barfs on unicode"""
        if not isinstance(source, str):
            return source.encode(encoding)
        return str(source)
