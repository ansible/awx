# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
from __future__ import absolute_import, unicode_literals

import os
import sys
import warnings
from importlib.metadata import PackageNotFoundError, version as _get_version


def get_version():
    version_from_file = get_version_from_file()
    if version_from_file:
        return version_from_file
    else:
        from setuptools_scm import get_version

        version = get_version(root='..', relative_to=__file__)
        return version


def get_version_from_file():
    vf = version_file()
    if vf:
        with open(vf, 'r') as file:
            return file.read().strip()


def version_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    version_file = os.path.join(current_dir, '..', 'VERSION')

    if os.path.exists(version_file):
        return version_file


try:
    __version__ = _get_version('awx')
except PackageNotFoundError:
    __version__ = get_version()

__all__ = ['__version__']


# Check for the presence/absence of "devonly" module to determine if running
# from a source code checkout or release packaage.
try:
    import awx.devonly  # noqa

    MODE = 'development'
except ImportError:  # pragma: no cover
    MODE = 'production'


try:
    import django  # noqa: F401
except ImportError:
    pass
else:
    from django.db import connection


def prepare_env():
    # Update the default settings environment variable based on current mode.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings')
    os.environ.setdefault('AWX_MODE', MODE)
    # Hide DeprecationWarnings when running in production.  Need to first load
    # settings to apply our filter after Django's own warnings filter.
    from django.conf import settings

    if not settings.DEBUG:  # pragma: no cover
        warnings.simplefilter('ignore', DeprecationWarning)


def manage():
    # Prepare the AWX environment.
    prepare_env()
    # Now run the command (or display the version).
    from django.conf import settings
    from django.core.management import execute_from_command_line

    # enforce the postgres version is a minimum of 12 (we need this for partitioning); if not, then terminate program with exit code of 1
    # In the future if we require a feature of a version of postgres > 12 this should be updated to reflect that.
    # The return of connection.pg_version is something like 12013
    if not os.getenv('SKIP_PG_VERSION_CHECK', False) and not MODE == 'development':
        if (connection.pg_version // 10000) < 12:
            sys.stderr.write("At a minimum, postgres version 12 is required\n")
            sys.exit(1)

    if len(sys.argv) >= 2 and sys.argv[1] in ('version', '--version'):  # pragma: no cover
        sys.stdout.write('%s\n' % __version__)
    # If running as a user without permission to read settings, display an
    # error message.  Allow --help to still work.
    elif not os.getenv('SKIP_SECRET_KEY_CHECK', False) and settings.SECRET_KEY == 'permission-denied':
        if len(sys.argv) == 1 or len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help', 'help'):
            execute_from_command_line(sys.argv)
            sys.stdout.write('\n')
        prog = os.path.basename(sys.argv[0])
        sys.stdout.write('Permission denied: %s must be run as root or awx.\n' % prog)
        sys.exit(1)
    else:
        execute_from_command_line(sys.argv)
