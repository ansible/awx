# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved
import sys

from awx.main.utils.common import get_custom_venv_choices, get_custom_venv_pip_freeze
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """Returns either a list of custom venv paths or outputs the pip freeze from the path passed in the argument"""

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            nargs='?',
            default='',
            help='run without arguments to see a list of paths, run with one of those paths as an argument and see the pip freeze data',
        )

    def handle(self, *args, **options):
        super(Command, self).__init__()
        if options.get('path'):
            pip_data = get_custom_venv_pip_freeze(options.get('path'))
            if pip_data:
                print(pip_data)
        else:
            venvs = get_custom_venv_choices()
            if venvs:
                print('# {}'.format("Discovered virtual environments:"))
                for venv in venvs:
                    print(venv)

                msg = [
                    '',
                    'To export the contents of a virtual environment, ' 're-run while supplying the path as an argument:',
                    'awx-manage export_custom_venv /path/to/venv',
                ]
                print('\n'.join(msg))
            else:
                msg = ["No custom virtual environments detected in:", settings.BASE_VENV_PATH]

                for path in settings.CUSTOM_VENV_PATHS:
                    msg.append(path)

                print('\n'.join(msg), file=sys.stderr)
