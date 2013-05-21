# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

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
    # the script is called from a celery task.  Don't attemtp to set a default.
    settings_module_name = os.environ['DJANGO_SETTINGS_MODULE']
    # This sys.path hack is needed when a celery task calls ansible-playbook
    # and needs to execute the script directly.  FIXME: Figure out if this will
    # work when installed in a production environment.
    try:
        settings_module = __import__(settings_module_name, globals(), locals(),
                                     [settings_module_name.split('.')[-1]])
    except ImportError:
        top_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        sys.path.insert(0, os.path.abspath(top_dir))
        settings_module = __import__(settings_module_name, globals(), locals(),
                                     [settings_module_name.split('.')[-1]])
    # Use the ACOM_TEST_DATABASE_NAME environment variable to specify the test
    # database name when called from unit tests.
    if os.environ.get('ACOM_TEST_DATABASE_NAME', None):
        settings_module.DATABASES['default']['NAME'] = os.environ['ACOM_TEST_DATABASE_NAME']
    from django.core.management import execute_from_command_line
    argv = [sys.argv[0], command_name] + sys.argv[1:]
    execute_from_command_line(argv)
