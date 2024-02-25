# Python
from unittest import mock
import uuid

# patch python-ldap
with mock.patch('__main__.__builtins__.dir', return_value=[]):
    import ldap  # NOQA

# Load development settings for base variables.
from awx.settings.development import *  # NOQA

# Some things make decisions based on settings.SETTINGS_MODULE, so this is done for that
SETTINGS_MODULE = 'awx.settings.development'

# Use SQLite for unit tests instead of PostgreSQL.  If the lines below are
# commented out, Django will create the test_awx-dev database in PostgreSQL to
# run unit tests.
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-{}'.format(str(uuid.uuid4()))}}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'awx.sqlite3'),  # noqa
        'TEST': {
            # Test database cannot be :memory: for inventory tests.
            'NAME': os.path.join(BASE_DIR, 'awx_test.sqlite3')  # noqa
        },
    }
}
