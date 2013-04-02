# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import sys

def run_command_as_script(command_name):
    '''
    Helper function to run the given management command directly as a script.

    Include something like the following in your management/commands/blah.py:

        if __name__ == '__main__':
            from __init__ import run_command_as_script
            command_name = os.path.splitext(os.path.basename(__file__))[0]
            run_command_as_script(command_name)

    '''
    # The DJANGO_SETTINGS_MODULE environment variable should already be set if
    # the script is called from a celery task.
    settings_module_name = os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                                                 'lib.settings')
    # This sys.path hack is needed when a celery task calls ansible-playbook
    # and needs to execute the script directly.  FIXME: Figure out if this will
    # work when installed in a production environment.
    try:
        settings_parent_module = __import__(settings_module_name)
    except ImportError:
        top_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        sys.path.insert(0, os.path.abspath(top_dir))
        settings_parent_module = __import__(settings_module_name)
    settings_module = getattr(settings_parent_module, settings_module_name.split('.')[-1])
    # Use the ACOM_TEST_DATABASE_NAME environment variable to specify the test
    # database name when called from unit tests.
    if os.environ.get('ACOM_TEST_DATABASE_NAME', None):
        settings_module.DATABASES['default']['NAME'] = os.environ['ACOM_TEST_DATABASE_NAME']
    from django.core.management import execute_from_command_line
    argv = [sys.argv[0], command_name] + sys.argv[1:]
    execute_from_command_line(argv)
