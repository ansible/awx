# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

__version__ = '1.2-b1'

import os
import sys

__all__ = ['__version__']

def manage():
    # Default to production mode unless being called from manage.py, which sets
    # the environment variable for development mode instead.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lib.settings.production')
    from django.core.management import execute_from_command_line
    if len(sys.argv) >= 2 and sys.argv[1] in ('version', '--version'):
        sys.stdout.write('ansibleworks-%s\n' % __version__)
    else:
        execute_from_command_line(sys.argv)
