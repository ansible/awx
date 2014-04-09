# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

__version__ = '2.0.0-0'

import os
import sys
import warnings

__all__ = ['__version__']

# Check for the presence/absence of "devonly" module to determine if running
# from a source code checkout or release packaage.
try:
    import awx.devonly
    MODE = 'development'
except ImportError: # pragma: no cover
    MODE = 'production'

def find_commands(management_dir):
    # Modified version of function from django/core/management/__init__.py.
    command_dir = os.path.join(management_dir, 'commands')
    commands = []
    try:
        for f in os.listdir(command_dir):
            if f.startswith('_'):
                continue
            elif f.endswith('.py') and f[:-3] not in commands:
                commands.append(f[:-3])
            elif f.endswith('.pyc') and f[:-4] not in commands: # pragma: no cover
                commands.append(f[:-4])
    except OSError:
        pass
    return commands

def prepare_env():
    # Update the default settings environment variable based on current mode.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings.%s' % MODE)
    # Add local site-packages directory to path.
    local_site_packages = os.path.join(os.path.dirname(__file__), 'lib',
                                       'site-packages')
    sys.path.insert(0, local_site_packages)
    # Hide DeprecationWarnings when running in production.  Need to first load
    # settings to apply our filter after Django's own warnings filter.
    from django.conf import settings
    if not settings.DEBUG: # pragma: no cover
        warnings.simplefilter('ignore', DeprecationWarning)
    # Monkeypatch Django find_commands to also work with .pyc files.
    import django.core.management
    django.core.management.find_commands = find_commands
    # Fixup sys.modules reference to django.utils.six to allow jsonfield to
    # work when using Django 1.4.
    import django.utils
    try:
        import django.utils.six
    except ImportError: # pragma: no cover
        import six
        sys.modules['django.utils.six'] = sys.modules['six']
        django.utils.six = sys.modules['django.utils.six']
        from django.utils import six
    # Use the AWX_TEST_DATABASE_* environment variables to specify the test
    # database settings to use when management command is run as an external
    # program via unit tests.
    for opt in ('ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST', 'PORT'): # pragma: no cover
        if os.environ.get('AWX_TEST_DATABASE_%s' % opt, None):
            settings.DATABASES['default'][opt] = os.environ['AWX_TEST_DATABASE_%s' % opt]
    # Disable capturing all SQL queries in memory when in DEBUG mode.
    if settings.DEBUG and not getattr(settings, 'SQL_DEBUG', True):
        from django.db.backends import BaseDatabaseWrapper
        from django.db.backends.util import CursorWrapper
        BaseDatabaseWrapper.make_debug_cursor = lambda self, cursor: CursorWrapper(cursor, self)

def manage():
    # Prepare the AWX environment.
    prepare_env()
    # Now run the command (or display the version).
    from django.core.management import execute_from_command_line
    if len(sys.argv) >= 2 and sys.argv[1] in ('version', '--version'): # pragma: no cover
        sys.stdout.write('%s\n' % __version__)
    else:
        execute_from_command_line(sys.argv)
