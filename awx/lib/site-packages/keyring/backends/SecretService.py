import logging

from keyring.util import properties
from keyring.backend import KeyringBackend
from keyring.errors import (InitError, PasswordDeleteError,
    ExceptionRaisedContext)

try:
    import secretstorage.exceptions
except ImportError:
    pass

log = logging.getLogger(__name__)

class Keyring(KeyringBackend):
    """Secret Service Keyring"""

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        with ExceptionRaisedContext() as exc:
            secretstorage.__name__
        if exc:
            raise RuntimeError("SecretService required")
        try:
            bus = secretstorage.dbus_init()
            secretstorage.Collection(bus)
        except secretstorage.exceptions.SecretServiceNotAvailableException:
            raise RuntimeError("Unable to get initialize SecretService")
        return 5

    def get_default_collection(self):
        bus = secretstorage.dbus_init()
        if hasattr(secretstorage, 'get_default_collection'):
            collection = secretstorage.get_default_collection(bus)
        else:
            collection = secretstorage.Collection(bus)
        if collection.is_locked():
            if collection.unlock():
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
