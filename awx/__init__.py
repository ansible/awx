# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
from __future__ import absolute_import, unicode_literals

import os
import sys
import warnings

from pkg_resources import get_distribution

__version__ = get_distribution('awx').version
__all__ = ['__version__']


# Check for the presence/absence of "devonly" module to determine if running
# from a source code checkout or release packaage.
try:
    import awx.devonly # noqa
    MODE = 'development'
except ImportError: # pragma: no cover
    MODE = 'production'


import hashlib

try:
    import django  # noqa: F401
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False
else:
    from django.db.backends.base import schema
    from django.db.models import indexes
    from django.db.backends.utils import names_digest


if HAS_DJANGO is True:

    # See upgrade blocker note in requirements/README.md
    try:
        names_digest('foo', 'bar', 'baz', length=8)
    except ValueError:
        def names_digest(*args, length):
            """
            Generate a 32-bit digest of a set of arguments that can be used to shorten
            identifying names.  Support for use in FIPS environments.
            """
            h = hashlib.md5(usedforsecurity=False)
            for arg in args:
                h.update(arg.encode())
            return h.hexdigest()[:length]

        schema.names_digest = names_digest
        indexes.names_digest = names_digest


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


def oauth2_getattribute(self, attr):
    # Custom method to override
    # oauth2_provider.settings.OAuth2ProviderSettings.__getattribute__
    from django.conf import settings
    val = None
    if 'migrate' not in sys.argv:
        # certain Django OAuth Toolkit migrations actually reference
        # setting lookups for references to model classes (e.g.,
        # oauth2_settings.REFRESH_TOKEN_MODEL)
        # If we're doing an OAuth2 setting lookup *while running* a migration,
        # don't do our usual "Configure Tower in Tower" database setting lookup
        val = settings.OAUTH2_PROVIDER.get(attr)
    if val is None:
        val = object.__getattribute__(self, attr)
    return val


def prepare_env():
    # Update the default settings environment variable based on current mode.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings.%s' % MODE)
    # Hide DeprecationWarnings when running in production.  Need to first load
    # settings to apply our filter after Django's own warnings filter.
    from django.conf import settings
    if not settings.DEBUG: # pragma: no cover
        warnings.simplefilter('ignore', DeprecationWarning)
    # Monkeypatch Django find_commands to also work with .pyc files.
    import django.core.management
    django.core.management.find_commands = find_commands

    # Monkeypatch Oauth2 toolkit settings class to check for settings
    # in django.conf settings each time, not just once during import
    import oauth2_provider.settings
    oauth2_provider.settings.OAuth2ProviderSettings.__getattribute__ = oauth2_getattribute

    # Use the AWX_TEST_DATABASE_* environment variables to specify the test
    # database settings to use when management command is run as an external
    # program via unit tests.
    for opt in ('ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST', 'PORT'): # pragma: no cover
        if os.environ.get('AWX_TEST_DATABASE_%s' % opt, None):
            settings.DATABASES['default'][opt] = os.environ['AWX_TEST_DATABASE_%s' % opt]
    # Disable capturing all SQL queries in memory when in DEBUG mode.
    if settings.DEBUG and not getattr(settings, 'SQL_DEBUG', True):
        from django.db.backends.base.base import BaseDatabaseWrapper
        from django.db.backends.utils import CursorWrapper
        BaseDatabaseWrapper.make_debug_cursor = lambda self, cursor: CursorWrapper(cursor, self)

    # Use the default devserver addr/port defined in settings for runserver.
    default_addr = getattr(settings, 'DEVSERVER_DEFAULT_ADDR', '127.0.0.1')
    default_port = getattr(settings, 'DEVSERVER_DEFAULT_PORT', 8000)
    from django.core.management.commands import runserver as core_runserver
    original_handle = core_runserver.Command.handle

    def handle(self, *args, **options):
        if not options.get('addrport'):
            options['addrport'] = '%s:%d' % (default_addr, int(default_port))
        elif options.get('addrport').isdigit():
            options['addrport'] = '%s:%d' % (default_addr, int(options['addrport']))
        return original_handle(self, *args, **options)

    core_runserver.Command.handle = handle


def manage():
    # Prepare the AWX environment.
    prepare_env()
    # Now run the command (or display the version).
    from django.conf import settings
    from django.core.management import execute_from_command_line
    if len(sys.argv) >= 2 and sys.argv[1] in ('version', '--version'): # pragma: no cover
        sys.stdout.write('%s\n' % __version__)
    # If running as a user without permission to read settings, display an
    # error message.  Allow --help to still work.
    elif settings.SECRET_KEY == 'permission-denied':
        if len(sys.argv) == 1 or len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help', 'help'):
            execute_from_command_line(sys.argv)
            sys.stdout.write('\n')
        prog = os.path.basename(sys.argv[0])
        sys.stdout.write('Permission denied: %s must be run as root or awx.\n' % prog)
        sys.exit(1)
    else:
        execute_from_command_line(sys.argv)
