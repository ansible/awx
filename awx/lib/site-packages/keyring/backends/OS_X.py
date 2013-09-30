import platform
import subprocess
import re
import binascii

from keyring.backend import KeyringBackend
from keyring.errors import PasswordSetError
from keyring.errors import PasswordDeleteError
from keyring.util import properties


class SecurityCommand(unicode):
    """
    A string suitable for passing as the 'command' parameter to the
    OS X 'security' command.
    """
    def __new__(cls, cmd, store='generic'):
        cmd = '%(cmd)s-%(store)s-password' % vars()
        return super(SecurityCommand, cls).__new__(cls, cmd)


class Keyring(KeyringBackend):
    """Mac OS X Keychain"""

    # regex for extracting password from security call
    password_regex = re.compile("""password:\s*(?:0x(?P<hex>[0-9A-F]+)\s*)?"""
                                """(?:"(?P<pw>.*)")?""")
    store = 'generic'

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        """
        Preferred for all OS X environments.
        """
        if platform.system() != 'Darwin':
            raise RuntimeError("OS X required")
        return 5

    def set_password(self, service, username, password):
        if username is None:
            username = ''
        set_error = PasswordSetError("Can't store password in keychain")
        try:
            # set up the call for security.
            cmd = [
                'security',
                SecurityCommand('add', self.store),
                '-a', username,
                '-s', service,
                '-w', password,
                '-U',
            ]
            call = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)
            stdoutdata, stderrdata = call.communicate()
            code = call.returncode
            # check return code.
            if code is not 0:
                raise set_error
        except:
            raise set_error

    def get_password(self, service, username):
        if username is None:
            username = ''
        try:
            # set up the call to security.
            cmd = [
                'security',
                SecurityCommand('find', self.store),
                '-g',
                '-a', username,
                '-s', service,
            ]
            call = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)
            stdoutdata, stderrdata = call.communicate()
            code = call.returncode
            if code is not 0:
                raise OSError("Can't fetch password from system")
            output = stderrdata.decode()
            # check for empty password.
            if output == 'password: \n':
                return ''
            # search for special password pattern.
            matches = Keyring.password_regex.search(output)
            if matches:
                group_dict = matches.groupdict()
                hex = group_dict.get('hex')
                pw = group_dict.get('pw')
                if hex:
                    # it's a weird hex password, decode it.
                    return unicode(binascii.unhexlify(hex), 'utf-8')
                else:
                    # it's a normal password, send it back.
                    return pw
            # nothing was found, it doesn't exist.
        except:
            pass

    def delete_password(self, service, username):
        del_error = PasswordDeleteError("Can't delete password in keychain")
        if username is None:
            username = ''
        try:
            cmd = [
                'security',
                SecurityCommand('delete', self.store),
                '-a', username,
                '-s', service,
            ]
            # set up the call for security.
            call = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)
            stdoutdata, stderrdata = call.communicate()
            code = call.returncode
            # check return code.
            if code is not 0:
                raise del_error
        except:
            raise del_error
