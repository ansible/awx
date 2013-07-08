# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

__version__ = '1.2.2-0'

import os
import sys

__all__ = ['__version__']

# Check for the presence/absence of "devonly" module to determine if running
# from a source code checkout or release packaage.
try:
    import awx.devonly
    MODE = 'development'
except ImportError:
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
            elif f.endswith('.pyc') and f[:-4] not in commands:
                commands.append(f[:-4])
    except OSError:
        pass
    return commands

def manage():
    # Update the default settings environment variable based on current mode.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings.%s' % MODE)
    # Add local site-packages directory to path.
    local_site_packages = os.path.join(os.path.dirname(__file__), 'lib',
                                       'site-packages')
    sys.path.insert(0, local_site_packages)
    # Monkeypatch Django find_commands to also work with .pyc files.
    import django.core.management
    django.core.management.find_commands = find_commands
    # Now run the command (or display the version).
    from django.core.management import execute_from_command_line
    if len(sys.argv) >= 2 and sys.argv[1] in ('version', '--version'):
        sys.stdout.write('awx-%s\n' % __version__)
    else:
        execute_from_command_line(sys.argv)
