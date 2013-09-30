import itertools

from keyring.util import properties
from keyring.backend import KeyringBackend
from keyring import errors

class MultipartKeyringWrapper(KeyringBackend):

    """A wrapper around an existing keyring that breaks the password into
    smaller parts to handle implementations that have limits on the maximum
    length of passwords i.e. Windows Vault
    """

    def __init__(self, keyring, max_password_size=512):
        self._keyring = keyring
        self._max_password_size = max_password_size

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        return 0

    def get_password(self, service, username):
        """Get password of the username for the service
        """
        init_part = self._keyring.get_password(service, username)
        if init_part:
            parts = [init_part,]
            i = 1
            while True:
                next_part = self._keyring.get_password(
                    service,
                    '%s{{part_%d}}' %(username, i))
                if next_part:
                    parts.append(next_part)
                    i += 1
                else:
                    break
            return ''.join(parts)
        return None

    def set_password(self, service, username, password):
        """Set password for the username of the service
        """
        segments = range(0, len(password), self._max_password_size)
        password_parts = [
            password[i:i + self._max_password_size] for i in segments]
        for i, password_part in enumerate(password_parts):
            curr_username = username
            if i > 0:
                curr_username += '{{part_%d}}' %i
            self._keyring.set_password(service, curr_username, password_part)

    def delete_password(self, service, username):
        self._keyring.delete_password(service, username)
        count = itertools.count(1)
        while True:
            part_name = '%(username)s{{part_%(index)d}}' % dict(
                index = count.next(), **vars())
            try:
                self._keyring.delete_password(service, part_name)
            except errors.PasswordDeleteError:
                break
