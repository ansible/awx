from unittest import mock

with mock.patch('__main__.__builtins__.dir', return_value=[]):
    import ldap  # NOQA

from awx.settings.development import *  # NOQA

IS_TESTING_MODE = True
