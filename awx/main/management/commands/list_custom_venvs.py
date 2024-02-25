# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved
import sys

from awx.main.utils.common import get_custom_venv_choices
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """Returns a list of custom venv paths from the path passed in the argument"""

    def add_arguments(self, parser):
        parser.add_argument('-q', action='store_true', help='run with -q to output only the results of the query.')

    def handle(self, *args, **options):
        super(Command, self).__init__()
        venvs = get_custom_venv_choices()
        if venvs:
            if not options.get('q'):
                msg = [
                    '# Discovered Virtual Environments:',
                    '\n'.join(venvs),
                    '',
                    '- To export the contents of a (deprecated) virtual environment, run the following command while supplying the path as an argument:',
                    'awx-manage export_custom_venv /path/to/venv',
                    '',
                    '- To view the connections a (deprecated) virtual environment had in the database, run the following command while supplying the path as an argument:',
                    'awx-manage custom_venv_associations /path/to/venv',
                    '',
                    '- Run these commands with `-q` to remove tool tips.',
                    '',
                ]
                print('\n'.join(msg))
            else:
                print('\n'.join(venvs), '\n')
        else:
            msg = ["No custom virtual environments detected in:", settings.BASE_VENV_PATH]

            for path in settings.CUSTOM_VENV_PATHS:
                msg.append(path)

            print('\n'.join(msg), file=sys.stderr)
