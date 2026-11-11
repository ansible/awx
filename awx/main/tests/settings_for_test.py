# Python
import sys
import uuid
import os

try:
    import sqlean
except ImportError:
    pass
else:
    sys.modules['sqlite3'] = sqlean

# Set these before importing awx.settings: its package initializer loads Dynaconf
# before the development compatibility module gets a chance to set AWX_MODE.
# Tests should not need /var/log/tower or a production settings file. Preserve
# explicit overrides for tests that exercise other configurations.
os.environ.setdefault('AWX_MODE', 'development')
os.environ.setdefault('AWX_LOGGING_MODE', 'stdout')

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
