import logging

from ..util import properties
from ..util import XDG
from ..backend import KeyringBackend
from ..errors import (InitError, PasswordDeleteError,
    ExceptionRaisedContext)

try:
    import secretstorage
    import secretstorage.exceptions as exceptions
except ImportError:
    pass

log = logging.getLogger(__name__)

class Keyring(KeyringBackend):
    """Secret Service Keyring"""

    @properties.ClassProperty
    @classmethod
    @XDG.Preference('Gnome')
    def priority(cls):
        with ExceptionRaisedContext() as exc:
            secretstorage.__name__
        if exc:
            raise RuntimeError("SecretStorage required")
        if not hasattr(secretstorage, 'get_default_collection'):
            raise RuntimeError("SecretStorage 1.0 or newer required")
        try:
            bus = secretstorage.dbus_init()
            list(secretstorage.get_all_collections(bus))
        except exceptions.SecretServiceNotAvailableException as e:
            raise RuntimeError(
                "Unable to initialize SecretService: %s" % e)
        return 5

    def get_default_collection(self):
        bus = secretstorage.dbus_init()
        try:
            collection = secretstorage.get_default_collection(bus)
        except exceptions.SecretStorageException as e:
            raise InitError("Failed to create the collection: %s." % e)
        if collection.is_locked():
            collection.unlock()
            if collection.is_locked(): # User dismissed the prompt
                raise InitError("Failed to unlock the collection!")
        return collection

    def get_password(self, service, username):
        """Get password of the username for the service
        """
        collection = self.get_default_collection()
        items = collection.search_items(
            {"username": username, "service": service})
        for item in items:
            return item.get_secret().decode('utf-8')

    def set_password(self, service, username, password):
        """Set password for the username of the service
        """
        collection = self.get_default_collection()
        attributes = {
            "application": "python-keyring",
            "service": service,
            "username": username
            }
        label = "Password for '%s' on '%s'" % (username, service)
        collection.create_item(label, attributes, password, replace=True)

    def delete_password(self, service, username):
        """Delete the stored password (only the first one)
        """
        collection = self.get_default_collection()
        items = collection.search_items(
            {"username": username, "service": service})
        for item in items:
            return item.delete()
        raise PasswordDeleteError("No such password!")
