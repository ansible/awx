# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved
import sys

from awx.main.utils.common import get_custom_venv_choices
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """Returns either a list of custom venv paths from the path passed in the argument"""

    def handle(self, *args, **options):
        super(Command, self).__init__()
        venvs = get_custom_venv_choices()
        if venvs:
            print('# {}'.format("Discovered virtual environments:"))
            for venv in venvs:
                print(venv)

            msg = [
                '',
                'To export the contents of a virtual environment, ' 'run the following command while supplying the path as an argument:',
                'awx-manage export_custom_venv /path/to/venv',
            ]
            print('\n'.join(msg))
        else:
            msg = ["No custom virtual environments detected in:", settings.BASE_VENV_PATH]

            for path in settings.CUSTOM_VENV_PATHS:
                msg.append(path)

            print('\n'.join(msg), file=sys.stderr)
