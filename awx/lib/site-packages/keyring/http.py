"""
urllib2.HTTPPasswordMgr object using the keyring, for use with the
urllib2.HTTPBasicAuthHandler.

usage:
    import urllib2
    handlers = [urllib2.HTTPBasicAuthHandler(PasswordMgr())]
    urllib2.install_opener(handlers)
    urllib2.urlopen(...)

This will prompt for a password if one is required and isn't already
in the keyring. Then, it adds it to the keyring for subsequent use.
"""

import keyring
import getpass


class PasswordMgr(object):
    def get_username(self, realm, authuri):
        return getpass.getuser()

    def add_password(self, realm, authuri, password):
        user = self.get_username(realm, authuri)
        keyring.set_password(realm, user, password)

    def find_user_password(self, realm, authuri):
        user = self.get_username(realm, authuri)
        password = keyring.get_password(realm, user)
        if password is None:
            prompt = 'password for %(user)s@%(realm)s for '\
                '%(authuri)s: ' % vars()
            password = getpass.getpass(prompt)
            keyring.set_password(realm, user, password)
        return user, password

    def clear_password(self, realm, authuri):
        user = self.get_username(realm, authuri)
        keyring.delete_password(realm, user)
