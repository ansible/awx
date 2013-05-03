# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.


__version__ = '1.2-b1'

import os
import sys

__all__ = ['__version__']

def manage():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lib.settings')
    from django.core.management import execute_from_command_line
    if len(sys.argv) >= 2 and sys.argv[1] in ('version', '--version'):
        sys.stdout.write('acom-%s\n' % __version__)
    else:
        execute_from_command_line(sys.argv)
